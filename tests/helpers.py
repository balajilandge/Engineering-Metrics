"""Fixture builders shared by the test modules."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.classify import classify_pr, is_revert  # noqa: E402
from metrics.collect import Collection, PullRecord  # noqa: E402
from metrics.sources.base import Availability, SourceStatus  # noqa: E402

START = "2026-07-01T00:00:00Z"
END = "2026-07-31T23:59:59Z"


def make_pr(number, author, title, files, created, merged=None,
            additions=50, deletions=10, reviews=(), detailed=True):
    record = PullRecord(
        number=number, title=title, author=author,
        author_url=f"https://github.com/{author}",
        html_url=f"https://github.com/acme/app/pull/{number}",
        created_at=created, merged_at=merged, closed_at=merged, draft=False,
    )
    record.detailed = detailed
    record.additions = additions
    record.deletions = deletions
    record.changed_files = len(files)
    record.files = list(files)
    record.reviews = [
        {"reviewer": r, "state": s, "submitted_at": t} for r, s, t in reviews
    ]
    submitted = sorted(r["submitted_at"] for r in record.reviews if r["submitted_at"])
    record.first_review_at = submitted[0] if submitted else None
    record.changes_requested = any(
        r["state"] == "CHANGES_REQUESTED" for r in record.reviews)
    record.review_comment_count = len(record.reviews)
    record.pr_type = classify_pr(title, list(files))
    record.revert = is_revert(title)
    return record


def make_collection(pulls, board=(), deploys=(), incidents=(),
                    start=START, end=END, repo="acme/app", month="2026-07"):
    created = [p for p in pulls if start <= p.created_at <= end]
    merged = [p for p in pulls if p.merged_at and start <= p.merged_at <= end]
    statuses = [
        SourceStatus("pull_requests", Availability.OK, f"{len(pulls)} PRs"),
        SourceStatus("reviews", Availability.OK, "reviews read"),
        SourceStatus("board", Availability.OK if board else Availability.UNCONFIGURED, ""),
        SourceStatus("deploys", Availability.OK if deploys else Availability.UNCONFIGURED, ""),
        SourceStatus("incidents", Availability.OK if incidents else Availability.UNCONFIGURED, ""),
    ]
    return Collection(
        repo=repo, month=month, start_iso=start, end_iso=end,
        created=created, merged=merged,
        board_items=list(board), deploy_events=list(deploys),
        incident_events=list(incidents), statuses=statuses,
    )


def make_run(label, claims, summary="Did the work.", gaps=("design work",),
             favourable="Broad delivery.", unfavourable="Narrow delivery.",
             questions=("What was hardest?",)):
    return {
        "engineer": label,
        "summary": summary,
        "complexity": list(claims),
        "blockers": [],
        "unblocking_others": [],
        "most_favourable_reading": favourable,
        "least_favourable_reading": unfavourable,
        "insufficient_evidence": list(gaps),
        "questions_for_the_1_1": list(questions),
    }


def claim(text, pr=1, kind="diff", quote="if resp.partial:"):
    return {"claim": text, "evidence": {"pr": pr, "kind": kind, "quote": quote}}
