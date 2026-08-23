# Squad — team — 2026-08

Repository: `balajilandge/Engineering-Metrics`. This page covers **team** plus the team aggregate. Other squads' individuals are not included.

## Team aggregate

| Metric | Value | Basis |
|---|---|---|
| deployment frequency | insufficient evidence | insufficient evidence — needs a deploy feed (DEPLOYS_PATH) or GitHub Deployments; merges are not deploys |
| lead time for changes | 0 hours | median PR open -> merge, n=6 (no deploy feed: this is merge time, not deploy time) |
| change failure rate | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH); revert rate is a weak proxy |
| time to restore | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH) with resolved_at |

| Metric | Value | Basis |
|---|---|---|
| review latency | insufficient evidence | insufficient evidence — needs a review by someone other than the author — none of the 7 PRs inspected had one |
| work in progress | 0.5 PRs | median concurrently-open PRs (proxy: no board feed configured) |
| carryover | 0 % | 0 of 6 merged PRs were opened in an earlier month |

## team — throughput by type

| Engineer | Merged | Substantive | Reviews given | Rework |
|---|---:|---:|---:|---:|
| balajilandge | 6 | 3 | 0 | 0.0% |

_Rows are alphabetical. This table is not ordered by any measure of output, and comparing rows down a column is not what it is for: a reviewer-heavy month legitimately shows fewer merged PRs._
