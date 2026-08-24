# Engineering Metrics

A four-layer pipeline that measures engineering work on a GitHub repository and
distributes what it finds to four different audiences — each getting only what
they should see, and the engineer getting theirs first.

```
SOURCES   pull requests · reviews given · board/Linear · CI & deploys · incidents
   |
[1] COLLECT      deterministic, no model
   |             size, files, timestamps, reviews, reverts, churn, time-in-state
   |             classify every PR by filename rule:
   |             dependency · config · docs · test · fix · feature
   |                          ↓ 23 becomes 14 — no model, no argument
[2] COMPUTE      deterministic, no model
   |             team: the four DORA metrics · review latency · WIP · carryover
   |             individual: throughput split by PR type · reviews · rework
   |                         — a profile, never one score
   |                          ↓ names stripped → Engineer A, B, C
[3] INTERPRET    THE ONLY PLACE A MODEL RUNS
   |             reads diffs and review comments; returns plain-English summary,
   |             complexity with the diff cited, blockers, evidence of
   |             unblocking others. Must give the most and least favourable
   |             reading. "Insufficient evidence" is allowed.
   |                          ↓ JSON — every claim carries an evidence field
GUARDRAIL GATE   no citation → claim dropped in code
   |             two runs disagree → flagged, never averaged
   |             no rating, no rank
[4] DISTRIBUTE   who sees what
   |
   ├── each engineer  their own page — FIRST, before anyone discusses it ──┐
   ├── the EM         everything, as a 1:1 agenda — not a verdict          │
   ├── squad leads    their own squad + team aggregate                     │
   ├── founder        team metrics and risk only                           │
   └── ranked list    NEVER GENERATED, so it cannot leak                   │
                                                                           │
        1:1 correction — the only loop ────────────────────────────────────┘
                         (back into layer 3)
```

**Layers 1, 2 and the gate are code. Layer 3 is the model. Layer 4 is policy.**

---

## The three ideas this encodes

**A PR count is not a measure of work.** Layer 1 classifies every PR by the
files it touches, before anything counts it. A month of 23 merged PRs where
nine are lockfile bumps, CI tweaks and typo fixes is a month of 14 substantive
PRs. That deflation happens in code from filenames, so there is nothing to
argue about — and both numbers are always shown, so nothing is hidden either.

**A model should interpret, not measure.** Every number comes from Layer 2,
which has no model in it. The model reads diffs and review comments and says
what the work *was* — the part a count genuinely cannot capture. It is required
to give both the most and the least favourable reading of the same evidence,
and to say "insufficient evidence" when that is the truth. Then a code gate
deletes any claim that cites nothing.

**A ranked list is a leak waiting to happen.** So one is never generated. Not
suppressed at render time, not access-controlled — never computed. Layer 2's
individual output has no score field; Layer 3's schema has nowhere to put one;
the gate strips score-shaped keys and refuses any list of engineers carrying an
ordinal. Three independent checks, each of which fails the build rather than
shipping a ranking.

---

## What each audience gets

| Audience | File | Contains | Explicitly excludes |
|---|---|---|---|
| Each engineer | `reports/<slug>/<month>/engineers/<login>.md` | Their own numbers, their own interpretation, both readings, what the data can't show, dropped claims | Anyone else's data |
| The EM | `reports/<slug>/<month>/em.md` | Everything, framed as questions to ask | Any ordering that means anything |
| Squad leads | `reports/<slug>/<month>/squads/<squad>.md` | Their squad + team aggregate | Other squads' individuals |
| Founder | `reports/<slug>/<month>/founder.md` | Team metrics and risk | All individual data |

### "Engineer FIRST" is enforced, not intended

The engineer's page is not merely written first — the manager-facing pages
**cannot be written** until the embargo expires. Phase `engineers` releases the
engineer pages and stamps `release-manifest.json`. Phase `rest` reads that
stamp and refuses to run until `EMBARGO_HOURS` (default 24) have passed:

