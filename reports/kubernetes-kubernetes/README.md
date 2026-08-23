# Reports moved

The ranked monthly leaderboard that used to live here is no longer generated.

Reports are now written per audience, under a month directory:

    reports/<repo-slug>/<YYYY-MM>/engineers/<login>.md   each engineer's own page
    reports/<repo-slug>/<YYYY-MM>/em.md                  the 1:1 agenda
    reports/<repo-slug>/<YYYY-MM>/squads/<squad>.md      squad lead view
    reports/<repo-slug>/<YYYY-MM>/founder.md             team metrics and risk

There is no ranked list among them. The pipeline does not produce one, which
is why it cannot leak.

Historical data under `data/` was migrated to schema 2: the per-engineer counts
those runs measured are intact, the `rank` field is gone. Those months predate
PR classification, so they carry no type split — see `schema_v1_import` in the
JSON.
