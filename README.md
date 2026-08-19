# Engineering Metrics

A monthly GitHub Action that measures pull request activity on a public
repository and publishes a per-engineer leaderboard back into this repo.

- **Source repo (read-only):** [microsoft/vscode](https://github.com/microsoft/vscode)
- **Metrics tracked, per engineer (PR author):**
  - PRs created in the month
  - PRs merged in the month
  - Rank (by PRs merged, ties broken by PRs created)

Everything is committed as plain files — no database, no dashboard to host,
no credentials beyond the token GitHub Actions provides automatically.

---

## Viewing the reports

Reports live in [`reports/microsoft-vscode/`](reports/microsoft-vscode) and
render as tables directly in GitHub — no tooling needed.

| File | What it is |
|---|---|
| [`latest.md`](reports/microsoft-vscode/latest.md) | The most recent report. This is the one to bookmark. |
| `YYYY-MM.md` | Per-month archive, e.g. `2026-07.md` |

Each report opens with a **Merged PRs by month** table (a rolling
multi-month view, ranked by the target month), followed by a detail table
for the target month itself.

| Engineer | May | Jun | Jul | Jul rank |
|---|---:|---:|---:|---:|
| octocat | — | — | 23 | 1 |
| hubot | 16 | 14 | 15 | 2 |
| monalisa | 14 | 15 | 14 | 3 |

Cell meanings:

- **A number** — merged PRs that month.
- **An em dash (—)** — no merged PRs that month; e.g. an engineer who hadn't
  joined yet.
- **A blank cell** — that month hasn't been generated yet. Backfill it by
  running the workflow with that `month` input (see below).

The rendered tables show the top 10 engineers. Full data for **every**
engineer is in [`data/microsoft-vscode/`](data/microsoft-vscode) as JSON.

---

## Running it

### On a schedule (automatic)

The workflow runs at **03:00 UTC on the 1st of every month** (cron
`0 3 1 * *`) and reports on the month that just ended. No action needed —
results are committed automatically when it finishes.

### On demand (manual)

1. Open the [**Monthly Engineering Metrics** workflow](../../actions/workflows/monthly-metrics.yml).
2. Click **Run workflow**.
3. Optionally fill in the inputs:

   | Input | Default | Notes |
   |---|---|---|
   | `month` | previous month | Target month as `YYYY-MM`, e.g. `2026-04` |
   | `source_repo` | `microsoft/vscode` | Any public `owner/name` repo |

4. Click the green **Run workflow** button.

A run takes **roughly 5 minutes** against `microsoft/vscode` — it pages
through about 2,000 pull requests twice (once for created, once for
merged). The job commits its own results, so when the run goes green the
report is already in the repo.

### Backfilling history

The trend table can only show months that have a data file. To add an
earlier month, dispatch the workflow with that `month`, then re-run the
current month so the table is redrawn with the new column filled in.

**Run backfills one at a time.** Concurrent runs both generate their data
and then contend on the commit; the workflow retries a rejected push, but
sequential runs are faster than watching retries resolve.

---

## Output

Each run writes three files, under a slug derived from the source repo
(`owner/name` with the `/` replaced by `-`, e.g. `microsoft-vscode`):

- `data/<slug>/YYYY-MM.json` — full machine-readable results, all engineers
- `reports/<slug>/YYYY-MM.md` — the report as markdown tables
- `reports/<slug>/latest.md` — a copy of the newest report

The JSON is the source of truth; the markdown is a rendering of it. The
trend table is built by reading back the JSON that earlier runs committed,
so showing history costs **no extra API calls**.

---

## How it works

`.github/workflows/monthly-metrics.yml` calls `scripts/monthly_metrics.py`,
which:

1. Pages through the target repo's pull requests via the REST `pulls` list
   endpoint to find PRs created in the target month, and separately PRs
   merged in the target month.
2. Aggregates counts per PR author, excluding bot accounts.
3. Ranks engineers by PRs merged, reads prior months back from `data/`, and
   writes the JSON and markdown outputs.

**Why not the Search API?** `search/issues` supports exactly the query this
needs, but truncates at 1,000 results. `microsoft/vscode` merges more than
that in a typical month (July 2026: 1,470), so Search would silently
undercount. Paging the `pulls` endpoint has no such cap.

### Configuration

The two most-used settings are exposed as workflow inputs (`month`,
`source_repo`). The rest are environment variables read by the script — set
them in the workflow's `env:` block, or export them when running locally.

| Variable | Default | Effect |
|---|---|---|
| `SOURCE_REPO` | `microsoft/vscode` | Repo to read stats from |
| `TARGET_MONTH` | previous month | Month to report on, `YYYY-MM` |
| `GH_TOKEN` | — | API auth; the workflow passes `GITHUB_TOKEN` automatically |
| `TREND_MONTHS` | `3` | How many months wide the trend table is |
| `TREND_TOP_N` | `10` | How many rows the trend table shows |
| `TOP_N` | `25` | How many rows the month-detail table shows |

---

## Troubleshooting

Open the failed run from the
[Actions tab](../../actions/workflows/monthly-metrics.yml) and check the
failing step. The metrics step prints its PR counts before committing, so
the logs distinguish a fetch problem from a push problem.

| Symptom | Cause and fix |
|---|---|
| Run is red on **Commit and push results** | Another run pushed first. The step fetches, rebases and retries up to 5 times; if it still fails, re-dispatch that month. |
| Run is red on **Generate monthly PR metrics** | Usually API rate limiting. The script backs off and retries; a persistent failure means the token is missing or the `source_repo` doesn't exist. |
| A month's column is blank in the trend table | That month has no data file yet — backfill it (see above). |
| "No changes to commit" | The run produced output identical to what's already committed. Not an error. |

---

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

### Reading the numbers

PR count measures throughput, not value. It says nothing about scope,
difficulty, review effort, or defect rate — a months-long refactor lands as
one PR just as a typo fix does, and an engineer doing heavy review work may
author fewer PRs precisely because they're unblocking everyone else. Rank is
useful for spotting month-over-month shifts worth asking about; it is not a
performance comparison between individuals.

Note also that **PRs created and PRs merged describe different sets** — a PR
created in June can merge in July — so the two columns should not be divided
into a ratio. An engineer can legitimately merge more PRs in a month than
they opened.

---

## Running locally

```bash
export SOURCE_REPO=microsoft/vscode
export TARGET_MONTH=2026-07   # optional, defaults to previous month
export GH_TOKEN=ghp_...       # optional, but avoids low anonymous rate limits
python scripts/monthly_metrics.py
```

Writes the same `data/` and `reports/` files the workflow does. No
third-party dependencies; verified on Python 3.10–3.13 (CI runs 3.12).
