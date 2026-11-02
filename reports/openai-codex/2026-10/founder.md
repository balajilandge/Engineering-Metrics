# Engineering — openai/codex — 2026-10

Team metrics and risk. **No individual data appears on this page**, by design: individual profiles exist only on each engineer's own page and their manager's 1:1 agenda.

## Delivery

| Metric | Value | Basis |
|---|---|---|
| deployment frequency | insufficient evidence | insufficient evidence — needs a deploy feed (DEPLOYS_PATH) or GitHub Deployments; merges are not deploys |
| lead time for changes | 0.46 hours | median PR open -> merge, n=2 (no deploy feed: this is merge time, not deploy time) |
| change failure rate | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH); revert rate is a weak proxy |
| time to restore | insufficient evidence | insufficient evidence — needs an incident feed (INCIDENTS_PATH) with resolved_at |

## Flow

| Metric | Value | Basis |
|---|---|---|
| review latency | 1.34 hours | median PR open -> first review, n=1 |
| work in progress | 1 PRs | median concurrently-open PRs (proxy: no board feed configured) |
| carryover | 0 % | 0 of 2 merged PRs were opened in an earlier month |

## Volume

- 2 PRs merged by 4 contributors
- Substantive share: 2 of 2 merged PRs

## Risk

- **deployment frequency** cannot be measured — needs a deploy feed (DEPLOYS_PATH) or GitHub Deployments; merges are not deploys.
- **change failure rate** cannot be measured — needs an incident feed (INCIDENTS_PATH); revert rate is a weak proxy.
- **time to restore** cannot be measured — needs an incident feed (INCIDENTS_PATH) with resolved_at.

## What we can and cannot measure

| Source | Availability | Detail |
|---|---|---|
| pull_requests | ok | 2573 pull requests in window |
| reviews | ok | reviews read for 7 of 7 PRs |
| board | unconfigured | no path configured |
| deploys | empty | repo publishes no GitHub Deployments in window |
| incidents | unconfigured | no path configured |