```
$ python scripts/monthly_metrics.py --phase rest
Embargo holds: engineer pages were released 0.2h ago; the embargo is 24h.
23.8h remain before manager-facing pages may be written.
$ echo $?
3
```

The scheduled workflow runs `engineers` on the 1st and `rest` on the 2nd. Set
`EMBARGO_HOURS=0` to run both back to back — the *ordering* still holds, since
`rest` always fails if no engineer release is stamped.

---

## The correction loop

The one loop in the system runs from the engineer back into Layer 3. An
engineer reads their page, finds something the data could not see, and writes:

```bash
mkdir -p corrections/microsoft-vscode/2026-07
cat > corrections/microsoft-vscode/2026-07/octocat.json <<'JSON'
{"corrections": [
  "PR #481 was deliberately scoped down after an incident review — the small
   diff was the point, not a sign the work was small."
]}
JSON
```

On the next run that text is passed into Layer 3 as first-hand evidence about
work the data does not show. It changes the *interpretation* only — never the
counts, because the counts are what they are.

---

## Running it

### Locally, no model, no API key

```bash
export SOURCE_REPO=microsoft/vscode
export TARGET_MONTH=2026-07      # optional; defaults to last month
export GH_TOKEN=ghp_...          # optional, but avoids anonymous rate limits
export EMBARGO_HOURS=0           # optional; for a single-shot local run

python scripts/monthly_metrics.py --phase all
```

Layers 1, 2, the gate and Layer 4 need **no third-party dependencies and no
model**. You get every number, every audience page, and the interpretation
section marked "not generated".

### With interpretation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export INTERPRET=true
python scripts/monthly_metrics.py --phase all
```

Layer 3 runs `claude-opus-5` with adaptive thinking and a closed JSON schema,
twice per engineer so the gate has two runs to compare, and it uses server-side
refusal fallback so a declined request produces a page rather than a gap.

### When Layer 3 is unavailable

A rejected API request — bad key, no credits, unavailable model — does not
take the run with it. The deterministic report is written and committed, the
pages show the interpretation as *not generated*, and the run exits **5** so
CI still goes red:

```
::error::Layer 3 unavailable — request rejected: 400 ... credit balance is too low
  continuing with the deterministic layers; pages will show the
  interpretation as not generated.
