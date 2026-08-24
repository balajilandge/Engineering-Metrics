#!/usr/bin/env python3
"""
Monthly engineering metrics — four-layer pipeline.

    SOURCES   pull requests · reviews given · board/Linear · CI & deploys · incidents
      |
    [1] collect     deterministic, no model — facts and PR classification
    [2] compute     deterministic, no model — team DORA + individual profiles
      |             names stripped -> Engineer A, B, C
    [3] interpret   THE ONLY PLACE A MODEL RUNS — diffs and review comments
      |             JSON, every claim carrying an evidence field
    gate            no citation -> dropped · runs disagree -> flagged, never
      |             averaged · no rating, no rank
    [4] distribute  each engineer FIRST · EM · squad leads · founder
                    a ranked list is never generated, so it cannot leak

Layers 1, 2 and the gate are code. Layer 3 is the model. Layer 4 is policy.

Usage:
    python scripts/monthly_metrics.py [--phase collect|engineers|rest|all]

Configuration is environment variables; see README.md.
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.config import Config, env  # noqa: E402
from metrics.distribute import EmbargoError  # noqa: E402
from metrics.pipeline import run  # noqa: E402

PHASES = ("collect", "engineers", "rest", "all")


def previous_month(today: datetime.date) -> str:
    last_of_prev = today.replace(day=1) - datetime.timedelta(days=1)
    return last_of_prev.strftime("%Y-%m")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--phase", choices=PHASES, default=env("PHASE", "all"),
        help="collect: layers 1-2 only. engineers: through the gate, then "
             "engineer pages. rest: manager-facing pages (embargoed). "
             "all: everything.",
    )
    parser.add_argument("--repo", default=env("SOURCE_REPO", "openai/codex"))
    parser.add_argument("--month", default=env("TARGET_MONTH"),
                        help="YYYY-MM (default: previous calendar month, UTC)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    month = args.month or previous_month(
        datetime.datetime.now(datetime.timezone.utc).date())

    config = Config.from_env(repo=args.repo, month=month)

    print(f"=== {config.repo} · {config.month} · phase={args.phase} ===")
    if not config.interpret:
        print("Layer 3 is off (INTERPRET=false). Layers 1, 2, the gate and "
              "Layer 4 run with no model and no API key.")

    try:
        payload = run(config, phase=args.phase)
    except EmbargoError as exc:
        # Not a crash: the embargo did its job.
        print(f"\nEmbargo holds: {exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 4

    if payload and payload.get("layer3_error"):
        # The deterministic report is written and worth committing, but the
        # run asked for interpretation and did not get it — so the run fails.
        print(f"\nDeterministic report written. Layer 3 did not run: "
              f"{payload['layer3_error']}", file=sys.stderr)
        return 5

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
