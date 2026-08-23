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

This payload contains almost no observable evidence. The metrics record one pull request created during the month, zero merged, and zero substantive merges; the `pull_requests` array is empty, so there is no diff, title, description, or review thread to read. Review activity is recorded as zero given, with no authors reviewed and no changes requested. Rework metrics are null because they were measured over zero PRs. On this data I cannot describe what Engineer DS worked on, how hard it was, or what it affected — the correct conclusion is that the evidence is insufficient rather than that little work happened.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** The absence of PR records is a gap in the data, not a finding about the work. A month with one open, unmerged PR and no reviews is exactly the shape you would expect from someone whose time went into work that does not surface in a pull-request feed — a long-running design or investigation, an incident, onboarding, cross-team or vendor work, leave, or contributions made in a repository not covered by this export. The single created PR may be substantial and still in flight; because no diff is attached, nothing here contradicts that reading.

**Least favourable reading.** Taken at face value, the tracked repositories show one PR created, zero merged, zero substantive merges, and zero reviews given to zero other authors for the whole month — meaning no shipped change and no reviewer support that this system can see. If the export is complete and the engineer was fully available on these repositories, that is a month with no visible output or collaboration in the code review process, and the manager would have no artifact to point to when asked what landed.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- What the single created PR actually changes — no title, description, diff, or file list is included.
- Whether the created PR is still open, closed, draft, or blocked in review.
- Whether the engineer was available all month (leave, on-call rotation, incident duty, holiday) — attendance is not in this payload.
- Whether work happened in repositories or systems outside the scope of this export.
- Any design documents, RFCs, architecture work, or spikes that did not produce a pull request.
- Mentoring, pairing, code review given verbally or in DMs, and any unblocking of teammates outside GitHub.
- Incident response, on-call debugging, or production operations work.
- Scope negotiation, planning, or reprioritisation that may have redirected the month's effort.
- Whether zero reviews given reflects no requests received, or requests received and not actioned.
- Whether the month included non-code contributions such as data analysis, customer support, or hiring.
- Whether the engineer was present and working for the full month, on leave, onboarding, or partially allocated elsewhere.
- Any work that does not pass through pull requests: design documents, RFCs, architecture decisions, incident response, on-call, debugging sessions, production investigations.
- Mentoring, pairing, or unblocking that happened in DMs, chat, meetings, or verbal review rather than as PR comments.
- Whether the engineer was assigned a long-lived or exploratory project where a low PR count is the expected shape of the work.
- Whether external dependencies, environment problems, or waiting on another team blocked the single PR from merging.
- Code quality, test discipline, or review responsiveness — no diff or review comment exists to assess.
- Scope negotiation: whether the engineer pushed back on, resized, or absorbed additional work this month.

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
