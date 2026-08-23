# 1:1 preparation — balajilandge/Engineering-Metrics — 2026-08

**This is an agenda, not a verdict.** Every engineer has already read their own page. Nothing here ranks anyone; there is no ordering in this document that means anything.

## Team

### DORA

| Metric | Value | Basis |
|---|---|---|
| deployment frequency | insufficient evidence | insufficient evidence — needs a deploy feed (DEPLOYS_PATH) or GitHub Deployments; merges are not deploys |
| lead time for changes | 0 hours | median PR open -> merge, n=7 (no deploy feed: this is merge time, not deploy time) |
| change failure rate | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH); revert rate is a weak proxy |
| time to restore | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH) with resolved_at |

### Flow

| Metric | Value | Basis |
|---|---|---|
| review latency | insufficient evidence | insufficient evidence — needs a review by someone other than the author — none of the 7 PRs inspected had one |
| work in progress | 0.5 PRs | median concurrently-open PRs (proxy: no board feed configured) |
| carryover | 0 % | 0 of 7 merged PRs were opened in an earlier month |

### Totals

- PRs created: 7 · merged: 7
- Contributors: 1 · reverts: 0

| PR type | Merged | Counted as substantive |
|---|---:|:---:|
| dependency | 0 | no |
| config | 1 | no |
| docs | 2 | no |
| test | 0 | yes |
| fix | 0 | yes |
| feature | 4 | yes |

## Per engineer

### balajilandge

_Interpreted as Engineer A; the model never saw the name._

Engineer A built and then substantially rewrote a GitHub-Actions-based engineering metrics system inside what appears to be their own repository. PR 1 established the whole thing: a workflow plus a 274-line `scripts/monthly_metrics.py` that pages the REST `pulls` endpoint, tallies per-author PR counts, and commits JSON and markdown outputs. PRs 2–6 iterated on that base — a feasibility table for metrics the GitHub API cannot supply (PR 2), a rebase-and-retry push loop (PR 3), a multi-month trend table built from previously committed JSON (PR 4), a default tweak (PR 5), and a README restructure (PR 6). PR 7 then replaced the design outright with a four-layer pipeline (collect / compute / interpret / distribute), an anonymization boundary, a citation-enforcing guardrail gate, a two-phase schedule with a 24-hour embargo on manager-facing pages, and a migration script that removed 1,045 `rank` fields from historical data. All seven PRs merged with a median time to merge of 0.0 hours and zero review comments anywhere in the payload.

**Questions to ask** (not points to deliver):

- PR 7 is 22,317 lines of churn and replaces the ranking model introduced in PR 1. What prompted the change of direction, and how did you decide to do it as one PR rather than in stages?
- None of the seven PRs has a review comment and the median merge time is 0.0 hours. Is that the intended working mode for this repo, and would you want review on something the size of PR 7?
- The README for PR 7 mentions 123 tests and a guardrail gate with three independent anti-ranking checks. Can you walk me through what the gate actually rejects, and what is covered by tests versus asserted in prose?
- PR 6 restructures the README and PR 7 rewrites much of it again shortly after. Was there a point where you knew the redesign was coming, and would you have sequenced the docs work differently?
- Three of the five sources in the PR 7 architecture (board, deploys, incidents) are unconfigured. What would it take to wire even one of them up, and is that blocked on you or on someone else?
- Reviews given is zero for the month. Is there review work you are doing that wouldn't show up here, or has there been nothing to review?
- PR 7 introduces a correction loop where an engineer can contest an interpretation. Has anyone used it yet, and what happens if a correction and the data disagree?

**What this data cannot show:**

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

**Contested between runs — do not present as fact:**

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
- The summary differed between the two runs.
- The most_favourable_reading differed between the two runs.
- The least_favourable_reading differed between the two runs.

**Both readings:**

- Most favourable: Engineer A shipped a working system end to end in one month and then, having seen what it produced, replaced its central premise. PR 1's leaderboard ranked people by merged PR count; PR 7 removes ranking entirely and states why — "the gate strips score-shaped keys and refuses any list of engineers carrying an ordinal. Three independent checks, each of which fails the build rather than shipping a ranking" — and backs the change with a migration that preserved every count while deleting 1,045 rank fields. The engineering along the way is careful about failure modes others would leave implicit: the Search API cap (PR 1), the concurrent-push race (PR 3), the difference between 'no data' and 'zero' in the trend table (PR 4), and missing feeds reporting 'insufficient evidence' rather than zero (PR 7). The documentation is unusually specific for a solo project — PR 2's table says exactly which API endpoint each unavailable metric would need and what it would cost.
- Least favourable: Seven PRs merged with zero external review and a median time to merge of 0.0 hours, including a 22,317-line rewrite (PR 7) that discards the architecture of PR 1 four PRs later. Substantive throughput is 4 of 7 merged PRs; PR 5 changes one default from 15 to 10 across two files (6 lines), and PRs 2 and 6 are README edits, one of which (PR 6) restructures documentation that PR 7 then rewrites again. PR 7's most load-bearing claims are visible only as prose in the README — "123 tests covering the deterministic layers and the gate" and the embargo transcript — and the diff supplied here is truncated before any of `metrics/guardrails.py`, `metrics/anonymize.py` or the test suite can be inspected, so the substance behind the architecture diagram is unverified in this payload. No reviews were given to anyone.

## Source availability

| Source | Availability | Detail |
|---|---|---|
| pull_requests | ok | 14 pull requests in window |
| reviews | ok | reviews read for 7 of 7 PRs |
| board | unconfigured | no path configured |
| deploys | empty | repo publishes no GitHub Deployments in window |
| incidents | unconfigured | no path configured |

A metric reading _insufficient evidence_ is not a zero and not a failure — it is a source this pipeline was never given.
