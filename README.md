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

For each run, two files are written under `<repo-slug>` (e.g. `vscode`):

- `data/vscode/YYYY-MM.json` — full machine-readable results
- `reports/vscode/YYYY-MM.md` — the leaderboard as a markdown table
- `reports/vscode/latest.md` — always a copy of the newest report

### Example report table

| Rank | Engineer | PRs Created | PRs Merged |
|---:|---|---:|---:|
| 1 | octocat | 23 | 21 |
| 2 | hubot | 15 | 14 |
| 3 | ... | ... | ... |

## Running locally

```bash
export SOURCE_REPO=microsoft/vscode
export TARGET_MONTH=2026-07   # optional, defaults to previous month
export GH_TOKEN=ghp_...       # optional but avoids low rate limits
python scripts/monthly_metrics.py
```
