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

The payload for this month contains almost no observable activity: metrics report `prs_created: 1` and `prs_merged: 0`, and the `pull_requests` list is empty, so there is no diff, title, or review thread to read. Every type bucket (dependency, config, docs, test, fix, feature) is zero, and median churn and median time-to-merge are null because nothing merged. Review activity is also recorded as zero given, with no authors reviewed and no changes requested. Rework metrics were measured over zero PRs, so the rework rate is null rather than low. On this evidence I cannot describe what Engineer AK worked on, how hard it was, or what got in the way — the single created PR has no attached record. Any statement about output or contribution this month would be invented rather than observed.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** The dataset simply does not capture this engineer's month. One PR was created but never appears in the `pull_requests` array, which is itself a sign of incomplete capture rather than incomplete work; the engineer may have spent the month on activity this payload structurally cannot see — design documents, incident response, an unmerged long-running branch, onboarding, cross-team support, leave, or work in a repository outside the scope of this export. Zero reviews given and zero rework are equally consistent with someone who was not present in this codebase at all during the period.

**Least favourable reading.** Taken at face value, the recorded footprint in this repository for the month is one unmerged PR, no merged changes of any type, and no code review participation (`reviews.given: 0`, `authors_reviewed: 0`). If this repository was expected to be the engineer's primary area, then neither shipped code nor collaboration through review is visible in it, and the one PR that was opened did not reach merge.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- What the single created PR actually contains — no title, diff, or description is present in the payload.
- Why that PR did not merge: whether it was closed, abandoned, still open at month end, or superseded.
- Whether the engineer was present and working during the whole month (leave, onboarding, rotation, or transfer are all invisible here).
- Whether work happened in other repositories, forks, or branches not covered by this export.
- Any non-PR contribution: design docs, RFCs, incident response, on-call, debugging, pairing, mentoring, or DM-based unblocking.
- Whether reviews were given outside this repository or through channels not captured as GitHub review events.
- Whether scope was negotiated, deferred, or reassigned during the month.
- Any signal about quality, since no diff or review comment exists to read.
- Whether that PR is still open, closed, draft, or was merged outside the measurement window.
- Any mentoring, pairing, or unblocking that happened in DMs, issue threads, or verbally rather than in code review.
- Whether zero reviews given reflects no requests received, a deliberate reallocation of their time, or reviews performed in a system not captured here.
- Whether work was blocked on dependencies, environments, approvals, or another team.
- Scope negotiation: whether planned work was cut, deferred, or absorbed by someone else.

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
