# Your month — 2026-07

Repository: `microsoft/vscode`. This page is about your work only; it contains no comparison to anyone else, because none was computed.

**You are reading this before your manager discusses it.** If anything here is wrong or missing context, file a correction (see the end of this page) — corrections are the one thing that feeds back into the interpretation.

## What you shipped

- PRs opened: **0**
- PRs merged: **1**
- Of those, substantive (excluding dependency, config, docs): **1**

The two numbers differ because every PR is classified by the files it touches. A lockfile bump and a rewrite are both one PR; only one of them is a month's work.

| PR type | Merged | Counted as substantive |
|---|---:|:---:|
| dependency | 0 | no |
| config | 0 | no |
| docs | 0 | no |
| test | 0 | yes |
| fix | 0 | yes |
| feature | 1 | yes |

## Review work you did for other people

- Reviews given: **0** across **0** other authors
- Median time from PR open to your review: **not measured**

## Rework

- PRs that received a changes-requested review: **0** of 0 measured
- Reverts authored: **0**

Rework is not a defect count. A changes-requested review is often the review process working.

## Read of your month

_Written by a model from your diffs and review comments, with your name removed before it ran. Every claim below survived a check that it cites a real diff; claims that did not cite one were deleted._

The payload contains a single merged pull request for the month, PR 287966, which makes custom editor models get disposed when their underlying file is deleted. The change adds a `FileOperation.DELETE` branch to the existing file-operation listener in `customEditors.ts`, adds `disposeAllModelsForResource` to the `ICustomEditorModelManager` interface, and implements it in `CustomEditorModelManager` by scanning the reference map for keys prefixed with the resource URI. No PRs were created during the month and none were reviewed; the recorded median time to merge is 4650.76 hours, which suggests this PR was authored well before the month in question and merged inside it. There are no review comments attached to the PR, so there is no visible discussion, pushback, or iteration to read. This is a small, contained fix in a specific VS Code contrib area; the evidence does not extend beyond it.

### What looked hard

_Nothing the evidence supports._

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

_Nothing the evidence supports._

### The same month, read two ways

**Most favourable reading.** Engineer HJ landed a correct, tightly scoped fix to a real state-management bug in the VS Code custom editor stack, closing out a contribution that had been open for months. The change is minimal and well-placed: it hooks the existing file-operation listener rather than adding a new one (`if (e.isOperation(FileOperation.DELETE))`), extends the manager interface deliberately, and documents the reason for the disposal in a comment about "recreating files with the same name." Landing a long-pending change in a large shared codebase often means persistence through review queues and rebases that leave no trace in the PR record, and the absence of any requested changes (`"prs_with_changes_requested": 0`) is consistent with the change being accepted as written.

**Least favourable reading.** The visible output for the month is one small PR that was authored earlier — zero PRs created, zero reviews given, zero changes requested of others — so there is almost no evidence of activity originating in this month. The change itself takes a shortcut that a reviewer might flag: it rebuilds the composite map key inline (`const keyStart = `${resource.toString()}@@@`;`) rather than reusing the manager's own `key()` helper, coupling the new method to an encoding detail, and it fires disposal without awaiting (`value.model.then(x => x.dispose());`) with no test added anywhere in the diff (`"test": 0`). Read strictly on this payload alone, the month shows one modest merge and no collaboration footprint.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- Whether Engineer HJ did substantial work this month that never reached a pull request — design docs, incident response, investigation, or code still in progress.
- Why PR 287966 took ~4650 hours to merge: whether the delay was review queue, CI, maintainer availability, the engineer's own responsiveness, or the PR simply being old and recently rediscovered.
- Whether the engineer is an external or occasional contributor to this repository versus a team member with day-to-day ownership; zero PRs created and zero reviews given are consistent with either.
- Whether the stale-cache bug was validated manually or by an existing test; the diff contains no test changes and no verification notes.
- Whether reviewers raised concerns about the key-prefix matching or fire-and-forget disposal in a channel outside the PR — the review_comments array is empty.
- Any mentoring, pairing, code review outside this repository, or scope negotiation, none of which appear in PR data.
- Whether the engineer's review load is genuinely zero or simply not captured for this repository/time window.
- The reason for the ~194-hundred-hour time to merge (maintainer availability, release branch policy, external contribution queue, or author inactivity) cannot be determined from the data given.
- Whether the DELETE path intentionally skips `asCanonicalUri` normalization used on the MOVE path, or whether that is an oversight, cannot be resolved without the surrounding code and any offline discussion.
- Whether tests exist elsewhere for this behaviour, or whether the reviewer waived them, is not shown; the payload contains no review comments at all.
- Mentoring, pairing, or design review conducted in DMs, issues, or meetings is entirely outside this dataset, so the zero reviews-given figure says nothing about collaboration off the PR surface.
- Whether this repository is the engineer's primary work location, or whether their main output lands in a repo not represented here, is unknown.

### Contested

Both interpretation runs independently raised PR #287966. Where they differ below is in *wording and emphasis*, not in which work they thought worth describing.

Claim by claim, the runs differed on the following. These are shown, never averaged. The comparison is textual, so a claim restated in different words can appear here as a difference:

- (only_in_run_1) The fix required touching three files across the customEditor layer — the service, the shared interface, and the model manager — rather than a single local edit, because the disposal capability did not previously exist on the manager's public surface.
- (only_in_run_1) The implementation depends on knowledge of the internal composite key format used by the manager, reconstructing the `resource@@@viewType` prefix by hand instead of going through the private `key()` helper.
- (only_in_run_1) The disposal path handles models held as promises, disposing asynchronously while removing the map entry synchronously — a lifecycle ordering the author had to decide on.
- (only_in_run_1) The stated motivation is a specific stale-state bug — recreating a file with the same name after deletion — which is a non-obvious failure mode rather than a generic cleanup.
- (only_in_run_2) PR 287966 required reasoning about the model manager's composite key encoding rather than a simple map lookup, because models are keyed by resource and view type together.
- (only_in_run_2) The fix required mutating the reference map while iterating it and disposing models that are stored as promises, i.e. handling asynchronous disposal inside a synchronous method.
- (only_in_run_2) The change spans three files including a public interface, so it touches the contract other implementers of the model manager must satisfy, not just local code.
- (only_in_run_2) The stated root cause is a lifecycle/staleness bug rather than a visible functional gap: stale model references surviving deletion and affecting later recreation of a same-named file.
- (only_in_run_1) The one merged PR sat for an extremely long time before merging: the recorded median time to merge is 4650.76 hours (roughly six months), with zero PRs created this month, indicating the merge closed out work started long before.
- (only_in_run_1) No review activity is recorded on the PR, so whatever caused the long wait is not visible in the data — there is no review comment, requested change, or approval thread to explain it.
- (only_in_run_2) The one merged PR sat for roughly 194 days between opening and merge, indicating a very long review or waiting period outside the engineer's own turnaround.
- (only_in_run_2) There is no recorded review conversation on the PR, so nothing in the payload explains what the delay consisted of or what feedback was needed.
- (only_in_run_1) There is no evidence in this payload of the engineer unblocking anyone: zero reviews were given and zero authors were reviewed.
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
