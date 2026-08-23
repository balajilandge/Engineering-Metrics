#!/usr/bin/env python3
"""
One-off migration: retire the ranked-leaderboard artifacts from the previous
architecture.

The old pipeline committed a ranked list of engineers to `data/` and rendered
it into `reports/`. The new architecture does not generate one — so leaving the
old ones in the repository would leave exactly the artifact the design exists
to prevent, still readable by anyone with repo access.

This script:

  * rewrites each `data/<slug>/<YYYY-MM>.json` to schema 2 — dropping the
    `rank` field and renaming `leaderboard` to `individuals`, while keeping
    every count the old run measured;
  * deletes the rendered ranked reports under `reports/<slug>/`;
  * writes `reports/<slug>/README.md` explaining where the reports went.

Historical months keep a `schema_v1_import` marker: they were collected before
PR classification existed, so they carry no type split, and nothing downstream
should pretend otherwise.

    python scripts/migrate_v1_artifacts.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

DATA_ROOT = "data"
REPORTS_ROOT = "reports"

NOTICE = """\
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
"""


def migrate_data_file(path: str, dry_run: bool) -> tuple[int, int]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)

    rows = payload.pop("leaderboard", None)
    if rows is None:
        return 0, 0

    ranks_removed = sum(1 for row in rows if "rank" in row)
    individuals = []
    for row in rows:
        row.pop("rank", None)
        individuals.append({
            "engineer": row.get("engineer", ""),
            "profile_url": row.get("profile_url", ""),
            "throughput": {
                "prs_created": row.get("prs_created", 0),
                "prs_merged": row.get("prs_merged", 0),
                # Unknowable for schema-1 months: classification did not exist.
                "prs_merged_substantive": None,
                "by_type": None,
            },
        })

    # Alphabetical, so the file itself no longer encodes an ordering.
    individuals.sort(key=lambda item: item["engineer"].lower())

    payload["schema_version"] = 2
    payload["schema_v1_import"] = (
        "Collected by the ranked-leaderboard pipeline before PR classification "
        "existed. Counts are as measured; rank has been removed and no type "
        "split is available for this month."
    )
    payload["individuals"] = individuals

    if not dry_run:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    return len(individuals), ranks_removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change, write nothing")
    args = parser.parse_args(argv)

    verb = "would migrate" if args.dry_run else "migrated"
    total_rows = total_ranks = 0

    for slug in sorted(os.listdir(DATA_ROOT)) if os.path.isdir(DATA_ROOT) else []:
        directory = os.path.join(DATA_ROOT, slug)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json") or ".collect." in name:
                continue
            rows, ranks = migrate_data_file(os.path.join(directory, name), args.dry_run)
            if rows:
                print(f"  {verb} {slug}/{name}: {rows} engineers, {ranks} ranks removed")
                total_rows += rows
                total_ranks += ranks

    removed = []
    for slug in sorted(os.listdir(REPORTS_ROOT)) if os.path.isdir(REPORTS_ROOT) else []:
        directory = os.path.join(REPORTS_ROOT, slug)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            path = os.path.join(directory, name)
            # Old layout: flat <YYYY-MM>.md and latest.md. New layout is a
            # month *directory*, which must survive.
            if os.path.isfile(path) and name.endswith(".md") and name != "README.md":
                removed.append(path)
                if not args.dry_run:
                    os.remove(path)

        if not args.dry_run:
            with open(os.path.join(directory, "README.md"), "w", encoding="utf-8") as handle:
                handle.write(NOTICE)

    for path in removed:
        print(f"  {'would remove' if args.dry_run else 'removed'} {path}")

    print(f"\n{total_rows} engineer rows {verb}, {total_ranks} rank fields removed, "
          f"{len(removed)} ranked report(s) {'would be ' if args.dry_run else ''}deleted")
    if args.dry_run:
        print("Dry run — nothing written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
