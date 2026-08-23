"""
Layer 1 — Collect. Deterministic, no model.

Turns the five sources into one flat, boring record set: per-PR facts, per-
review facts, and the off-GitHub feeds passed through untouched. Nothing here
judges anything; the only opinion is the filename rule in `classify`, and that
rule is fixed in code so its output is not arguable.

The deflation the architecture calls for happens here as a side effect of
classification: a raw count of 23 PRs becomes 14 substantive ones once
dependency, config and docs PRs are labelled as what they are. No model, no
argument — a re-run on the same data produces the same split.
"""
from __future__ import annotations

import calendar
import dataclasses
import datetime
import sys

from .classify import classify_pr, is_revert
from .sources import board as board_source
from .sources import deploys as deploys_source
from .sources import github as github_source
from .sources import incidents as incidents_source
from .sources.base import Availability, SourceStatus


def month_bounds(year_month: str) -> tuple[str, str]:
    year, month = (int(part) for part in year_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return (f"{year:04d}-{month:02d}-01T00:00:00Z",
            f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z")


def parse_ts(value: str | None) -> datetime.datetime | None:
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def hours_between(start: str | None, end: str | None) -> float | None:
    a, b = parse_ts(start), parse_ts(end)
    if a is None or b is None or b < a:
        return None
    return round((b - a).total_seconds() / 3600.0, 2)


@dataclasses.dataclass
class PullRecord:
    number: int
    title: str
    author: str
    author_url: str
    html_url: str
    created_at: str
    merged_at: str | None
    closed_at: str | None
    draft: bool

    # filled in by detail fetches, when budget allows
    detailed: bool = False
    additions: int | None = None
    deletions: int | None = None
    changed_files: int | None = None
    files: list[str] = dataclasses.field(default_factory=list)

    pr_type: str = "feature"
    revert: bool = False

    # review facts
    reviews: list[dict] = dataclasses.field(default_factory=list)
    first_review_at: str | None = None
    changes_requested: bool = False
    review_comment_count: int = 0

    @property
    def churn(self) -> int | None:
        if self.additions is None or self.deletions is None:
            return None
        return self.additions + self.deletions

    @property
    def time_to_first_review_h(self) -> float | None:
        return hours_between(self.created_at, self.first_review_at)

    @property
    def time_to_merge_h(self) -> float | None:
        return hours_between(self.created_at, self.merged_at)

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "author": self.author,
            "author_url": self.author_url,
            "html_url": self.html_url,
            "created_at": self.created_at,
            "merged_at": self.merged_at,
            "closed_at": self.closed_at,
            "draft": self.draft,
            "detailed": self.detailed,
            "additions": self.additions,
            "deletions": self.deletions,
            "changed_files": self.changed_files,
            "churn": self.churn,
            "files": self.files,
            "pr_type": self.pr_type,
            "revert": self.revert,
            "first_review_at": self.first_review_at,
            "changes_requested": self.changes_requested,
            "review_comment_count": self.review_comment_count,
            "time_to_first_review_h": self.time_to_first_review_h,
            "time_to_merge_h": self.time_to_merge_h,
            "reviews": self.reviews,
        }


@dataclasses.dataclass
class Collection:
    repo: str
    month: str
    start_iso: str
    end_iso: str
    created: list[PullRecord]
    merged: list[PullRecord]
    board_items: list[dict]
    deploy_events: list[dict]
    incident_events: list[dict]
    statuses: list[SourceStatus]
    api_calls: int = 0

    @property
    def all_pulls(self) -> list[PullRecord]:
        seen: dict[int, PullRecord] = {}
        for record in self.created + self.merged:
            seen.setdefault(record.number, record)
        return list(seen.values())

    def status(self, name: str) -> SourceStatus:
        for status in self.statuses:
            if status.name == name:
                return status
        return SourceStatus(name, Availability.UNCONFIGURED, "not collected")

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "month": self.month,
            "period": {"start": self.start_iso, "end": self.end_iso},
            "sources": [s.to_dict() for s in self.statuses],
            "api_calls": self.api_calls,
            "pulls_created": [p.to_dict() for p in self.created],
            "pulls_merged": [p.to_dict() for p in self.merged],
            "board_items": self.board_items,
            "deploys": self.deploy_events,
            "incidents": self.incident_events,
        }


def _record_from_item(item: dict) -> PullRecord | None:
    user = item.get("user") or {}
    if github_source.is_bot(user):
        return None
    return PullRecord(
        number=item.get("number", 0),
        title=item.get("title", "") or "",
        author=user.get("login", ""),
        author_url=user.get("html_url", ""),
        html_url=item.get("html_url", ""),
        created_at=item.get("created_at", ""),
        merged_at=item.get("merged_at"),
        closed_at=item.get("closed_at"),
        draft=bool(item.get("draft")),
    )


