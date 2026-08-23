"""
Layer 4 — Distribute. Policy, not computation.

Four audiences, four different documents built from the same gated data:

  * **Each engineer** — their own page, and nothing about anyone else. Written
    FIRST, before any other audience's page exists on disk.
  * **The EM** — everything, shaped as a 1:1 agenda. Questions, contested
    claims and gaps lead; the numbers support them. Not a verdict.
  * **Squad leads** — their own squad plus the team aggregate. No other
    squad's individuals.
  * **The founder** — team metrics and risk only. No individual pages at all.

"Engineer first" is enforced by an embargo, not by ordering the function calls.
Engineer pages are written in phase `engineers` and stamped in a manifest.
The `rest` phase refuses to write the EM, squad and founder pages until
`embargo_hours` have passed since that stamp. Set EMBARGO_HOURS=0 to run both
phases back to back.

A ranked list is never generated. There is no flag that turns one on, and
`assert_no_ranked_list` runs over every payload on the way out.
"""
from __future__ import annotations

import datetime
import json
import os

from .compute import Metric
from .guardrails import GateResult, assert_no_ranked_list

MANIFEST_NAME = "release-manifest.json"

AUDIENCES = ("engineer", "em", "squad_lead", "founder")


# --------------------------------------------------------------------------
# Embargo
# --------------------------------------------------------------------------

def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def manifest_path(root: str) -> str:
    return os.path.join(root, MANIFEST_NAME)


def read_manifest(root: str) -> dict:
    path = manifest_path(root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}


