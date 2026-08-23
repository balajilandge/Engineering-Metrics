# Your month — 2026-08

Repository: `balajilandge/Engineering-Metrics`. This page is about your work only; it contains no comparison to anyone else, because none was computed.

**You are reading this before your manager discusses it.** If anything here is wrong or missing context, file a correction (see the end of this page) — corrections are the one thing that feeds back into the interpretation.

## What you shipped

- PRs opened: **7**
- PRs merged: **7**
- Of those, substantive (excluding dependency, config, docs): **4**

The two numbers differ because every PR is classified by the files it touches. A lockfile bump and a rewrite are both one PR; only one of them is a month's work.

| PR type | Merged | Counted as substantive |
|---|---:|:---:|
| dependency | 0 | no |
| config | 1 | no |
| docs | 2 | no |
| test | 0 | yes |
| fix | 0 | yes |
| feature | 4 | yes |

## Review work you did for other people

- Reviews given: **0** across **0** other authors
- Median time from PR open to your review: **not measured**

## Rework

- PRs that received a changes-requested review: **0** of 7 measured
- Reverts authored: **0**

Rework is not a defect count. A changes-requested review is often the review process working.

## Read of your month

_Written by a model from your diffs and review comments, with your name removed before it ran. Every claim below survived a check that it cites a real diff; claims that did not cite one were deleted._

Engineer A built and then substantially rewrote a GitHub-Actions-based engineering metrics system inside what appears to be their own repository. PR 1 established the whole thing: a workflow plus a 274-line `scripts/monthly_metrics.py` that pages the REST `pulls` endpoint, tallies per-author PR counts, and commits JSON and markdown outputs. PRs 2–6 iterated on that base — a feasibility table for metrics the GitHub API cannot supply (PR 2), a rebase-and-retry push loop (PR 3), a multi-month trend table built from previously committed JSON (PR 4), a default tweak (PR 5), and a README restructure (PR 6). PR 7 then replaced the design outright with a four-layer pipeline (collect / compute / interpret / distribute), an anonymization boundary, a citation-enforcing guardrail gate, a two-phase schedule with a 24-hour embargo on manager-facing pages, and a migration script that removed 1,045 `rank` fields from historical data. All seven PRs merged with a median time to merge of 0.0 hours and zero review comments anywhere in the payload.

### What looked hard

- PR 1 chose the paginated `pulls` list endpoint over the Search API specifically to avoid a silent undercount at high PR volume, and documented the reasoning in the module docstring.  
  ↳ PR #1 (diff): `Uses the paginated `/repos/{owner}/{repo}/pulls` list endpoint (sorted by +created/updated) rather than the Search API, since Search caps results at +1000 items and a high-traffic repo like microsoft/vscode comfortably +exceeds that in merged PRs per month.`
- PR 1 handles GitHub rate limiting with a bounded retry that honours `Retry-After` and falls back to exponential backoff.  
  ↳ PR #1 (diff): `if exc.code in (403, 429) and attempt < 5: +                wait = int(exc.headers.get("Retry-After", "0")) or (2 ** attempt)`

### What got in your way

_Nothing the evidence supports._

### Where you unblocked other people

- PR 6 adds operator-facing troubleshooting material mapping failure symptoms to causes and fixes, which is written for someone other than the author.  
  ↳ PR #6 (diff): `| Run is red on **Commit and push results** | Another run pushed first. The step fetches, rebases and retries up to 5 times; if it still fails, re-dispatch that month. |`

### The same month, read two ways

**Most favourable reading.** Engineer A shipped a working system end to end in one month and then, having seen what it produced, replaced its central premise. PR 1's leaderboard ranked people by merged PR count; PR 7 removes ranking entirely and states why — "the gate strips score-shaped keys and refuses any list of engineers carrying an ordinal. Three independent checks, each of which fails the build rather than shipping a ranking" — and backs the change with a migration that preserved every count while deleting 1,045 rank fields. The engineering along the way is careful about failure modes others would leave implicit: the Search API cap (PR 1), the concurrent-push race (PR 3), the difference between 'no data' and 'zero' in the trend table (PR 4), and missing feeds reporting 'insufficient evidence' rather than zero (PR 7). The documentation is unusually specific for a solo project — PR 2's table says exactly which API endpoint each unavailable metric would need and what it would cost.

