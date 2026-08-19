# Engineering Metrics

A monthly GitHub Action that measures engineering activity on a public
repository and publishes a per-engineer leaderboard.

- **Source repo (read-only):** [microsoft/vscode](https://github.com/microsoft/vscode)
- **Metrics tracked, per engineer (PR author):**
  - PRs created in the month
  - PRs merged in the month
  - Rank (by PRs merged, ties broken by PRs created)

## How it works

`.github/workflows/monthly-metrics.yml` runs on the 1st of every month
(and on demand via `workflow_dispatch`). It calls
`scripts/monthly_metrics.py`, which:

1. Pages through the target repo's pull requests (via the REST `pulls`
   list endpoint, not the Search API — Search caps out at 1000 results,
   which a high-traffic repo like `microsoft/vscode` exceeds in merged
   PRs most months) to find PRs created in the target month, and
   separately PRs merged in the target month.
2. Aggregates counts per PR author (excluding bot accounts).
3. Ranks engineers by PRs merged and writes the results back into this
   repo.

By default the target month is the previous full calendar month (UTC). You
can override it by running the workflow manually with a `month` input
(`YYYY-MM`) and/or a different `source_repo`.

## Output

For each run, two files are written under `<repo-slug>` (`owner/name` with
the `/` replaced by `-`, e.g. `microsoft-vscode`):

- `data/microsoft-vscode/YYYY-MM.json` — full machine-readable results
- `reports/microsoft-vscode/YYYY-MM.md` — the leaderboard as a markdown table
- `reports/microsoft-vscode/latest.md` — always a copy of the newest report

### Example report

Each report leads with a **Merged PRs by month** table — a rolling
multi-month view ranked by the target month — followed by a detail table
for the target month itself.

| Engineer | May | Jun | Jul | Jul rank |
|---|---:|---:|---:|---:|
| octocat | — | — | 23 | 1 |
| hubot | 16 | 14 | 15 | 2 |
| monalisa | 14 | 15 | 14 | 3 |

An em dash (—) means no merged PRs that month — e.g. an engineer who hadn't
joined yet. A blank cell means that month hasn't been generated yet; run the
workflow with that `month` input to backfill it.

The trend table reads earlier months from the JSON files previous runs
committed, so building it costs no extra API calls. Its width and length are
controlled by `TREND_MONTHS` (default 3) and `TREND_TOP_N` (default 10).

## Metrics we don't track (and why)

Some engineering-analytics reports include columns like *PR quality score*,
*median PR size*, *reviews given*, *rework rate*, and *incidents*. This
system deliberately scopes to **PRs created, PRs merged, and rank** — here's
what it would take to add the rest, and where the GitHub API stops helping:

| Metric | Available from GitHub API? | How |
|---|---|---|
| **Median PR size (LOC)** | Yes | `GET /repos/{owner}/{repo}/pulls/{number}` returns `additions`, `deletions`, `changed_files` per PR. Requires one API call *per PR* (not present in list/search responses) — hundreds of extra calls per month for a repo like vscode. Median = median(additions + deletions) across an engineer's PRs. |
| **Reviews given** | Yes, but costly | `GET /repos/{owner}/{repo}/pulls/{number}/reviews` lists reviewer + timestamp per PR. There's no repo-wide "reviews by user" endpoint — every PR's reviews must be pulled and tallied by reviewer. GraphQL can batch this more efficiently than REST. |
| **Rework rate** | Derivable, not a real metric | Not a GitHub field. A common proxy: % of PRs with a `CHANGES_REQUESTED` review, or with commits pushed after the first review. Needs `.../pulls/{number}/commits` cross-referenced with `.../reviews` per PR, and a formula you define yourself. |
| **PR quality score** | No | Not a GitHub metric. This is a composite score from a paid engineering-analytics tool (LinearB, Swarmia, Jellyfish, Code Climate Velocity, etc.) or a custom internal formula. No API field exists for it. |
| **Incidents** | No | Comes from an incident-management system (PagerDuty, Opsgenie, an internal tracker) linking an outage to the engineer/change that caused it. A public repo exposes no such linkage via GitHub — this is outside the scope of a read-only public-repo integration entirely. |

**Bottom line:** PR size and reviews-given are addable with real API calls,
at real added cost (per-PR fetches instead of the cheap page-scan this
pipeline currently uses). Rework rate can only be *approximated* via a
formula you'd define, not measured directly. PR quality score and incidents
aren't things GitHub exposes for any repo, public or private — they'd
require either a third-party analytics tool or data from a system outside
GitHub entirely.

## Running locally

```bash
export SOURCE_REPO=microsoft/vscode
export TARGET_MONTH=2026-07   # optional, defaults to previous month
export GH_TOKEN=ghp_...       # optional but avoids low rate limits
python scripts/monthly_metrics.py
```