def _enrich(client: github_source.GitHubClient, repo: str,
            record: PullRecord, want_reviews: bool = True) -> None:
    """One PR's detail: size, files, reviews. Three calls at most."""
    try:
        detail = client.pull_detail(repo, record.number)
        record.additions = detail.get("additions")
        record.deletions = detail.get("deletions")
        record.changed_files = detail.get("changed_files")

        files = client.pull_files(repo, record.number)
        record.files = [f.get("filename", "") for f in files if f.get("filename")]

        if want_reviews:
            reviews = client.pull_reviews(repo, record.number)
            record.reviews = [
                {
                    "reviewer": (r.get("user") or {}).get("login", ""),
                    "state": r.get("state", ""),
                    "submitted_at": r.get("submitted_at", ""),
                }
                for r in reviews
                if not github_source.is_bot(r.get("user"))
                and (r.get("user") or {}).get("login") != record.author
            ]
            submitted = sorted(
                r["submitted_at"] for r in record.reviews if r["submitted_at"]
            )
            record.first_review_at = submitted[0] if submitted else None
            record.changes_requested = any(
                r["state"] == "CHANGES_REQUESTED" for r in record.reviews
            )
            record.review_comment_count = len(record.reviews)
        record.detailed = True
    except Exception as exc:  # noqa: BLE001 - one bad PR must not sink the run
        print(f"  warning: detail fetch failed for #{record.number}: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)


def collect(config) -> Collection:
    """Runs every source adapter and returns the flat record set."""
    start_iso, end_iso = month_bounds(config.month)
    client = github_source.GitHubClient(config.token, config.max_pages)

    print(f"Layer 1 collect: {config.repo} {config.month} ({start_iso}..{end_iso})")

    created_raw = client.paged_pulls(
        config.repo, state="all", sort="created", sort_field="created_at",
        start_iso=start_iso, end_iso=end_iso,
    )
    merged_raw = client.paged_pulls(
        config.repo, state="closed", sort="updated", sort_field="updated_at",
        filter_field="merged_at", start_iso=start_iso, end_iso=end_iso,
    )
    print(f"  created: {len(created_raw)}  merged: {len(merged_raw)}")

    created = [r for r in (_record_from_item(i) for i in created_raw) if r]
    merged = [r for r in (_record_from_item(i) for i in merged_raw) if r]

    # Deduplicate before spending detail budget: a PR created and merged in
    # the same month appears in both lists and must be enriched once.
    unique: dict[int, PullRecord] = {}
    for record in created + merged:
        unique.setdefault(record.number, record)

    # Merged PRs carry the most signal, so they get the budget first.
    merged_numbers = {r.number for r in merged}
    ordered = sorted(unique.values(),
                     key=lambda r: (r.number not in merged_numbers, -r.number))

    budget = min(config.detail_budget, len(ordered))
    print(f"  enriching {budget} of {len(ordered)} PRs (detail budget)")
    for record in ordered[:budget]:
        _enrich(client, config.repo, record)

    # Classification runs over every PR, enriched or not. Without a file list
    # the rule falls back to the title split, and `detailed` records that.
    for record in unique.values():
        record.pr_type = classify_pr(record.title, record.files)
        record.revert = is_revert(record.title)

    # Re-point the created/merged lists at the deduplicated, enriched records.
    created = [unique[r.number] for r in created]
    merged = [unique[r.number] for r in merged]

    statuses = [github_source.status_for(created_raw + merged_raw, config.token)]

    detailed_count = sum(1 for r in unique.values() if r.detailed)
    statuses.append(SourceStatus(
        "reviews",
        Availability.OK if detailed_count else Availability.EMPTY,
        f"reviews read for {detailed_count} of {len(unique)} PRs",
    ))

    board_items, board_status = board_source.load(config.board_path, start_iso, end_iso)
    statuses.append(board_status)

    deploy_events, deploy_status = deploys_source.load(config.deploys_path, start_iso, end_iso)
    if not deploy_status.usable and not config.deploys_path:
        deploy_events, deploy_status = deploys_source.load_from_github(
            client, config.repo, start_iso, end_iso)
    statuses.append(deploy_status)

    incident_events, incident_status = incidents_source.load(
        config.incidents_path, start_iso, end_iso)
    statuses.append(incident_status)

    for status in statuses:
        print(f"  source {status.name:14} {status.availability.value:13} {status.detail}")

    return Collection(
        repo=config.repo, month=config.month,
        start_iso=start_iso, end_iso=end_iso,
        created=created, merged=merged,
        board_items=board_items, deploy_events=deploy_events,
        incident_events=incident_events,
        statuses=statuses, api_calls=client.calls,
    )
