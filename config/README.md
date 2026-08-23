# Configuration

## `squads.json`

Maps squad name to the GitHub logins in it. Copy `squads.example.json` to
`squads.json` and edit, or point `SQUADS_PATH` somewhere else.

```json
{ "platform": ["octocat", "hubot"], "data": ["monalisa"] }
```

A squad lead's page shows their own squad plus the team aggregate — never
another squad's individuals. With no file present the pipeline falls back to a
single implicit team, which is the right default for a repo with no squad
structure.

## Optional source feeds

Three of the five sources in the architecture do not live in GitHub. Each is a
JSON file you export from the system that actually owns the data, pointed at by
an environment variable. All are optional; metrics that depend on a missing
feed report **insufficient evidence** rather than zero.

| Variable | Source | Record shape |
|---|---|---|
| `BOARD_PATH` | Board / Linear | `{"id", "assignee", "type", "created_at", "started_at", "done_at", "state"}` |
| `DEPLOYS_PATH` | CI & deploys | `{"id", "deployed_at", "environment", "commit_sha", "success"}` |
| `INCIDENTS_PATH` | Incidents | `{"id", "started_at", "resolved_at", "severity", "caused_by_deploy", "caused_by_pr"}` |

Each file is either a JSON array of records, or an object with the records
under `items` / `deploys` / `incidents`.

`caused_by_pr` is the only field linking an incident to a change, and it is
optional. Incidents count toward the team's change failure rate; they never
appear on an individual's page.
