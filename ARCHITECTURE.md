# Code Architecture

This document maps the codebase to the four-layer pipeline described in the
[README](README.md), including how the GitHub Actions workflows drive it.
Diagrams are Mermaid and render natively on GitHub. A print-friendly PDF of
the same three diagrams is at [`docs/architecture-diagrams.pdf`](docs/architecture-diagrams.pdf).

---

## 1. System overview

```mermaid
flowchart TB
    subgraph SRC["Sources (metrics/sources/)"]
        direction LR
        GH["github.py\npull requests · reviews"]
        BOARD["board.py\nboard/Linear feed (optional)"]
        DEPLOY["deploys.py\ndeploy feed (optional)"]
        INC["incidents.py\nincident feed (optional)"]
    end

    subgraph L1["[1] COLLECT — collect.py, classify.py — deterministic, no model"]
        C1["fan in all sources\nclassify every PR by filename rule:\ndependency · config · docs · test · fix · feature"]
    end

    subgraph L2["[2] COMPUTE — compute.py — deterministic, no model"]
        C2["team: DORA · review latency · WIP · carryover\nindividual: throughput by type · reviews · rework\n(cohort filter applied here — select_engineer_cohort)"]
    end

    ANON["anonymize.py\nnames stripped → Engineer A, B, C"]

    subgraph L3["[3] INTERPRET — interpret.py — THE ONLY MODEL CALL"]
        C3["claude-opus-5, 2 runs/engineer\nreads diffs + review comments (fetch_evidence)\nreturns JSON, every claim cites evidence"]
    end

    subgraph GATE["GUARDRAIL GATE — guardrails.py"]
        G1["no citation → claim dropped\nruns disagree → flagged, never averaged\nassert_no_scores / assert_no_ranked_list"]
    end

    subgraph L4["[4] DISTRIBUTE — distribute.py — policy"]
        D1["engineer pages — FIRST\nEM page — 1:1 agenda\nsquad pages\nfounder page\n(ranked list: never generated)"]
    end

    CORR["corrections.py\n1:1 correction loop"]

    SRC --> L1 --> L2 --> ANON --> L3 --> GATE --> L4
    D1 -. "engineer reads page, files a correction" .-> CORR
    CORR -. "next run: fed into Layer 3 as evidence" .-> L3

    classDef code fill:#e8f4ea,stroke:#4a8a5a,color:#1a1a1a;
    classDef model fill:#fde8d8,stroke:#c9701f,color:#1a1a1a;
    classDef gate fill:#f4e8fc,stroke:#8a4ac9,color:#1a1a1a;
    class L1,L2,L4,CORR code;
    class L3 model;
    class GATE gate;
```

**Layers 1, 2 and the gate are code. Layer 3 is the model. Layer 4 is policy.**

---

## 2. Module map

```mermaid
flowchart LR
    entry["scripts/monthly_metrics.py\nCLI entry point"]
    cfg["metrics/config.py\nConfig.from_env()"]
    pipe["metrics/pipeline.py\nrun(config, phase)"]

    entry --> cfg
    entry --> pipe
    cfg --> pipe

    pipe --> collect["metrics/collect.py"]
    pipe --> classify["metrics/classify.py"]
    pipe --> compute["metrics/compute.py"]
    pipe --> anonymize["metrics/anonymize.py"]
    pipe --> corrections["metrics/corrections.py"]
    pipe --> interpret["metrics/interpret.py"]
    pipe --> guardrails["metrics/guardrails.py"]
    pipe --> distribute["metrics/distribute.py"]

    collect --> classify
    collect --> sbase["metrics/sources/base.py"]
    sbase --> sgh["sources/github.py"]
    sbase --> sboard["sources/board.py"]
    sbase --> sdeploy["sources/deploys.py"]
    sbase --> sinc["sources/incidents.py"]

    interpret --> sgh
    interpret --> anonymize

    distribute --> squads["config/squads.json\n(via distribute.load_squads)"]

    pipe -->|"writes"| data["data/&lt;repo&gt;/&lt;month&gt;.*.json\ncollect · compute · interpretation · mapping"]
    distribute -->|"writes"| reports["reports/&lt;repo&gt;/&lt;month&gt;/\nengineers/ · em.md · squads/ · founder.md\n+ release-manifest.json"]
```

