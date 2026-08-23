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

This payload contains almost no observable activity. The metrics record one pull request created, zero merged, and zero merged substantive PRs; the per-type breakdown is zero across dependency, config, docs, test, fix and feature. The `pull_requests` array is empty, so there is no diff, title, description or review thread for the single created PR — its content, size and status are unknown. Review activity is also zero: no reviews given, no authors reviewed, no changes requested. Rework is unmeasurable (`measured_over: 0`, `rate_pct: null`), and no reverts were authored. On this data no claim about what Engineer IJ worked on, how hard it was, or what blocked it can be supported; the correct conclusion is that the evidence is missing, not that the work is missing.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** The dataset is empty rather than negative: there are no reverts, no changes-requested, and no failed or reopened work recorded. A single created-but-unmerged PR with no captured diff is consistent with many situations this payload cannot see — work in a repository outside this dataset, a long-running branch, time away from code, on-call or incident work, design or planning work, pairing, or contributions made through someone else's PR. Nothing here contradicts a productive month; the instrumentation simply captured one artifact and no content for it.

**Least favourable reading.** Taken purely at face value, this month produced no merged code and no reviews visible in this dataset: `prs_merged: 0`, `prs_merged_substantive: 0`, `reviews.given: 0`, `authors_reviewed: 0`. The one PR created never merged within the window and left no recorded diff or discussion. On the PR record alone there is no evidence of delivered output or of collaboration with teammates through code review during the period.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- The content, scope, size and current state of the single created PR — the `pull_requests` array is empty, so no diff, title, description or review thread exists.
- Whether the created PR is still open, closed, superseded, or merged outside the measurement window.
- Whether Engineer IJ worked in repositories or systems not covered by this dataset.
- Any design, architecture, RFC or planning work, which leaves no trace in PR data.
- Incident response, on-call load, or production debugging.
- Mentoring, pairing, or review feedback given in DMs, meetings or verbally rather than as GitHub review comments.
- Time away from work (leave, holiday, illness) or reassignment to non-coding duties.
- Whether the engineer was blocked on dependencies, environment access, or another team's deliverable.
- Review latency and rework rate, both of which are null because there was nothing to measure.
- What the one created PR actually was: no title, description, diff, file list, or line count was supplied.
- Whether the month included leave, on-call, incident response, or an interrupt-heavy support rotation.
- Any design, architecture, or scoping work that happened in documents, tickets, or meetings rather than in pull requests.
- Any mentoring, pairing, debugging help, or unblocking done in DMs, chat, or synchronously — none of which appears in PR data.
- Why zero reviews were given: no reviews requested, reviews given outside the tracked repos, or a deliberate focus elsewhere are all indistinguishable here.
- Whether the reported metrics themselves are complete, given that `prs_created` is 1 while `pull_requests` is empty and every `by_type` bucket is 0.
- Any measure of code quality, since no diff or review comment is available.

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
