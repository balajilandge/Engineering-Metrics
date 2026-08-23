# Your month — 2026-07

Repository: `microsoft/vscode`. This page is about your work only; it contains no comparison to anyone else, because none was computed.

**You are reading this before your manager discusses it.** If anything here is wrong or missing context, file a correction (see the end of this page) — corrections are the one thing that feeds back into the interpretation.

## What you shipped

- PRs opened: **3**
- PRs merged: **0**
- Of those, substantive (excluding dependency, config, docs): **0**

The two numbers differ because every PR is classified by the files it touches. A lockfile bump and a rewrite are both one PR; only one of them is a month's work.

| PR type | Merged | Counted as substantive |
|---|---:|:---:|
| dependency | 0 | no |
| config | 0 | no |
| docs | 0 | no |
| test | 0 | yes |
| fix | 0 | yes |
| feature | 0 | yes |

## Review work you did for other people

- Reviews given: **0** across **0** other authors
- Median time from PR open to your review: **not measured**

## Rework

- PRs that received a changes-requested review: **0** of 0 measured
- Reverts authored: **0**

Rework is not a defect count. A changes-requested review is often the review process working.

## Read of your month

_Written by a model from your diffs and review comments, with your name removed before it ran. Every claim below survived a check that it cites a real diff; claims that did not cite one were deleted._

This payload contains almost no evidence about the month's work. The metrics block records 3 PRs created, 0 merged and 0 merged-substantive, with every by_type bucket (dependency, config, docs, test, fix, feature) at zero, and median_churn and median_time_to_merge_h both null. Reviews given is 0, authors_reviewed is 0, and the rework block reports measured_over: 0 with rate_pct null and no reverts authored. The pull_requests array is empty, so there are no diffs, titles, descriptions or review comments to read — the three created PRs are counted but not described. On this data I cannot say what Engineer EY worked on, how hard it was, or what happened to the three open PRs; any narrative beyond the counters would be invention.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** Three PRs were opened during the month, and the absence of merges plus an empty pull_requests array is consistent with work that is genuinely in flight — long-running branches, work blocked on external review or dependencies, or work whose visible output falls outside this repository's PR records (design, incident response, pairing, spec work). The zeroed rework block (measured_over: 0, reverts_authored: 0) means nothing in this window was recorded as reverted or as having changes requested. Nothing here shows a problem; it shows a window with no observable output captured by this tooling.

**Least favourable reading.** For the month as measured, there is no merged output at all (prs_merged: 0, prs_merged_substantive: 0), no code review contribution to other people (reviews.given: 0, authors_reviewed: 0), and no PR bodies for the three PRs that were created. Read strictly, the visible collaborative and delivered footprint in this repository for this window is empty, and there is no artifact in the payload a manager could point to as completed work.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- The pull_requests array is empty, so there is no diff, title, description, or file list for any of the 3 created PRs.
- Why 0 of 3 created PRs merged: still open, closed unmerged, awaiting review, blocked on a dependency, or superseded — the data does not distinguish these.
- Whether the 3 PRs are small or large, and whether they are related to one another (median_churn is null).
- Time-to-merge and review latency cannot be computed (both medians null, measured_over: 0).
- Whether Engineer EY reviewed, commented on, or unblocked others outside of formal PR reviews — the reviews counter only records PR review events.
- Any work that does not produce pull requests: design docs, incident response, on-call, migrations executed by hand, customer or cross-team work, mentoring, interviewing.
- Whether this engineer was present and working for the full month (leave, onboarding, rotation onto another repository or another codebase not covered by this payload).
- Whether work landed in a repository or account not included in this anonymized extract.
- Any scope changes, re-prioritisation, or reassignment that would explain the shape of the month.
- The content of the three PRs recorded as created — no titles, diffs, file paths, or line counts are present in the payload.
- Whether those three PRs are still open, closed unmerged, merged after the reporting window, or simply missing from the export.
- Whether the empty `pull_requests` array is a data-extraction failure or an intentional filter (e.g. only merged PRs included), which changes the interpretation entirely.
- Any technical difficulty encountered: with no diffs, no claim about complexity can be supported.
- Any blockers: no review comments, CI results, or timestamps are available to show what slowed work down.
- Any contribution to unblocking others: reviews are recorded as zero, but mentoring, pairing, debugging help, DMs, and design feedback would not appear in this payload even if they occurred.
- Non-PR work of any kind — incident response, on-call, architecture or design work, scoping and planning, interviewing, documentation outside the repo.
- Whether the engineer was present and available for all of this month (leave, onboarding, ramp-up on a new area, or reassignment would all produce this shape of data).
- Whether zero reviews given reflects a team norm, an explicit reallocation of their time, or something else.

### Contested

Claim by claim, the runs differed on the following. These are shown, never averaged. The comparison is textual, so a claim restated in different words can appear here as a difference:

- **summary** differed between runs.
- **most_favourable_reading** differed between runs.
- **least_favourable_reading** differed between runs.

---

## Filing a correction

Add a JSON file at `corrections/microsoft-vscode/2026-07/<your-login>.json`:

```json
{"corrections": ["The refactor in PR #481 was scoped down after an incident review — the smaller diff was the point."]}
```

It is read on the next run and treated as first-hand evidence about work the data does not show. This is the only loop in the system.
