"""
The orchestrator: runs the layers in order and writes what each one produced.

    sources -> [1] collect -> [2] compute -> strip names -> [3] interpret
             -> gate -> [4] distribute

Each layer's output is written to `data/` so a later phase (or a human) can
inspect exactly what a layer produced, without re-running the layer above it.
Layer 3 is the only step that costs money and the only one that needs network
access beyond GitHub, so the phases are separable on purpose.
"""
from __future__ import annotations

import datetime
import json
import os
import sys

from . import SCHEMA_VERSION
from .anonymize import anonymize_diff, anonymize_profile, build_mapping
from .collect import collect
from .compute import compute
from .corrections import load_corrections
from .distribute import (distribute_engineers, distribute_rest, load_squads)
from .guardrails import gate_all
from .interpret import interpret
from .sources import github as github_source


def repo_slug(repo: str) -> str:
    return repo.replace("/", "-")


def data_dir(repo: str) -> str:
    return os.path.join("data", repo_slug(repo))


def reports_root(repo: str, month: str) -> str:
    return os.path.join("reports", repo_slug(repo), month)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"  wrote {path}")


def fetch_evidence(config, collection, profiles, mapping) -> tuple[dict, dict]:
    """
    Pulls the diffs and review comments Layer 3 reads, anonymized on the way
    out. Only for the engineers that will actually be interpreted — this is
    the expensive part of the run.
    """
    if not config.interpret:
        return {}, {}

    client = github_source.GitHubClient(config.token, config.max_pages)
    by_number = {p.number: p for p in collection.all_pulls}

    diffs: dict[str, dict[int, str]] = {}
    comments: dict[str, dict[int, list[str]]] = {}

    for profile in profiles[:config.interpret_engineers]:
        label = mapping[profile["engineer"]]
        diffs[label], comments[label] = {}, {}

        for item in profile["evidence_prs"][:8]:
            number = item["number"]
            pull = by_number.get(number)
            if pull is None:
                continue
            try:
                files = client.pull_files(config.repo, number)
                patch = "\n".join(
                    f"--- {f.get('filename')}\n{f.get('patch', '')}"
                    for f in files if f.get("patch")
                )
                diffs[label][number] = anonymize_diff(patch, mapping)

                raw_comments = client.pull_review_comments(config.repo, number)
                comments[label][number] = [
                    anonymize_diff(c.get("body", ""), mapping)
                    for c in raw_comments
                    if not github_source.is_bot(c.get("user")) and c.get("body")
                ][:20]
            except Exception as exc:  # noqa: BLE001
                print(f"  warning: evidence fetch failed for #{number}: "
                      f"{type(exc).__name__}: {exc}", file=sys.stderr)

    print(f"  evidence fetched for {len(diffs)} engineers "
          f"({client.calls} API calls)")
    return diffs, comments


