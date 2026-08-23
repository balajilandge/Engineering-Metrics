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

The payload for this month contains almost no observable activity: one pull request was created, none were merged, and no reviews were given (`prs_created: 1`, `prs_merged: 0`, `reviews.given: 0`). The `pull_requests` array is empty, so the single created PR has no title, diff, files, or comments attached — there is nothing about its content, size, or subject matter to describe. All derived metrics are null (`median_churn`, `median_time_to_merge_h`, `median_latency_h`), and the rework block was measured over zero PRs, so it reports nothing either. The by_type breakdown is zero across every category (dependency, config, docs, test, fix, feature), meaning no merged work of any kind is recorded here. This is a data-absence profile rather than a low-output profile: the evidence does not show what this engineer worked on, and it equally does not show that they were idle. Any account of the month has to come from the engineer or from sources outside pull request data.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** The dataset simply does not cover this engineer's month. A single created-but-unmerged PR with no attached diff is consistent with work that lives outside merged pull requests entirely — a long-running branch, an incident, a design or planning cycle, onboarding, leave, work in a repository not captured by this export, or pairing where someone else authored the commits. Nothing in the payload contradicts a productive month; there is no revert, no changes-requested signal, and no failed review interaction, because there is no recorded interaction at all.

**Least favourable reading.** Taken at face value, the month produced no merged code and no peer review contribution: `prs_merged: 0`, `prs_merged_substantive: 0`, `reviews.given: 0`, `authors_reviewed: 0`. The one PR that was opened did not land within the window, and no review latency exists because no reviews were performed. On this evidence alone, the engineer left no trace in the shared repository and no trace in anyone else's pull requests either.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- The content of the single created PR — its title, diff, files touched, size, and whether it is still open, closed, or draft — is absent because `pull_requests` is empty.
- Whether the engineer was present and working for the full month (leave, secondment, on-call rotation, or partial availability are not represented in this data).
- Whether work was done in repositories, forks, or branches outside the scope of this export.
- Any design documents, RFCs, architecture decisions, or technical planning produced this month.
- Incident response, on-call load, production debugging, or operational toil, none of which appears as pull requests.
- Mentoring, pairing, onboarding of others, or code review conducted verbally or in DMs rather than as recorded GitHub reviews.
- Whether the single open PR is blocked on someone else, on a dependency, on an environment, or on a decision — no comments or review history are present.
- Whether the engineer's role in this period was primarily non-code (e.g., interviewing, project coordination, customer support).
- Any measure of quality, complexity, or difficulty of work, since no diff is available to inspect.
- Whether the zero review count reflects no review requests being routed to them or requests going unanswered.
- What the one created PR actually contains — no title, diff, files, or line counts are present in the payload.
- Whether that PR is still open, closed without merge, or blocked on review or CI.
- Whether the month included leave, on-call, incident response, or a rotation onto non-code work.
- Whether mentoring, pairing, code review over DMs/in person, or unblocking of teammates occurred outside GitHub review records.
- Whether scope was negotiated, deferred, or reassigned during the month.
- Whether the absence of reviews given reflects a team norm, a reassignment, or an availability gap.
- Whether any of this engineer's work landed under another author's PR (e.g., pairing or handoff).

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
