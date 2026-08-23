# Your month — 2026-07

Repository: `microsoft/vscode`. This page is about your work only; it contains no comparison to anyone else, because none was computed.

**You are reading this before your manager discusses it.** If anything here is wrong or missing context, file a correction (see the end of this page) — corrections are the one thing that feeds back into the interpretation.

## What you shipped

- PRs opened: **1**
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

This payload contains almost no observable activity. The metrics record one pull request created, zero merged, and zero merged substantive PRs, with no per-type breakdown (all type counters are 0) and no churn or time-to-merge figures because nothing merged. The `pull_requests` array is empty, so there is no diff, description, or review thread for the single created PR — its size, subject matter, and current state are all unknown. Review activity is also recorded as zero: no reviews given, no authors reviewed, no changes requested. Rework is measured over 0 PRs, so the rework rate is null rather than good or bad. The honest reading is that this month's data cannot support any statement about what Engineer BX worked on; the 1:1 should start by establishing where the work went, not by interpreting these numbers.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** The dataset is empty of PR-visible work, and PR data is a narrow lens. An engineer with one open, unmerged PR and no review activity may have spent the month on work this payload structurally cannot see: an incident, a design document, a long-running branch not yet opened, onboarding, a migration tracked outside this repository, planned leave, or work in a codebase not covered by this export. The single created PR that never merged is consistent with a large or still-in-progress piece of work rather than an absence of work. Nothing here is evidence of a problem — the rework rate is null because it was measured over 0 PRs, not because quality was poor.

**Least favourable reading.** Across the month there is no merged output (prs_merged: 0, prs_merged_substantive: 0) and no contribution to anyone else's work (reviews given: 0, authors_reviewed: 0). Even the single created PR has no accompanying record, so there is nothing that demonstrably landed or demonstrably helped a colleague. On the evidence available in this repository's PR stream alone, this month left no trace, and if a manager's expectation was steady shipping or review participation, that expectation was not met in any way this data can confirm.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- The identity, scope, size, and status of the single created PR — the pull_requests array is empty, so there is no diff, title, or description.
- Whether the created PR is still open, closed, draft, or blocked on review.
- Whether the engineer was present and working this month at all (leave, sabbatical, on-call rotation, secondment).
- Any work that happened outside pull requests: design docs, RFCs, architecture decisions, incident response, on-call, customer escalations.
- Mentoring, pairing, or code review conducted verbally or in DMs rather than as GitHub review comments.
- Work in other repositories or organisations not included in this export.
- Whether reviewing was an explicit part of this engineer's remit, so whether reviews-given of 0 is a gap or simply not applicable.
- Whether the month was consumed by scope negotiation, requirements churn, or dependency on another team.
- Any quality signal whatsoever: rework rate and time-to-merge are null over a sample of 0.
- Whether Engineer BX worked in repositories or systems not covered by this payload.
- Any design work, RFCs, architecture discussion, or planning that did not produce a pull request.
- Any incident response, on-call load, or production debugging during the month.
- Any mentoring, pairing, code review over DMs or in person, or scope negotiation with stakeholders.
- Whether the engineer was on leave, onboarding, reassigned, or partially allocated during this period.
- Whether zero reviews given reflects an expectation of the role or an absence of review requests directed at them.
- Any qualitative feedback from teammates, since no review comments appear in the payload.

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
