"""Shared source-adapter vocabulary."""
from __future__ import annotations

import dataclasses
import enum
import json
import os


class Availability(str, enum.Enum):
    OK = "ok"                 # source configured and returned data
    EMPTY = "empty"           # source configured, but had nothing this month
    UNCONFIGURED = "unconfigured"   # no adapter pointed at it
    ERROR = "error"           # configured but failed to read


@dataclasses.dataclass(frozen=True)
class SourceStatus:
    name: str
    availability: Availability
    detail: str = ""

    @property
    def usable(self) -> bool:
        return self.availability is Availability.OK

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "availability": self.availability.value,
            "detail": self.detail,
        }


def load_json_file(name: str, path: str) -> tuple[list | dict, SourceStatus]:
    """
    Reads an optional JSON feed from disk. Missing path -> UNCONFIGURED, which
    is a normal state, not an error: most repos have no incident feed.
    """
    if not path:
        return [], SourceStatus(name, Availability.UNCONFIGURED,
                                "no path configured")
    if not os.path.exists(path):
        return [], SourceStatus(name, Availability.ERROR,
                                f"configured path does not exist: {path}")
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return [], SourceStatus(name, Availability.ERROR, f"{type(exc).__name__}: {exc}")

    if not payload:
        return payload, SourceStatus(name, Availability.EMPTY, f"read {path}, no records")
    return payload, SourceStatus(name, Availability.OK,
                                 f"read {len(payload)} records from {path}")
