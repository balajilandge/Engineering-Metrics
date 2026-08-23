"""
Layer 2 — Compute. Deterministic, no model.

Two outputs, deliberately shaped differently:

  * A **team** block: the four DORA metrics, review latency, WIP, carryover.
    Team metrics are aggregates and are safe to compare over time.

  * An **individual** block: throughput split by PR type, reviews given,
    rework. A profile, never one score. There is no composite, no rating and
    no rank — not because they are withheld at render time, but because this
    layer never computes one. You cannot leak a number that does not exist.

Every metric that a missing source makes underivable returns a Metric with
`available=False` and a `basis` explaining what would be needed. Downstream
renders that as "insufficient evidence", never as zero.
"""
from __future__ import annotations

import dataclasses
import statistics
from collections import Counter, defaultdict

from .classify import PR_TYPES, substantive_types
from .collect import Collection, PullRecord, hours_between, parse_ts


@dataclasses.dataclass(frozen=True)
class Metric:
    """A number, or an honest account of why there isn't one."""
    name: str
    value: float | int | None
    unit: str
    basis: str
    available: bool = True

    @classmethod
    def unavailable(cls, name: str, unit: str, needs: str) -> "Metric":
        return cls(name=name, value=None, unit=unit,
                   basis=f"insufficient evidence — needs {needs}", available=False)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "basis": self.basis,
            "available": self.available,
        }

    def render(self) -> str:
        if not self.available or self.value is None:
            return "insufficient evidence"
        if isinstance(self.value, float):
            return f"{self.value:g} {self.unit}".strip()
        return f"{self.value} {self.unit}".strip()


