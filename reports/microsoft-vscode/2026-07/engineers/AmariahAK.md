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

This payload contains almost no observable work. The metrics record one PR created, zero merged, zero substantive merges, and zero reviews given; every by_type counter (dependency, config, docs, test, fix, feature) is 0, and median churn, median time-to-merge, and review latency are all null. The pull_requests list is empty, so there is no diff, no title, no review thread, and no PR number attached to the single created PR — nothing that can be read or cited. As a result I cannot describe what was hard, what slowed the work down, or whether anyone else was unblocked, because no artifact in this payload supports any such statement. This is a report about missing data, not about performance: the correct conclusion from this evidence is that the engineer's month is not visible in pull request activity, and the reason for that is not determinable from what is here.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** The absence of merged PRs and reviews is fully consistent with a month spent on work that pull requests do not capture — design, incident response, cross-team support, investigation, onboarding, leave, or a long-running effort still in progress behind the single created PR. The payload contains no diff and no review thread, so there is literally nothing here that contradicts a productive month; the data collection simply did not reach whatever the work was.

**Least favourable reading.** Taken at face value, the tracked output for the month is one created PR that never merged (prs_merged: 0), zero reviews given to zero authors (given: 0, authors_reviewed: 0), and no code landed in any category. On this evidence alone there is no visible contribution to the shared codebase and no visible participation in other people's work, and a reader with only this payload would have no way to see value delivered.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- The identity, title, scope, and current state of the single created PR — pull_requests is empty, so it cannot be examined.
- Whether the engineer was present and working for the full month (leave, illness, onboarding, or a partial month are all consistent with these numbers).
- Any work outside pull requests: design documents, architecture decisions, incident response, on-call, debugging sessions, customer escalations, or migrations coordinated elsewhere.
- Mentoring, pairing, or code review conducted verbally, in DMs, or in tools not captured here (reviews.given: 0 measures only recorded PR reviews).
- Whether the engineer was reassigned, blocked on someone else, or waiting on infrastructure or dependencies during the month.
- Whether work landed in a different repository, fork, or under a different account not included in this payload.
- Code quality, rework rate, or review responsiveness — rework.measured_over is 0, so no rate exists to interpret.
- What Engineer FG actually spent the month on — the payload contains an empty `pull_requests` array and no titles, diffs, or descriptions.
- The content, size, and status of the one PR recorded as created (`prs_created: 1`) — no PR object is present.
- Whether the engineer was on leave, partially allocated, or working in a repository not covered by this payload.
- Any code review or mentoring done via comments, DMs, or synchronous channels (`reviews.given: 0` only shows no recorded PR reviews in this dataset).
- Whether scope was negotiated, blocked by dependencies, or reprioritised mid-month.

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