| Module | Layer | Responsibility |
|---|---|---|
| `metrics/sources/base.py`, `github.py`, `board.py`, `deploys.py`, `incidents.py` | Sources | One adapter per source box; missing feeds report "insufficient evidence", never a silent zero |
| `metrics/classify.py` | 1 | Filename-rule PR classification (dependency/config/docs/test/fix/feature) |
| `metrics/collect.py` | 1 | Fans sources in, threads the per-PR detail fetch (`DETAIL_WORKERS`) |
| `metrics/compute.py` | 2 | Deterministic DORA/flow/individual metrics; `select_engineer_cohort` for `REPORT_ENGINEERS` |
| `metrics/anonymize.py` | 2→3 | Strips names to `Engineer A, B, C`; builds/uses the reversible mapping |
| `metrics/corrections.py` | loop | Reads `corrections/<repo>/<month>/<login>.json` back into Layer 3 |
| `metrics/interpret.py` | 3 | The only model call — schema-constrained JSON, 2 runs/engineer |
| `metrics/guardrails.py` | gate | Drops uncited claims, flags disagreement, asserts no scores/ranking |
| `metrics/distribute.py` | 4 | Per-audience page rendering + embargo (`EmbargoError`) |
| `metrics/config.py` | — | `Config` dataclass, environment-variable parsing (`env`, `env_int`, `env_bool`, `env_list`) |
| `metrics/pipeline.py` | — | Orchestrator: `run(config, phase)`, `fetch_evidence`, disk-only `rest` phase |
| `scripts/monthly_metrics.py` | — | CLI entry point; maps exit codes (`0` ok, `3` embargo, `4` missing data, `5` Layer 3 failed) |
| `scripts/migrate_v1_artifacts.py` | — | One-off: strips legacy `rank` fields from historical `data/` |

---

## 3. GitHub Actions

Two workflows in `.github/workflows/`, split deliberately: the scheduled
metrics run never executes tests (it's a demo/production job producing
reports), and `tests.yml` exists specifically to cover the deterministic
layers and the gate before a PR merges.

```mermaid
flowchart TB
    subgraph EVT1["Triggers"]
        pr["pull_request"]
        push["push → main"]
    end
    subgraph WF1["Tests (tests.yml)"]
        direction TB
        t1["checkout"] --> t2["setup-python 3.12"] --> t3["python -m unittest discover -s tests"]
    end
    pr --> WF1
    push --> WF1

    subgraph EVT2["Triggers"]
        cron1["schedule: 0 3 1 * *\nphase=engineers"]
        cron2["schedule: 0 3 2 * *\nphase=rest"]
        disp["workflow_dispatch\nphase / month / source_repo /\ninterpret / engineers"]
    end
    subgraph WF2["Monthly Engineering Metrics (monthly-metrics.yml)"]
        direction TB
        m1["checkout"] --> m2["setup-python 3.12"] --> m3["resolve phase\n(dispatch input, else cron→engineers/rest)"]
        m3 --> m4{"inputs.interpret?"}
        m4 -- yes --> m5["pip install -r requirements.txt"]
        m4 -- no --> m6
        m5 --> m6["python scripts/monthly_metrics.py --phase &lt;phase&gt;\nenv: GH_TOKEN, ANTHROPIC_API_KEY, TARGET_MONTH,\nSOURCE_REPO, INTERPRET, BOARD/DEPLOYS/INCIDENTS_PATH,\nEMBARGO_HOURS, DETAIL_BUDGET, DETAIL_WORKERS,\nREPORT_ENGINEERS, REPORT_ENGINEER_SELECT"]
        m6 --> m7["commit data/ + reports/\n(if !cancelled — runs even on Layer 3 failure)\npush with fetch+rebase retry ×5"]
    end
    cron1 --> WF2
    cron2 --> WF2
    disp --> WF2

    m6 -.->|"invokes"| pipe["metrics.pipeline.run()"]
```