def write_manifest(root: str, manifest: dict) -> None:
    os.makedirs(root, exist_ok=True)
    with open(manifest_path(root), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


class EmbargoError(RuntimeError):
    """Raised when a later audience is asked for before the engineers have seen theirs."""


def check_embargo(root: str, embargo_hours: int) -> None:
    manifest = read_manifest(root)
    released_at = manifest.get("engineer_pages_released_at")
    if not released_at:
        raise EmbargoError(
            "engineer pages have not been released yet. Run the `engineers` "
            "phase first — every engineer reads their own page before anyone "
            "else discusses it.")
    if embargo_hours <= 0:
        return
    stamp = datetime.datetime.fromisoformat(released_at.replace("Z", "+00:00"))
    elapsed = (_now() - stamp).total_seconds() / 3600.0
    if elapsed < embargo_hours:
        raise EmbargoError(
            f"engineer pages were released {elapsed:.1f}h ago; the embargo is "
            f"{embargo_hours}h. {embargo_hours - elapsed:.1f}h remain before "
            "manager-facing pages may be written.")


# --------------------------------------------------------------------------
# Squads
# --------------------------------------------------------------------------

def load_squads(path: str) -> dict[str, list[str]]:
    """
    {"squad name": ["login", ...]}. Absent file means one implicit team, which
    is the right default for a repo with no squad structure.
    """
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return {name: list(members) for name, members in payload.items()}


def squad_of(login: str, squads: dict[str, list[str]]) -> str | None:
    for name, members in squads.items():
        if login in members:
            return name
    return None


# --------------------------------------------------------------------------
# Markdown fragments
# --------------------------------------------------------------------------

def _metric_rows(metrics: list[dict]) -> list[str]:
    lines = ["| Metric | Value | Basis |", "|---|---|---|"]
    for raw in metrics:
        metric = Metric(**raw)
        name = metric.name.replace("_", " ")
        lines.append(f"| {name} | {metric.render()} | {metric.basis} |")
    return lines


def _claim_lines(claims: list[dict]) -> list[str]:
    if not claims:
        return ["_Nothing the evidence supports._"]
    lines = []
    for claim in claims:
        evidence = claim.get("evidence") or {}
        quote = (evidence.get("quote") or "").replace("\n", " ").strip()
        lines.append(
            f"- {claim.get('claim', '')}  \n"
            f"  ↳ PR #{evidence.get('pr')} ({evidence.get('kind')}): `{quote}`"
        )
    return lines


def _bullets(items: list[str], empty: str) -> list[str]:
    return [f"- {item}" for item in items] if items else [f"_{empty}_"]


def _type_table(by_type: dict[str, int], non_substantive: tuple[str, ...]) -> list[str]:
    lines = ["| PR type | Merged | Counted as substantive |", "|---|---:|:---:|"]
    for pr_type, count in by_type.items():
        counted = "no" if pr_type in non_substantive else "yes"
        lines.append(f"| {pr_type} | {count} | {counted} |")
    return lines


# --------------------------------------------------------------------------
# Engineer page — written first
# --------------------------------------------------------------------------

def render_engineer_page(profile: dict, gated: GateResult | None, repo: str,
                         month: str, non_substantive: tuple[str, ...],
                         layer3_error: str = "") -> str:
    throughput = profile["throughput"]
    reviews = profile["reviews"]
    rework = profile["rework"]

    lines = [
        f"# Your month — {month}",
        "",
        f"Repository: `{repo}`. This page is about your work only; it contains "
        "no comparison to anyone else, because none was computed.",
        "",
        "**You are reading this before your manager discusses it.** If anything "
        "here is wrong or missing context, file a correction (see the end of "
        "this page) — corrections are the one thing that feeds back into the "
        "interpretation.",
        "",
        "## What you shipped",
        "",
        f"- PRs opened: **{throughput['prs_created']}**",
        f"- PRs merged: **{throughput['prs_merged']}**",
        f"- Of those, substantive (excluding "
        f"{', '.join(non_substantive)}): **{throughput['prs_merged_substantive']}**",
        "",
        "The two numbers differ because every PR is classified by the files it "
        "touches. A lockfile bump and a rewrite are both one PR; only one of "
        "them is a month's work.",
        "",
    ]
    lines += _type_table(throughput["by_type"], non_substantive)
    lines += [
        "",
        "## Review work you did for other people",
        "",
        f"- Reviews given: **{reviews['given']}** across "
        f"**{reviews['authors_reviewed']}** other authors",
        f"- Median time from PR open to your review: "
        f"**{reviews['median_latency_h'] if reviews['median_latency_h'] is not None else 'not measured'}**"
        f"{' h' if reviews['median_latency_h'] is not None else ''}",
        "",
        "## Rework",
        "",
        f"- PRs that received a changes-requested review: "
        f"**{rework['prs_with_changes_requested']}** of {rework['measured_over']} measured",
        f"- Reverts authored: **{rework['reverts_authored']}**",
        "",
        "Rework is not a defect count. A changes-requested review is often the "
        "review process working.",
        "",
    ]

    if gated is not None:
        interp = gated.interpretation
        lines += [
            "## Read of your month",
            "",
            "_Written by a model from your diffs and review comments, with your "
            "name removed before it ran. Every claim below survived a check that "
            "it cites a real diff; claims that did not cite one were deleted._",
            "",
            interp.get("summary", ""),
            "",
            "### What looked hard",
            "",
        ]
        lines += _claim_lines(interp.get("complexity", []))
        lines += ["", "### What got in your way", ""]
        lines += _claim_lines(interp.get("blockers", []))
        lines += ["", "### Where you unblocked other people", ""]
        lines += _claim_lines(interp.get("unblocking_others", []))
        lines += [
            "",
            "### The same month, read two ways",
            "",
            "**Most favourable reading.** " + interp.get("most_favourable_reading", ""),
            "",
            "**Least favourable reading.** " + interp.get("least_favourable_reading", ""),
            "",
            "Both readings are of the same evidence. Neither is the verdict.",
            "",
            "### What this data cannot show",
            "",
        ]
        lines += _bullets(interp.get("insufficient_evidence", []),
                          "Nothing flagged — which is itself worth questioning.")

        if gated.contested:
            lines += [
                "",
                "### Contested",
                "",
                "The interpretation ran twice and the runs disagreed on the "
                "following. Disagreements are shown, never averaged:",
                "",
            ]
            for item in gated.disagreements:
                if item["kind"] == "narratives_differ":
                    lines.append(f"- **{item['field']}** differed between runs.")
                else:
                    lines.append(f"- ({item['kind']}) {item.get('claim', item.get('detail',''))}")

        if gated.dropped_claims:
            lines += [
                "",
                "### Dropped for lack of evidence",
                "",
                "The model made these claims and the gate deleted them, because "
                "they cited nothing checkable:",
                "",
            ]
            lines += [f"- ~~{item['claim']}~~ — {item['reason']}"
                      for item in gated.dropped_claims]
    elif layer3_error:
        # Say which of the two it was. "Disabled" and "attempted and failed"
        # are different facts, and the second one means a page is missing
        # content someone expected to be here.
        lines += [
            "## Read of your month",
            "",
            "_**Not generated — interpretation was requested but could not "
            "run.** The numbers above are unaffected; they come from layers "
            "that use no model._",
            "",
            f"> {layer3_error}",
        ]
    else:
        lines += [
            "## Read of your month",
            "",
            "_Not generated: interpretation was switched off for this run, so "
            "this page is the deterministic numbers only._",
        ]

    lines += [
        "",
        "---",
        "",
        "## Filing a correction",
        "",
        f"Add a JSON file at `corrections/{repo.replace('/', '-')}/{month}/"
        "<your-login>.json`:",
        "",
        "```json",
        '{"corrections": ["The refactor in PR #481 was scoped down after an '
        'incident review — the smaller diff was the point."]}',
        "```",
        "",
        "It is read on the next run and treated as first-hand evidence about "
        "work the data does not show. This is the only loop in the system.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# EM page — a 1:1 agenda, not a verdict
# --------------------------------------------------------------------------

def render_em_page(computed: dict, gated: dict[str, GateResult],
                   mapping: dict[str, str], repo: str, month: str,
                   sources: list[dict], non_substantive: tuple[str, ...]) -> str:
    reverse = {label: login for login, label in mapping.items()}
    team = computed["team"]

    lines = [
        f"# 1:1 preparation — {repo} — {month}",
        "",
        "**This is an agenda, not a verdict.** Every engineer has already read "
        "their own page. Nothing here ranks anyone; there is no ordering in "
        "this document that means anything.",
        "",
        "## Team",
        "",
        "### DORA",
        "",
    ]
    lines += _metric_rows(team["dora"])
    lines += ["", "### Flow", ""]
    lines += _metric_rows(team["flow"])

    totals = team["totals"]
    lines += [
        "",
        "### Totals",
        "",
        f"- PRs created: {totals['prs_created']} · merged: {totals['prs_merged']}",
        f"- Contributors: {totals['contributors']} · reverts: {totals['reverts']}",
        "",
    ]
    lines += _type_table(totals["merged_by_type"], non_substantive)

    lines += ["", "## Per engineer", ""]
    if not gated:
        lines.append("_Interpretation disabled for this run; per-engineer "
                     "numbers are on each engineer's own page._")

    for label in sorted(gated):
        result = gated[label]
        login = reverse.get(label, label)
        interp = result.interpretation
        lines += [
            f"### {login}",
            "",
            f"_Interpreted as {label}; the model never saw the name._",
            "",
            interp.get("summary", ""),
            "",
            "**Questions to ask** (not points to deliver):",
            "",
        ]
        lines += _bullets(interp.get("questions_for_the_1_1", []),
                          "None proposed.")
        lines += ["", "**What this data cannot show:**", ""]
        lines += _bullets(interp.get("insufficient_evidence", []), "Nothing flagged.")

        if result.contested:
            lines += ["", "**Contested between runs — do not present as fact:**", ""]
            for item in result.disagreements:
                if item["kind"] == "narratives_differ":
                    lines.append(f"- The {item['field']} differed between the two runs.")
                else:
                    lines.append(f"- ({item['kind']}) {item.get('claim', item.get('detail',''))}")

        lines += [
            "",
            "**Both readings:**",
            "",
            f"- Most favourable: {interp.get('most_favourable_reading', '')}",
            f"- Least favourable: {interp.get('least_favourable_reading', '')}",
            "",
        ]

    lines += ["## Source availability", ""]
    lines += _source_table(sources)
    lines += [
        "",
        "A metric reading _insufficient evidence_ is not a zero and not a "
        "failure — it is a source this pipeline was never given.",
        "",
    ]
    return "\n".join(lines)


def _source_table(sources: list[dict]) -> list[str]:
    lines = ["| Source | Availability | Detail |", "|---|---|---|"]
    for source in sources:
        lines.append(f"| {source['name']} | {source['availability']} | {source['detail']} |")
    return lines


# --------------------------------------------------------------------------
# Squad lead page
# --------------------------------------------------------------------------

def render_squad_page(squad: str, members: list[str], computed: dict,
                      repo: str, month: str, non_substantive: tuple[str, ...]) -> str:
    profiles = [p for p in computed["individuals"] if p["engineer"] in set(members)]
    team = computed["team"]

    lines = [
        f"# Squad — {squad} — {month}",
        "",
        f"Repository: `{repo}`. This page covers **{squad}** plus the team "
        "aggregate. Other squads' individuals are not included.",
        "",
        "## Team aggregate",
        "",
    ]
    lines += _metric_rows(team["dora"])
    lines += [""]
    lines += _metric_rows(team["flow"])

    lines += [
        "",
        f"## {squad} — throughput by type",
        "",
        "| Engineer | Merged | Substantive | Reviews given | Rework |",
        "|---|---:|---:|---:|---:|",
    ]
    # Sorted by name. Any other order would be a ranking with extra steps.
    for profile in sorted(profiles, key=lambda p: p["engineer"].lower()):
        throughput, reviews, rework = profile["throughput"], profile["reviews"], profile["rework"]
        rate = rework["rate_pct"]
        lines.append(
            f"| {profile['engineer']} | {throughput['prs_merged']} | "
            f"{throughput['prs_merged_substantive']} | {reviews['given']} | "
            f"{rate if rate is not None else '—'}{'%' if rate is not None else ''} |"
        )
    if not profiles:
        lines.append("| _no members with activity this month_ | | | | |")

    lines += [
        "",
        "_Rows are alphabetical. This table is not ordered by any measure of "
        "output, and comparing rows down a column is not what it is for: a "
        "reviewer-heavy month legitimately shows fewer merged PRs._",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Founder page — team metrics and risk only
# --------------------------------------------------------------------------

def render_founder_page(computed: dict, repo: str, month: str,
                        sources: list[dict]) -> str:
    team = computed["team"]
    totals = team["totals"]

    risks = []
    for raw in team["dora"] + team["flow"]:
        metric = Metric(**raw)
        if not metric.available:
            risks.append(f"**{metric.name.replace('_', ' ')}** cannot be measured — "
                         f"{metric.basis.replace('insufficient evidence — needs ', 'needs ')}.")
    if totals["reverts"]:
        risks.append(f"{totals['reverts']} revert(s) merged this month.")
    carryover = next((Metric(**m) for m in team["flow"] if m["name"] == "carryover"), None)
    if carryover and carryover.available and (carryover.value or 0) > 50:
        risks.append(f"{carryover.value}% of merged PRs were opened in an earlier "
                     "month — work is spanning month boundaries.")

    lines = [
        f"# Engineering — {repo} — {month}",
        "",
        "Team metrics and risk. **No individual data appears on this page**, by "
        "design: individual profiles exist only on each engineer's own page and "
        "their manager's 1:1 agenda.",
        "",
        "## Delivery",
        "",
    ]
    lines += _metric_rows(team["dora"])
    lines += ["", "## Flow", ""]
    lines += _metric_rows(team["flow"])
    lines += [
        "",
        "## Volume",
        "",
        f"- {totals['prs_merged']} PRs merged by {totals['contributors']} contributors",
        f"- Substantive share: "
        f"{sum(v for k, v in totals['merged_by_type'].items() if k in ('feature', 'fix', 'test'))}"
        f" of {totals['prs_merged']} merged PRs",
        "",
        "## Risk",
        "",
    ]
    lines += _bullets(risks, "Nothing flagged this month.")
    lines += ["", "## What we can and cannot measure", ""]
    lines += _source_table(sources)
    lines += [""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def _write(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def distribute_engineers(root: str, computed: dict, gated: dict[str, GateResult],
                         mapping: dict[str, str], repo: str, month: str,
                         non_substantive: tuple[str, ...],
                         layer3_error: str = "") -> list[str]:
    """Phase 1. Writes every engineer's own page and stamps the manifest."""
    assert_no_ranked_list(computed["individuals"])

    written = []
    for profile in computed["individuals"]:
        login = profile["engineer"]
        label = mapping.get(login)
        result = gated.get(label) if label else None
        page = render_engineer_page(profile, result, repo, month,
                                    non_substantive, layer3_error)
        written.append(_write(os.path.join(root, "engineers", f"{login}.md"), page))

    manifest = read_manifest(root)
    manifest.update({
        "repo": repo,
        "month": month,
        "engineer_pages_released_at": _now().isoformat().replace("+00:00", "Z"),
        "engineer_pages": len(written),
        "audiences_released": ["engineer"],
    })
    write_manifest(root, manifest)
    print(f"Layer 4 distribute [engineers]: {len(written)} pages released")
    return written


def distribute_rest(root: str, computed: dict, gated: dict[str, GateResult],
                    mapping: dict[str, str], repo: str, month: str,
                    sources: list[dict], squads: dict[str, list[str]],
                    non_substantive: tuple[str, ...], embargo_hours: int) -> list[str]:
    """Phase 2. Refuses to run until the engineer embargo has elapsed."""
    check_embargo(root, embargo_hours)

    written = [
        _write(os.path.join(root, "em.md"),
               render_em_page(computed, gated, mapping, repo, month,
                              sources, non_substantive)),
        _write(os.path.join(root, "founder.md"),
               render_founder_page(computed, repo, month, sources)),
    ]

    effective = squads or {"team": [p["engineer"] for p in computed["individuals"]]}
    for squad, members in effective.items():
        slug = squad.lower().replace(" ", "-").replace("/", "-")
        written.append(_write(
            os.path.join(root, "squads", f"{slug}.md"),
            render_squad_page(squad, members, computed, repo, month, non_substantive)))

    manifest = read_manifest(root)
    manifest["audiences_released"] = list(AUDIENCES)
    manifest["manager_pages_released_at"] = _now().isoformat().replace("+00:00", "Z")
    write_manifest(root, manifest)
    print(f"Layer 4 distribute [rest]: {len(written)} pages released")
    return written