def _median(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    return round(statistics.median(clean), 2) if clean else None


# --------------------------------------------------------------------------
# Team — the four DORA metrics
# --------------------------------------------------------------------------

def deployment_frequency(collection: Collection) -> Metric:
    deploys = collection.deploy_events
    if not deploys:
        return Metric.unavailable(
            "deployment_frequency", "per day",
            "a deploy feed (DEPLOYS_PATH) or GitHub Deployments; merges are not deploys")
    start, end = parse_ts(collection.start_iso), parse_ts(collection.end_iso)
    days = max((end - start).days + 1, 1)
    return Metric("deployment_frequency", round(len(deploys) / days, 2), "per day",
                  f"{len(deploys)} deploys over {days} days")


def lead_time_for_changes(collection: Collection) -> Metric:
    """
    PR opened -> deployed. With no deploy feed, opened -> merged is reported
    instead, and the basis says so: it is a different, shorter interval.
    """
    merged = [p for p in collection.merged if p.merged_at]
    if not merged:
        return Metric.unavailable("lead_time_for_changes", "hours",
                                  "at least one merged PR in the month")

    deploys = sorted(
        (d for d in collection.deploy_events if d.get("deployed_at")),
        key=lambda d: d["deployed_at"],
    )
    if deploys:
        durations = []
        for pull in merged:
            after = next((d for d in deploys if d["deployed_at"] >= pull.merged_at), None)
            if after:
                durations.append(hours_between(pull.created_at, after["deployed_at"]))
        value = _median([d for d in durations if d is not None])
        if value is not None:
            return Metric("lead_time_for_changes", value, "hours",
                          f"median PR open -> first deploy after merge, n={len(durations)}")

    value = _median([p.time_to_merge_h for p in merged])
    return Metric("lead_time_for_changes", value, "hours",
                  f"median PR open -> merge, n={len(merged)} "
                  "(no deploy feed: this is merge time, not deploy time)")


def change_failure_rate(collection: Collection) -> Metric:
    incidents = collection.incident_events
    deploys = collection.deploy_events
    if not incidents:
        reverts = [p for p in collection.merged if p.revert]
        if not deploys:
            return Metric.unavailable(
                "change_failure_rate", "%",
                "an incident feed (INCIDENTS_PATH); revert rate is a weak proxy")
        rate = round(100.0 * len(reverts) / max(len(deploys), 1), 2)
        return Metric("change_failure_rate", rate, "%",
                      f"{len(reverts)} reverts / {len(deploys)} deploys "
                      "(proxy: no incident feed configured)")
    denominator = len(deploys) or len([p for p in collection.merged if p.merged_at])
    rate = round(100.0 * len(incidents) / max(denominator, 1), 2)
    return Metric("change_failure_rate", rate, "%",
                  f"{len(incidents)} incidents / {denominator} changes")


def time_to_restore(collection: Collection) -> Metric:
    incidents = collection.incident_events
    if not incidents:
        return Metric.unavailable("time_to_restore", "hours",
                                  "an incident feed (INCIDENTS_PATH) with resolved_at")
    durations = [
        hours_between(i.get("started_at"), i.get("resolved_at"))
        for i in incidents
    ]
    value = _median([d for d in durations if d is not None])
    if value is None:
        return Metric.unavailable("time_to_restore", "hours",
                                  "incidents carrying a resolved_at timestamp")
    return Metric("time_to_restore", value, "hours",
                  f"median incident start -> resolve, n={len(incidents)}")


# --------------------------------------------------------------------------
# Team — flow
# --------------------------------------------------------------------------

def review_latency(collection: Collection) -> Metric:
    pulls = collection.all_pulls
    latencies = [p.time_to_first_review_h for p in pulls
                 if p.detailed and p.time_to_first_review_h is not None]
    if not latencies:
        # Distinguish "we did not look" from "we looked and nobody reviewed".
        # Telling someone to raise DETAIL_BUDGET when the real finding is that
        # PRs merge unreviewed would hide the more important fact.
        detailed = [p for p in pulls if p.detailed]
        if not detailed:
            return Metric.unavailable("review_latency", "hours",
                                      "per-PR review data (raise DETAIL_BUDGET)")
        return Metric.unavailable(
            "review_latency", "hours",
            f"a review by someone other than the author — none of the "
            f"{len(detailed)} PRs inspected had one")
    return Metric("review_latency", _median(latencies), "hours",
                  f"median PR open -> first review, n={len(latencies)}")


def work_in_progress(collection: Collection) -> Metric:
    """
    Median count of PRs open simultaneously, sampled at each PR's open event.
    Board items are preferred when a board feed exists, since a PR is a late
    stage of work and understates true WIP.
    """
    if collection.board_items:
        open_items = [i for i in collection.board_items if not i.get("done_at")]
        return Metric("work_in_progress", len(open_items), "items",
                      f"{len(open_items)} board items unfinished at month end")

    pulls = [p for p in collection.all_pulls if p.created_at]
    if not pulls:
        return Metric.unavailable("work_in_progress", "PRs", "PRs in the month")

    events = sorted(
        [(p.created_at, 1) for p in pulls] +
        [(p.closed_at or collection.end_iso, -1) for p in pulls]
    )
    concurrent, samples = 0, []
    for _, delta in events:
        concurrent += delta
        samples.append(concurrent)
    return Metric("work_in_progress", _median([float(s) for s in samples]), "PRs",
                  "median concurrently-open PRs (proxy: no board feed configured)")


def carryover(collection: Collection) -> Metric:
    """PRs merged this month that were opened before it started."""
    merged = [p for p in collection.merged if p.merged_at]
    if not merged:
        return Metric.unavailable("carryover", "%", "merged PRs in the month")
    carried = [p for p in merged if p.created_at < collection.start_iso]
    return Metric("carryover", round(100.0 * len(carried) / len(merged), 2), "%",
                  f"{len(carried)} of {len(merged)} merged PRs were opened "
                  "in an earlier month")


def compute_team(collection: Collection) -> dict:
    metrics = [
        deployment_frequency(collection),
        lead_time_for_changes(collection),
        change_failure_rate(collection),
        time_to_restore(collection),
        review_latency(collection),
        work_in_progress(collection),
        carryover(collection),
    ]
    merged = [p for p in collection.merged if p.merged_at]
    type_counts = Counter(p.pr_type for p in merged)
    return {
        "dora": [m.to_dict() for m in metrics[:4]],
        "flow": [m.to_dict() for m in metrics[4:]],
        "totals": {
            "prs_created": len(collection.created),
            "prs_merged": len(merged),
            "contributors": len({p.author for p in collection.all_pulls if p.author}),
            "merged_by_type": {t: type_counts.get(t, 0) for t in PR_TYPES},
            "reverts": sum(1 for p in merged if p.revert),
        },
    }


# --------------------------------------------------------------------------
# Individual — a profile, never one score
# --------------------------------------------------------------------------

FORBIDDEN_PROFILE_KEYS = frozenset({"score", "rating", "rank", "grade",
                                    "percentile", "stars", "performance"})


def compute_individuals(collection: Collection, non_substantive: tuple[str, ...]) -> list[dict]:
    substantive = set(substantive_types(non_substantive))

    created_by: dict[str, list[PullRecord]] = defaultdict(list)
    merged_by: dict[str, list[PullRecord]] = defaultdict(list)
    for pull in collection.created:
        created_by[pull.author].append(pull)
    for pull in collection.merged:
        if pull.merged_at:
            merged_by[pull.author].append(pull)

    reviews_given: dict[str, list[dict]] = defaultdict(list)
    for pull in collection.all_pulls:
        for review in pull.reviews:
            reviewer = review.get("reviewer")
            if not reviewer:
                continue
            reviews_given[reviewer].append({
                "pr": pull.number,
                "author": pull.author,
                "state": review.get("state", ""),
                "submitted_at": review.get("submitted_at", ""),
                "latency_h": hours_between(pull.created_at, review.get("submitted_at")),
            })

    logins = set(created_by) | set(merged_by) | set(reviews_given)
    logins.discard("")

    profiles = []
    for login in sorted(logins):
        created = created_by.get(login, [])
        merged = merged_by.get(login, [])
        given = reviews_given.get(login, [])

        merged_types = Counter(p.pr_type for p in merged)
        merged_substantive = [p for p in merged if p.pr_type in substantive]

        detailed = [p for p in merged if p.detailed]
        reworked = [p for p in detailed if p.changes_requested]

        profile_url = next(
            (p.author_url for p in created + merged if p.author_url), "")

        profiles.append({
            "engineer": login,
            "profile_url": profile_url,
            "throughput": {
                "prs_created": len(created),
                "prs_merged": len(merged),
                # The deflation, made explicit: raw count next to the count
                # that survives classification.
                "prs_merged_substantive": len(merged_substantive),
                "by_type": {t: merged_types.get(t, 0) for t in PR_TYPES},
                "median_churn": _median(
                    [float(p.churn) for p in detailed if p.churn is not None]),
                "median_time_to_merge_h": _median(
                    [p.time_to_merge_h for p in merged
                     if p.time_to_merge_h is not None]),
            },
            "reviews": {
                "given": len(given),
                "authors_reviewed": len({r["author"] for r in given
                                         if r["author"] and r["author"] != login}),
                "median_latency_h": _median(
                    [r["latency_h"] for r in given if r["latency_h"] is not None]),
                "changes_requested_given": sum(
                    1 for r in given if r["state"] == "CHANGES_REQUESTED"),
            },
            "rework": {
                "prs_with_changes_requested": len(reworked),
                "measured_over": len(detailed),
                "rate_pct": (round(100.0 * len(reworked) / len(detailed), 2)
                             if detailed else None),
                "reverts_authored": sum(1 for p in merged if p.revert),
            },
            "evidence_prs": sorted(
                ({"number": p.number, "title": p.title, "type": p.pr_type,
                  "url": p.html_url, "churn": p.churn, "detailed": p.detailed}
                 for p in merged),
                key=lambda d: -(d["churn"] or 0),
            )[:20],
        })

    assert_no_scores(profiles)
    return profiles


def assert_no_scores(profiles: list[dict]) -> None:
    """
    Layer 2's own guarantee, enforced rather than documented: no profile may
    carry a composite score, rating or rank. If a future edit adds one, the
    pipeline fails here instead of shipping it.
    """
    def walk(node, path=""):
        if isinstance(node, dict):
            for key, value in node.items():
                lowered = key.lower()
                if lowered in FORBIDDEN_PROFILE_KEYS:
                    raise ValueError(
                        f"Layer 2 produced a forbidden key {path}{key!r}. "
                        "Individual output is a profile, never one score.")
                walk(value, f"{path}{key}.")
        elif isinstance(node, list):
            for item in node:
                walk(item, path)

    walk(profiles)


def compute(collection: Collection, non_substantive: tuple[str, ...]) -> dict:
    return {
        "team": compute_team(collection),
        "individuals": compute_individuals(collection, non_substantive),
    }