**Least favourable reading.** Seven PRs merged with zero external review and a median time to merge of 0.0 hours, including a 22,317-line rewrite (PR 7) that discards the architecture of PR 1 four PRs later. Substantive throughput is 4 of 7 merged PRs; PR 5 changes one default from 15 to 10 across two files (6 lines), and PRs 2 and 6 are README edits, one of which (PR 6) restructures documentation that PR 7 then rewrites again. PR 7's most load-bearing claims are visible only as prose in the README — "123 tests covering the deterministic layers and the gate" and the embargo transcript — and the diff supplied here is truncated before any of `metrics/guardrails.py`, `metrics/anonymize.py` or the test suite can be inspected, so the substance behind the architecture diagram is unverified in this payload. No reviews were given to anyone.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- The PR 7 diff is truncated mid-file; the actual implementation of `metrics/classify.py`, `compute.py`, `anonymize.py`, `interpret.py`, `guardrails.py`, `distribute.py`, `corrections.py` and `pipeline.py` is not present, so the quality of the code behind the README's architecture cannot be assessed.
- The claim of "123 tests covering the deterministic layers and the gate" appears only in README prose in PR 7; no test files appear in the visible diff.
- Whether the PR 1 → PR 7 redesign was self-directed, requested by someone, or a response to feedback received outside a PR. No review comments exist on any PR in this payload.
- Whether this repository has any users or collaborators beyond the author. The generated data shows `"contributors": 1` for this repo, but that measures PR authorship, not usage.
- Whether the zero reviews given reflects an absence of review work or a context in which no one else was authoring code to review.
- Whether the 0.0h median time to merge reflects self-merge policy, a solo repo, or something else.
- Any design work, scoping conversations, mentoring, incident response, or discussion that happened outside a pull request.
- Whether the pipeline described in PR 7 has actually been run against a real multi-engineer team, or only against this repo and a single pallets/flask backfill.
- Whether this repository is a personal/side project, a sanctioned internal tool, or something with real users — nothing in the payload identifies stakeholders or consumers.
- Whether the absence of reviews reflects a solo repo with no available reviewers, a choice not to seek review, or a team norm; the data shows only that no PR had a review by someone other than the author.
- Whether the rearchitecture in PR 7 was self-initiated or requested — no issue links, design docs, or discussion appear in the payload.
- Whether the 123 tests claimed in PR 7's README exist and pass; the provided diff shows the README claim and the workflow's `python -m unittest discover -s tests -v` step, but no test files.
- Whether the guardrail gate, anonymization boundary and score-key stripping described in PR 7's README are actually implemented as described; only `metrics/guardrails.py` and `metrics/anonymize.py` filenames appear in the layout block, not their contents.
- Whether the pipeline has ever been run end-to-end with Layer 3 enabled against a real API key, or only with interpretation off.
- Whether PRs 1–6 were ever used in production before PR 7 superseded them, and whether anyone depended on the leaderboard output that the migration deleted.

### Contested

Both interpretation runs independently raised PR #1, PR #3, PR #4, PR #6, PR #7. Where they differ below is in *wording and emphasis*, not in which work they thought worth describing.

Only one run raised PR #2 — treat those as genuinely unsettled.

Claim by claim, the runs differed on the following. These are shown, never averaged. The comparison is textual, so a claim restated in different words can appear here as a difference:

- (only_in_run_1) PR 1's pagination separates the field used for early termination from the field used for filtering, so that PRs merged in a month can be found by scanning an updated-sorted list.
- (only_in_run_1) PR 4's trend table distinguishes three different absences — no data file for a month, an engineer absent from a month that does have data, and a present count — rather than collapsing them into zero.
- (only_in_run_1) PR 3 addresses a concurrency failure mode in the commit step by rebasing onto the remote branch and retrying the push up to five times with increasing sleeps, failing the job explicitly if all attempts fail.
- (only_in_run_1) PR 7 encodes an ordering constraint (engineer sees their page before managers do) as a runtime failure with a non-zero exit code and a two-cron schedule, rather than as a convention.
- (only_in_run_1) PR 7 is a very large change (22,317 lines of churn) that replaces the ranked leaderboard model from PR 1 and includes a one-off migration removing rank fields from historical data.
- (only_in_run_1) PR 7 makes missing off-GitHub data sources surface as explicit 'insufficient evidence' rather than as zero, and carries that through the generated data files.
- (only_in_run_2) PR 1 implements early-exit pagination that relies on the sort order being descending, with a separate filter field so 'created in month' and 'merged in month' can be gathered from differently-sorted listings.
- (only_in_run_2) PR 4's trend table distinguishes three distinct empty states — no data file for a month (blank), engineer absent from a month that does have data (em dash), and a number — rather than collapsing them all to zero.
- (only_in_run_2) PR 4 builds multi-month history by reading back JSON committed by earlier runs, avoiding additional API calls for historical months.
- (only_in_run_2) PR 7 encodes an ordering constraint as a runtime failure rather than a convention: the `rest` phase exits non-zero if the engineer-facing release has not been stamped or the embargo has not elapsed.
- (only_in_run_2) PR 7 adds phase-resolution logic to the workflow that infers the phase from which cron schedule fired, with manual dispatch able to override it.
- (only_in_run_2) PR 7 makes missing data sources report absence rather than zero, and encodes that in the emitted JSON (`value: null` with a `basis` string explaining what feed is needed).
- (only_in_run_2) PR 7 includes a one-off migration that rewrote historical data files to a new schema and stripped 1,045 `rank` fields, plus deletion of the previously rendered ranked reports.
- (only_in_run_1) None of the seven PRs carries a single review comment in this payload, and the pipeline's own output records that no PR it inspected had a review by anyone other than the author.
- (only_in_run_1) Median time to merge across all seven PRs is 0.0 hours, consistent with self-merge and no waiting on review.
- (only_in_run_1) The GitHub API itself constrained what could be measured; PR 2 documents which metrics are unavailable or only approximable and why.
- (only_in_run_1) Concurrent workflow runs contending on the same commit was a real failure mode that required a code fix and then a documented operational workaround.
- (only_in_run_1) Three of the five data sources the PR 7 architecture depends on were not configured when the pipeline was run against this repo, so most DORA metrics could not be produced.
- (only_in_run_2) Concurrent workflow runs contending on `git push` was a real operational problem the engineer had to work around; PR 3 adds a five-attempt fetch/rebase/retry loop rather than relying on a single push.
- (only_in_run_2) The same contention constrained how the tool can be used, and the engineer had to document a manual workaround rather than solve it in code.
- (only_in_run_2) No PR in this month received a review from anyone other than the author, so there was no external checkpoint on any of the work — including the 22,317-churn rearchitecture.
- (only_in_run_2) Three of five intended data sources were unavailable in the environment, so several outputs of the system the engineer built cannot currently produce values.
- (only_in_run_2) Work shipped in PRs 1, 4 and 5 was superseded within the same month by PR 7, which removed the leaderboard and rank concept those PRs built.
- (only_in_run_1) No code reviews were given to anyone during the month; the reviews metrics are all zero or null.
- (only_in_run_1) PR 7 adds a `config/README.md` documenting the record shape of each optional external feed so others can wire them up.
- (only_in_run_1) PR 7 builds an explicit feedback channel for engineers to contest interpretations of their own work, with a worked example.
- (only_in_run_2) The metrics recorded zero reviews given and zero authors reviewed, so the payload contains no in-PR evidence of Engineer A unblocking another person.
- (only_in_run_2) PR 7 adds a `config/README.md` documenting the exact record shape each optional external feed must supply, so someone else could wire up a board, deploy or incident export without reading the adapter code.
- (only_in_run_2) PR 7 ships a generated worked example of all four audience outputs so a reader can see what each audience receives without running the pipeline.
- **summary** differed between runs.
- **most_favourable_reading** differed between runs.
- **least_favourable_reading** differed between runs.

---

## Filing a correction

Add a JSON file at `corrections/balajilandge-Engineering-Metrics/2026-08/<your-login>.json`:

```json
{"corrections": ["The refactor in PR #481 was scoped down after an incident review — the smaller diff was the point."]}
```

It is read on the next run and treated as first-hand evidence about work the data does not show. This is the only loop in the system.