Deterministic report written. Layer 3 did not run: ...
```

The cause is also recorded as `layer3_error` in that month's JSON. Layers 1, 2
and 4 carry every number, so losing them because a billing check failed would
be strictly worse than shipping them without an interpretation.

### Phases

| Phase | Runs | Writes |
|---|---|---|
| `collect` | Layers 1–2 | `data/` only |
| `engineers` | Layers 1–3, gate, Layer 4 (part) | engineer pages + manifest |
| `rest` | Layer 4 (part), from data on disk | EM, squad, founder pages |
| `all` | Everything | Everything (embargo still applies) |

`rest` re-reads `data/` rather than re-running collection, so the manager-facing
pages cost no API calls and no tokens.

---

## Configuration

| Variable | Default | Effect |
|---|---|---|
| `SOURCE_REPO` | `microsoft/vscode` | Repo to read from |
| `TARGET_MONTH` | previous month | `YYYY-MM` |
| `GH_TOKEN` | — | GitHub auth |
| `PHASE` | `all` | Same values as `--phase` |
| `DETAIL_BUDGET` | `400` | Per-PR API calls allowed (size, files, reviews) |
| `DETAIL_WORKERS` | `8` | Threads fanning out that per-PR fetch. `1` forces the old serial path |
| `NON_SUBSTANTIVE_TYPES` | `dependency,config,docs` | Which types the substantive count excludes |
| `INTERPRET` | `false` | Turn Layer 3 on |
| `INTERPRET_MODEL` | `claude-opus-5` | Model for Layer 3 |
| `INTERPRET_EFFORT` | `high` | `low`…`max` |
| `INTERPRET_RUNS` | `2` | Runs per engineer; the gate needs ≥2 to detect disagreement |
| `INTERPRET_ENGINEERS` | `12` | Cap on profiles interpreted per run |
| `EMBARGO_HOURS` | `24` | Hold on manager-facing pages |
| `SQUADS_PATH` | `config/squads.json` | Squad membership |
| `BOARD_PATH` / `DEPLOYS_PATH` / `INCIDENTS_PATH` | — | Optional off-GitHub feeds |

See [`config/README.md`](config/README.md) for the feed formats.

---

## What this cannot measure, and why that shows up as a blank

Three of the five sources in the architecture do not live in GitHub. Without
them, the metrics that depend on them report **insufficient evidence** — never
zero, and never a substitute quietly swapped in:

| Metric | Needs | Without it |
|---|---|---|
| Deployment frequency | A deploy feed | *insufficient evidence.* A merge is not a deploy. |
| Lead time for changes | A deploy feed | Falls back to open→merge, **and says so in the basis** |
| Change failure rate | An incident feed | *insufficient evidence*, or a revert-rate proxy labelled as a proxy |
| Time to restore | An incident feed | *insufficient evidence* |
| WIP | A board feed | Falls back to concurrently-open PRs, labelled as a proxy |

This is the point of the source row in the architecture. A dashboard that shows
`0` for change failure rate because nobody wired up PagerDuty is worse than one
that shows a blank, because the zero looks like good news.

---

## Reading the numbers

PR count measures throughput, not value. A months-long refactor lands as one PR
just as a typo fix does, and an engineer doing heavy review work authors fewer
PRs precisely because they are unblocking everyone else — which is why reviews
given is a first-class part of every profile rather than a footnote.

PRs created and PRs merged describe **different sets**: a PR created in June can
merge in July. Do not divide one by the other.

Rework rate is not a defect count. A changes-requested review is usually the
review process working.

And the individual profile is deliberately several numbers that do not add up
to one. There is no composite because a composite invites a ranking, and the
moment a ranking exists somebody will paste it into a promotion committee.

---

## Development

```bash
python -m unittest discover -s tests -v
```

134 tests covering the deterministic layers and the gate — the classifier's
priority rules, the DORA fallbacks, the anonymization boundary, every gate rule,
and the audience/embargo policy. Layer 3's contract is tested without a network
call (schema shape, prompt constraints, payload anonymization).

CI runs the suite before the pipeline on every run: layers 1, 2 and the gate are
code, so they are tested before they are trusted to produce anything a person
reads.

### Layout

```
metrics/
  classify.py      Layer 1  filename rules
  collect.py       Layer 1  source fan-in
  sources/         Layer 1  one adapter per source box
  compute.py       Layer 2  DORA, flow, individual profiles
  anonymize.py     the layer 2 → 3 arrow
  interpret.py     Layer 3  the only model call
  guardrails.py    the gate
  distribute.py    Layer 4  audience policy + embargo
  corrections.py   the 1:1 loop
  pipeline.py      orchestration
scripts/
  monthly_metrics.py       entry point
  migrate_v1_artifacts.py  one-off: retire the old ranked artifacts
```

### A worked example

`reports/balajilandge-Engineering-Metrics/2026-08/` holds a real run of the
pipeline against this repository — all four audience pages, generated with
Layer 3 off. It is the quickest way to see what each audience actually
receives, including a founder page where three of the four DORA metrics read
*insufficient evidence* because this repo has no deploy or incident feed.

### History

This repo previously generated a ranked per-engineer leaderboard. That is the
artifact this architecture exists to prevent, so
`scripts/migrate_v1_artifacts.py` retired it: historical `data/` files were
migrated to schema 2 with every count preserved and 1,045 `rank` fields
removed, and the rendered ranked reports were deleted. Those months predate PR
classification and carry no type split — see `schema_v1_import` in the JSON.
