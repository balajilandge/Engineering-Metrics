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

Engineer A built and then substantially redesigned a self-contained engineering-metrics system in a single month across seven merged PRs. PR 1 laid the foundation: a scheduled GitHub Action plus a ~274-line Python script that pages the REST `pulls` endpoint (explicitly avoiding the Search API's 1,000-result cap), retries on rate limits, and writes JSON plus a markdown leaderboard. PRs 2–6 iterated on that base — a feasibility table for metrics GitHub cannot supply (PR 2), a rebase-and-retry push loop for concurrent runs (PR 3), a multi-month trend table read back from committed JSON at no extra API cost (PR 4), a default tweak (PR 5), and a full README restructure with a troubleshooting table (PR 6). PR 7 then replaced the leaderboard premise entirely with a four-layer pipeline (collect / compute / interpret / distribute), an anonymization boundary, a claim-citation gate, an enforced 24-hour embargo before manager-facing pages can be written, and a migration script that stripped 1,045 `rank` fields from historical data; its churn is 22,317 lines. No PR in the payload carries a single review comment, and the pipeline's own output for this repo records that no PR had a review by anyone other than the author.

### What looked hard

- PR 7 encodes a release-ordering policy as an enforced runtime failure rather than a convention: the `rest` phase exits non-zero until the embargo window since the engineer-page release has elapsed.  
  ↳ PR #7 (diff): `Embargo holds: engineer pages were released 0.2h ago; the embargo is 24h.`

### What got in your way

- Median time to merge across the seven PRs is 0.0 hours, consistent with changes landing without an external review gate.  
  ↳ PR #7 (metric): `"median_time_to_merge_h": 0.0`

### Where you unblocked other people

- PR 6 added an operational troubleshooting table mapping each red-step symptom to a cause and a fix, which is documentation aimed at someone other than the author operating the workflow.  
  ↳ PR #6 (diff): `| Run is red on **Commit and push results** | Another run pushed first. The step fetches, rebases and retries up to 5 times; if it still fails, re-dispatch that month. |`

### The same month, read two ways

**Most favourable reading.** Engineer A took a project from an empty repo to a working, tested, opinionated system in one month, and — unusually — recognised mid-stream that the thing they had built (a ranked per-engineer leaderboard, PR 1) was the wrong artifact, then rebuilt it around a defensible policy: anonymization before interpretation, a code gate that drops uncited claims, and 'engineer FIRST' enforced by a non-zero exit rather than by convention (PR 7: 'Embargo holds: engineer pages were released 0.2h ago'). The supporting work is careful in the places that usually bite: Search API truncation avoided in PR 1, concurrent-push contention handled in PR 3, history rendered from committed JSON at zero extra API cost in PR 4, and honest 'insufficient evidence' fallbacks rather than misleading zeros ('A merge is not a deploy'). The documentation (PRs 2 and 6) is written for an operator, not for the author, and PR 7 claims 123 tests running in CI before the pipeline is trusted to produce anything a person reads.

**Least favourable reading.** Seven PRs merged with zero review comments and a median time to merge of 0.0 hours means nothing in this month was checked by another person, and a 22,317-line change (PR 7) landed the same way — a size at which meaningful review is unlikely even if someone had been asked. The month also contains visible churn against the author's own recent decisions: PR 5 retunes a default set days earlier in PR 4, and PR 7 deletes the leaderboard premise PR 1 was built to deliver, stripping 1,045 rank fields from data the same repo produced. Much of the output is prose about how the system should be used (PRs 2 and 6 are docs; PR 7 is largely README and architecture narrative) rather than code exercised by anyone; the pipeline's only demonstrated run is against this repo itself, with one contributor, three of four DORA metrics blank, and the model layer switched off.

Both readings are of the same evidence. Neither is the verdict.

### What this data cannot show

- Whether anyone besides Engineer A uses, depends on, or asked for this system — the only run shown has "contributors": 1 and the source repo default is a public repo (microsoft/vscode) rather than a team's own.
- Whether the absence of reviews reflects a solo/greenfield project, an unavailable reviewer, or a choice — the payload shows the absence but not its cause.
- Whether the 123 tests in PR 7 pass, what they cover in practice, or whether CI was green: the visible diff is truncated before any test file and shows only README claims about them.
- Whether Layer 3 (the model interpretation path) has ever executed — the workflow gates it behind `if: ${{ inputs.interpret }}` and the example run in PR 7 is described as 'generated with Layer 3 off'.
- Any design discussion, RFC, or stakeholder agreement behind the decision to retire the ranked leaderboard and impose an embargo policy — no review comments or linked issues are present.
- Time spent outside PRs: incident response, pairing, DMs, mentoring, scope negotiation, or discussion that led to the PR 1 → PR 7 direction change.
- Whether the PR 5 default change (15 → 10) came from feedback, from rendering the report and eyeballing it, or from something else.
- Cost and rate-limit behaviour of the new per-PR detail fetches (`DETAIL_BUDGET` = 400) against a large repo — no run against a high-traffic repo with the new pipeline is shown.
- Whether this repository is a solo/personal project, a prototype, or something with real users — the 0.0h median merge time and single contributor in the generated data ("contributors": 1) are consistent with all three.
- Whether PR 7's redesign was the result of feedback, a design discussion, or a stated requirement from someone else; no review comments or linked issues appear in the payload.
- Whether the 123 tests referenced in PR 7's README actually exist and pass — the test files and the `metrics/` modules are not in the visible diff, which is truncated.
- Whether the architectural pivot in PR 7 was planned from the start (build simple, then replace) or a late correction; the evidence shows only the outcome.
- Any mentoring, pairing, design review, incident response, or scope negotiation that happened outside a pull request.
- Whether anyone other than the author has run, read, or consumed the reports this system generates.
- How much of PR 7's 22,317 churn is hand-written code versus generated data files — the visible diff includes large committed JSON artifacts such as `data/pallets-flask/2026-07.json` at 1,210 lines.
- Whether the absence of reviews reflects a team norm, a repository with no other collaborators, or a choice by this engineer.

### Contested

The interpretation ran twice and the runs disagreed on the following. Disagreements are shown, never averaged:

- (only_in_run_1) PR 1 chose paginated `pulls` listing over the Search API specifically because Search truncates at 1,000 results, and added a page-scan safety cap plus rate-limit backoff honouring Retry-After.
- (only_in_run_1) PR 4 added a trend table that distinguishes three states — a count, an em dash for 'no merged PRs that month', and a blank for 'month not generated yet' — by reading prior months back from committed JSON rather than making new API calls.
- (only_in_run_1) PR 3 handled concurrent workflow runs contending on the same branch by fetching, rebasing and retrying the push up to five times with escalating sleeps, failing the job explicitly if all attempts fail.
- (only_in_run_1) PR 7 splits a single cron schedule into two phases and resolves the phase from either the dispatch input or the specific cron expression that triggered the run.
- (only_in_run_1) PR 7 is the largest change in the month by a wide margin at 22,317 lines of churn, versus a median of 143 across the seven PRs.
- (only_in_run_1) PR 7 claims a test suite of 123 tests over the deterministic layers and the gate, wired to run in CI before the pipeline itself.
- (only_in_run_2) PR 1 chose the paginated `pulls` REST endpoint over the Search API specifically because Search truncates at 1,000 results, which would silently undercount a high-traffic repo.
- (only_in_run_2) PR 1 handles GitHub rate limiting explicitly, honouring `Retry-After` and falling back to exponential backoff over five attempts.
- (only_in_run_2) PR 1's pagination relies on a sorted-descending early-stop, with a separate `filter_field` so merged-at can be filtered while paging by updated-at.
- (only_in_run_2) PR 4's trend table distinguishes three distinct cell states — a count, an em dash for 'no merged PRs', and a blank for 'month not generated yet' — rather than collapsing missing data into zero.
- (only_in_run_2) PR 3 addresses a concurrency failure mode in the workflow: a rejected push from a competing run is retried up to five times with a fetch and rebase between attempts.
- (only_in_run_2) PR 7 splits the scheduled workflow into two crons and resolves the phase from the triggering schedule, defaulting to `engineers` for anything else.
- (only_in_run_2) PR 7 includes a data migration that rewrote historical artifacts to a new schema and removed the ranking fields the earlier design produced.
- (only_in_run_2) PR 7 designs missing data sources to report 'insufficient evidence' rather than zero, with the rationale stated in the README.
- (only_in_run_1) No PR in this payload received a review comment, and the system's own generated data for this repo records that none of the seven PRs inspected had a review by someone other than the author.
- (only_in_run_1) PR 7 reverses the core premise shipped in PR 1 within the same month: the ranked leaderboard PR 1 built is retired by a migration that deletes 1,045 rank fields and the rendered ranked reports.
- (only_in_run_1) PR 5 changes a default introduced by PR 4 earlier in the same month (TREND_TOP_N from 15 to 10), a six-line follow-up correction to the author's own recent work.
- (only_in_run_1) PR 7 introduces new external dependencies and a paid-API code path (an Anthropic key, two model runs per engineer) that the workflow can only exercise when a secret and an opt-in flag are both present, leaving the interpretation layer unexercised in the default run.
- (only_in_run_2) None of the seven PRs received a review from anyone other than the author, according to the pipeline's own generated output committed in PR 7.
- (only_in_run_2) The month's largest PR reverses the product direction of the six PRs before it: PRs 1, 2, 4 and 6 all shipped and documented a ranked leaderboard, and PR 7 removes it as the thing the architecture exists to prevent.
- (only_in_run_2) Three of the five declared data sources were unavailable in the environment, leaving several team metrics uncomputable in the worked example committed with PR 7.
- (only_in_run_2) PR 5 was a six-line follow-up adjusting a default introduced by PR 4 three PRs earlier, indicating the trend-table sizing was tuned after the fact rather than settled at design time.
- (only_in_run_1) PR 2 documented, for each metric the system does not track, whether GitHub can supply it and at what cost — a decision record for anyone later asked to add those columns.
- (only_in_run_1) PR 7 added a config/README.md specifying the exact record shape for each optional external feed, so someone wiring up a board, deploy or incident export can do it without reading the code.
- (only_in_run_1) There is no evidence in this payload of Engineer A reviewing anyone else's code: reviews given is zero over the month.
- (only_in_run_2) The metrics record zero reviews given to any other author this month, so there is no PR-based evidence of unblocking others through review.
- (only_in_run_2) PR 7 added `config/README.md` documenting the exact record shape of each optional external feed, which is the interface another person would need to wire up a board, deploy or incident source.
- (only_in_run_2) PR 7 builds an explicit correction channel so a subject of the report can inject first-hand context back into the interpretation layer.
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
