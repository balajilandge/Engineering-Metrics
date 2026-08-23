"""
Board / Linear adapter — issue time-in-state and carryover.

GitHub has no notion of a board column, so this reads a JSON feed you export
from whatever tracker you actually use. Expected record shape (extra keys are
ignored):

    {"id": "ENG-1421", "assignee": "alice", "type": "feature",
     "started_at": "2026-07-02T09:00:00Z", "done_at": "2026-07-08T17:20:00Z",
     "state": "done", "created_at": "2026-06-28T11:00:00Z"}

Unconfigured is the normal case: WIP and carryover then resolve to
"insufficient evidence" rather than being silently derived from PR counts,
which measure a different thing.
"""
from __future__ import annotations

from .base import SourceStatus, load_json_file

REQUIRED_KEYS = ("id",)


def load(path: str, start_iso: str, end_iso: str) -> tuple[list[dict], SourceStatus]:
    payload, status = load_json_file("board", path)
    if not status.usable:
        return [], status

    items = payload if isinstance(payload, list) else payload.get("items", [])
    kept = [
        item for item in items
        if all(key in item for key in REQUIRED_KEYS)
        and _touches_window(item, start_iso, end_iso)
    ]
    return kept, SourceStatus(
        "board", status.availability,
        f"{len(kept)} of {len(items)} board items overlap {start_iso[:7]}",
    )


def _touches_window(item: dict, start_iso: str, end_iso: str) -> bool:
    """An item counts if it was open at any point during the month."""
    created = item.get("created_at") or item.get("started_at") or ""
    done = item.get("done_at") or ""
    if created and created > end_iso:
        return False
    if done and done < start_iso:
        return False
    return bool(created or done)