def run(config, phase: str = "all") -> dict:
    """
    phase:
      collect    layers 1-2 only, write data, no pages
      engineers  layers 1-3 + gate, then engineer pages only
      rest       manager/squad/founder pages from data already on disk
      all        every phase in one go (embargo still applies unless it is 0)
    """
    root = reports_root(config.repo, config.month)
    ddir = data_dir(config.repo)

    if phase == "rest":
        return _run_rest_from_disk(config, root, ddir)

    # ---- Layer 1 ---------------------------------------------------------
    collection = collect(config)
    _write_json(os.path.join(ddir, f"{config.month}.collect.json"),
                collection.to_dict())

    # ---- Layer 2 ---------------------------------------------------------
    print("Layer 2 compute: deterministic team and individual metrics")
    computed = compute(collection, config.non_substantive)
    print(f"  {len(computed['individuals'])} individual profiles, "
          f"no score and no rank among them")

    mapping = build_mapping(
        [p["engineer"] for p in computed["individuals"]],
        salt=f"{config.repo}:{config.month}",
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "repo": config.repo,
        "month": config.month,
        "period": {"start": collection.start_iso, "end": collection.end_iso},
        "generated_at": _now_iso(),
        "sources": [s.to_dict() for s in collection.statuses],
        "non_substantive_types": list(config.non_substantive),
        "team": computed["team"],
        "individuals": computed["individuals"],
    }
    _write_json(os.path.join(ddir, f"{config.month}.json"), payload)

    if phase == "collect":
        print("phase=collect: stopping before interpretation")
        return payload

    # ---- Layer 3 (the only model call) -----------------------------------
    anonymized = [anonymize_profile(p, mapping) for p in computed["individuals"]]
    corrections = load_corrections(config.repo, config.month, mapping)
    diffs, comments = fetch_evidence(config, collection, computed["individuals"], mapping)

    interpretations = interpret(anonymized, mapping, diffs, comments, corrections, config)

    # ---- Gate ------------------------------------------------------------
    valid_prs = {
        mapping[p["engineer"]]: {item["number"] for item in p["evidence_prs"]}
        for p in computed["individuals"]
    }
    gated = gate_all(interpretations, valid_prs)
    if gated:
        dropped = sum(len(g.dropped_claims) for g in gated.values())
        contested = sum(1 for g in gated.values() if g.contested)
        print(f"Guardrail gate: {dropped} uncited claim(s) dropped, "
              f"{contested} engineer(s) with contested runs")
        _write_json(
            os.path.join(ddir, f"{config.month}.interpretation.json"),
            {
                "schema_version": SCHEMA_VERSION,
                "repo": config.repo,
                "month": config.month,
                "generated_at": _now_iso(),
                "model": config.model,
                "runs_per_engineer": config.interpret_runs,
                # Anonymized labels only: this file never carries a name.
                "gated": {label: result.to_dict() for label, result in gated.items()},
            },
        )

    # ---- Layer 4 ---------------------------------------------------------
    distribute_engineers(root, computed, gated, mapping, config.repo,
                         config.month, config.non_substantive)
    _write_json(os.path.join(ddir, f"{config.month}.mapping.json"), {
        "note": "engineer -> anonymized label, for re-attaching names after "
                "Layer 3. Never sent to the model.",
        "month": config.month,
        "mapping": mapping,
    })

    if phase == "engineers":
        print("phase=engineers: manager-facing pages held until the embargo "
              "expires. Run phase=rest next.")
        return payload

    distribute_rest(root, computed, gated, mapping, config.repo, config.month,
                    [s.to_dict() for s in collection.statuses],
                    load_squads(config.squads_path), config.non_substantive,
                    config.embargo_hours)
    return payload


def _run_rest_from_disk(config, root: str, ddir: str) -> dict:
    """Phase 2 without re-running collection or paying for interpretation."""
    from .guardrails import GateResult

    computed_path = os.path.join(ddir, f"{config.month}.json")
    if not os.path.exists(computed_path):
        raise FileNotFoundError(
            f"{computed_path} not found — run the `engineers` phase first.")

    with open(computed_path, encoding="utf-8") as handle:
        payload = json.load(handle)

    mapping_path = os.path.join(ddir, f"{config.month}.mapping.json")
    mapping = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, encoding="utf-8") as handle:
            mapping = json.load(handle).get("mapping", {})

    gated: dict[str, GateResult] = {}
    interp_path = os.path.join(ddir, f"{config.month}.interpretation.json")
    if os.path.exists(interp_path):
        with open(interp_path, encoding="utf-8") as handle:
            stored = json.load(handle).get("gated", {})
        for label, entry in stored.items():
            audit = entry.get("audit", {})
            gated[label] = GateResult(
                engineer=label,
                interpretation=entry.get("interpretation", {}),
                dropped_claims=audit.get("dropped_claims", []),
                disagreements=audit.get("disagreements", []),
                stripped_keys=audit.get("stripped_keys", []),
                rating_prose=audit.get("rating_prose_removed", []),
                runs_compared=audit.get("runs_compared", 0),
            )

    computed = {"team": payload["team"], "individuals": payload["individuals"]}
    distribute_rest(root, computed, gated, mapping, config.repo, config.month,
                    payload.get("sources", []), load_squads(config.squads_path),
                    tuple(payload.get("non_substantive_types", ())),
                    config.embargo_hours)
    return payload