### Workflow reference

| Workflow | File | Triggers | Permissions | Concurrency |
|---|---|---|---|---|
| Tests | `.github/workflows/tests.yml` | `pull_request`, `push` to `main` | `contents: read` | cancels in-progress per ref |
| Monthly Engineering Metrics | `.github/workflows/monthly-metrics.yml` | `schedule` (1st & 2nd of month, 03:00 UTC), `workflow_dispatch` | `contents: write` (commits reports) | queued, never cancelled (`monthly-metrics` group) |

### `monthly-metrics.yml` phase resolution

| Firing | Resolved phase | Effect |
|---|---|---|
| Cron `0 3 1 * *` | `engineers` | Layers 1–3 + gate + engineer pages; stamps `release-manifest.json` |
| Cron `0 3 2 * *` | `rest` | Reads `data/` from disk, writes EM/squad/founder pages — **fails if the 24h embargo hasn't elapsed** |
| `workflow_dispatch` with `phase` input | that input | Manual override of the above, plus `collect`/`all` |

This cron split *is* the "engineer FIRST" guarantee from the README, enforced
by `metrics/distribute.py`'s `EmbargoError` (exit code `3`) rather than by
convention — running `rest` early fails the job.

### Secrets, variables and how they map to `Config`

The workflow's `env:` block is the only place outside `metrics/config.py`
that names these variables; `Config.from_env()` (`metrics/config.py:72`) is
what actually consumes them at runtime.

| Workflow source | Env var | `Config` field |
|---|---|---|
| `secrets.GITHUB_TOKEN` | `GH_TOKEN` | `token` |
| `secrets.ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY` | read directly by `metrics/interpret.py` |
| `inputs.month` | `TARGET_MONTH` | `month` (CLI `--month`) |
| `inputs.source_repo` | `SOURCE_REPO` | `repo` (CLI `--repo`) |
| `inputs.interpret` | `INTERPRET` | `interpret` |
| `vars.BOARD_PATH` / `DEPLOYS_PATH` / `INCIDENTS_PATH` | same | `board_path` / `deploys_path` / `incidents_path` |
| `vars.EMBARGO_HOURS` (default `24`) | `EMBARGO_HOURS` | `embargo_hours` |
| `vars.DETAIL_BUDGET` | `DETAIL_BUDGET` | `detail_budget` |
| `vars.DETAIL_WORKERS` (default `8`) | `DETAIL_WORKERS` | `detail_workers` |
| `inputs.engineers` or `vars.REPORT_ENGINEERS` | `REPORT_ENGINEERS` | `report_engineers` |
| `vars.REPORT_ENGINEER_SELECT` (default `activity`) | `REPORT_ENGINEER_SELECT` | `report_engineer_select` |

### Exit codes surfaced by the workflow

`scripts/monthly_metrics.py` turns pipeline outcomes into process exit codes,
which is what makes the "commit and push" step's `if: ${{ !cancelled() }}`
meaningful — it runs even when the pipeline step goes red:

| Exit | Meaning | Commit-and-push step still runs? |
|---|---|---|
| `0` | Full success | yes |
| `3` | Embargo not yet elapsed (`rest` too early) | yes (nothing new to commit) |
| `4` | `rest` run with no `engineers` data on disk | yes |
| `5` | Deterministic layers wrote a report, but Layer 3 failed | yes — deterministic report is committed, job still shows red |

---

## 4. Directory layout

```
metrics/            pipeline package (see module map above)
scripts/            CLI entry points
config/             squads.json + feed format docs
data/<repo>/         layer 1/2/3 JSON artifacts, one file per stage per month
reports/<repo>/<month>/   rendered audience pages (engineers/, em.md, squads/, founder.md)
tests/               unit tests for the deterministic layers + the gate
.github/workflows/   tests.yml, monthly-metrics.yml
```
