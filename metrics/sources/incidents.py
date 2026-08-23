"""
Incidents adapter — the source behind change failure rate and time to restore.

Comes from an incident tracker (PagerDuty, Opsgenie, an internal one), never
from GitHub. Expected record shape:

    {"id": "INC-88", "started_at": "...", "resolved_at": "...",
     "severity": "sev2", "caused_by_deploy": "deploy-1174",
     "caused_by_pr": 4821}

`caused_by_pr` is the only field that attaches an incident to a change. It is
optional, and incidents without it still count toward team-level failure rate
while contributing nothing to any individual's profile — blameless by
construction: an incident never lands on a person's page.
"""
from __future__ import annotations

from .base import Availability, SourceStatus, load_json_file


def load(path: str, start_iso: str, end_iso: str) -> tuple[list[dict], SourceStatus]:
    payload, status = load_json_file("incidents", path)
    if not status.usable:
        return [], status

    records = payload if isinstance(payload, list) else payload.get("incidents", [])
    kept = [
        record for record in records
        if record.get("started_at") and start_iso <= record["started_at"] <= end_iso
    ]
    if not kept:
        return [], SourceStatus("incidents", Availability.EMPTY,
                                f"no incidents inside {start_iso[:7]}")
    return kept, SourceStatus("incidents", Availability.OK,
                              f"{len(kept)} incidents inside {start_iso[:7]}")
