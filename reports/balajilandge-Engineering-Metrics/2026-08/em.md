# 1:1 preparation — balajilandge/Engineering-Metrics — 2026-08

**This is an agenda, not a verdict.** Every engineer has already read their own page. Nothing here ranks anyone; there is no ordering in this document that means anything.

## Team

### DORA

| Metric | Value | Basis |
|---|---|---|
| deployment frequency | insufficient evidence | insufficient evidence — needs a deploy feed (DEPLOYS_PATH) or GitHub Deployments; merges are not deploys |
| lead time for changes | 0 hours | median PR open -> merge, n=6 (no deploy feed: this is merge time, not deploy time) |
| change failure rate | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH); revert rate is a weak proxy |
| time to restore | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH) with resolved_at |

### Flow

| Metric | Value | Basis |
|---|---|---|
| review latency | insufficient evidence | insufficient evidence — needs a review by someone other than the author — none of the 6 PRs inspected had one |
| work in progress | 0.5 PRs | median concurrently-open PRs (proxy: no board feed configured) |
| carryover | 0 % | 0 of 6 merged PRs were opened in an earlier month |

### Totals

- PRs created: 6 · merged: 6
- Contributors: 1 · reverts: 0

| PR type | Merged | Counted as substantive |
|---|---:|:---:|
| dependency | 0 | no |
| config | 1 | no |
| docs | 2 | no |
| test | 0 | yes |
| fix | 0 | yes |
| feature | 3 | yes |

## Per engineer

_Interpretation disabled for this run; per-engineer numbers are on each engineer's own page._
## Source availability

| Source | Availability | Detail |
|---|---|---|
| pull_requests | ok | 12 pull requests in window |
| reviews | ok | reviews read for 6 of 6 PRs |
| board | unconfigured | no path configured |
| deploys | empty | repo publishes no GitHub Deployments in window |
| incidents | unconfigured | no path configured |

A metric reading _insufficient evidence_ is not a zero and not a failure — it is a source this pipeline was never given.
