"""
CI & deploys adapter — the source behind deployment frequency and lead time.

Two ways in:

  * a JSON feed you export from your deployment system (preferred), records
    shaped {"id", "deployed_at", "environment", "commit_sha", "success"}; or
  * GitHub Deployments, when the repo actually uses them.

A merged PR is not a deploy. With neither source configured, deployment
frequency and lead time report "insufficient evidence" rather than quietly
substituting merge events, which would make every repo look like it deploys
on merge.
"""
from __future__ import annotations

from .base import Availability, SourceStatus, load_json_file


def load(path: str, start_iso: str, end_iso: str) -> tuple[list[dict], SourceStatus]:
    payload, status = load_json_file("deploys", path)
    if not status.usable:
        return [], status

    records = payload if isinstance(payload, list) else payload.get("deploys", [])
    kept = [
        record for record in records
        if record.get("deployed_at") and start_iso <= record["deployed_at"] <= end_iso
    ]
    if not kept:
        return [], SourceStatus("deploys", Availability.EMPTY,
                                f"no deploys inside {start_iso[:7]}")
    return kept, SourceStatus("deploys", Availability.OK,
                              f"{len(kept)} deploys inside {start_iso[:7]}")


def load_from_github(client, repo: str, start_iso: str, end_iso: str
                     ) -> tuple[list[dict], SourceStatus]:
    """Fallback: the GitHub Deployments API, for repos that use it."""
    try:
        raw = client.get(f"/repos/{repo}/deployments?per_page=100")
    except Exception as exc:  # noqa: BLE001 - adapter reports, never crashes the run
        return [], SourceStatus("deploys", Availability.ERROR,
                                f"github deployments: {type(exc).__name__}: {exc}")

    kept = [
        {
            "id": str(item.get("id")),
            "deployed_at": item.get("created_at"),
            "environment": item.get("environment", ""),
            "commit_sha": item.get("sha", ""),
            "success": True,
        }
        for item in raw
        if item.get("created_at") and start_iso <= item["created_at"] <= end_iso
    ]
    if not kept:
        return [], SourceStatus("deploys", Availability.EMPTY,
                                "repo publishes no GitHub Deployments in window")
    return kept, SourceStatus("deploys", Availability.OK,
                              f"{len(kept)} GitHub Deployments in window")
