"""
The 1:1 correction loop — the only loop in the architecture.

An engineer reads their own page, finds something the data got wrong or could
not see, and writes it down. On the next run that text is passed back into
Layer 3 as first-hand evidence. It does not flow into Layers 1 or 2: a
correction changes the *interpretation*, never the counts, because the counts
are what they are.

    corrections/<repo-slug>/<YYYY-MM>/<login>.json
    {"corrections": ["...", "..."]}
"""
from __future__ import annotations

import json
import os


def corrections_dir(repo: str, month: str) -> str:
    return os.path.join("corrections", repo.replace("/", "-"), month)


def load_corrections(repo: str, month: str, mapping: dict[str, str]) -> dict[str, list[str]]:
    """Returns {anonymized_label: [text, ...]} so Layer 3 stays name-blind."""
    directory = corrections_dir(repo, month)
    if not os.path.isdir(directory):
        return {}

    found: dict[str, list[str]] = {}
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".json"):
            continue
        login = filename[:-len(".json")]
        label = mapping.get(login)
        if label is None:
            continue
        try:
            with open(os.path.join(directory, filename), encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue

        items = payload.get("corrections") if isinstance(payload, dict) else payload
        if isinstance(items, str):
            items = [items]
        if isinstance(items, list) and items:
            found[label] = [str(item) for item in items]

    if found:
        print(f"  corrections loaded for {len(found)} engineer(s)")
    return found
