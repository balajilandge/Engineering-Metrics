"""
The guardrail gate. Code, not model — it runs on Layer 3's output before any
of it reaches a human.

Three rules, in order:

  1. **No citation -> claim dropped.** A claim whose evidence is missing,
     empty, or points at a PR the engineer did not author is deleted. Not
     flagged for review, not softened — deleted. The dropped claims are kept
     in an audit list so the deletion itself is inspectable.

  2. **Two runs disagree -> flagged, never averaged.** The runs are compared
     claim by claim. Anything present in one run and absent from the other is
     surfaced as a disagreement for a human to resolve. Nothing is merged,
     averaged, or resolved by majority: a claim two runs cannot agree on is
     exactly the claim a manager needs to see is contested.

  3. **No rating, no rank.** Any score-like key that appears anywhere in the
     payload is stripped, and the pipeline refuses to proceed if a rank-shaped
     structure (an ordered list of engineers) is present.

Rule 2 is why `interpret_runs` defaults to 2. With one run there is nothing to
compare, and the gate says so rather than pretending the single run is agreed.
"""
from __future__ import annotations

import dataclasses
import difflib
import re

CLAIM_LISTS = ("complexity", "blockers", "unblocking_others")
NARRATIVE_FIELDS = ("summary", "most_favourable_reading", "least_favourable_reading")

FORBIDDEN_KEYS = frozenset({
    "score", "rating", "rank", "ranking", "grade", "percentile", "stars",
    "performance_score", "overall", "tier",
})

# Phrases that smuggle a rating back in as prose.
_RATING_PROSE = re.compile(
    r"\b(top|bottom)\s+(performer|quartile|decile|\d+\s*%)"
    r"|\b(above|below)\s+average\b"
    r"|\brank(?:s|ed|ing)?\s+(?:#?\d+|first|second|third|last)\b"
    r"|\b(?:out|one)\s+of\s+the\s+(?:best|worst)\b"
    r"|\b(?:strong|weak|poor|excellent|outstanding)\s+performer\b",
    re.IGNORECASE,
)

# How similar two claims must be to count as "the same claim".
AGREEMENT_THRESHOLD = 0.72


@dataclasses.dataclass
class GateResult:
    engineer: str
    interpretation: dict
    dropped_claims: list[dict] = dataclasses.field(default_factory=list)
    disagreements: list[dict] = dataclasses.field(default_factory=list)
    stripped_keys: list[str] = dataclasses.field(default_factory=list)
    rating_prose: list[str] = dataclasses.field(default_factory=list)
    runs_compared: int = 0

    @property
    def contested(self) -> bool:
        return bool(self.disagreements)

    def to_dict(self) -> dict:
        return {
            "engineer": self.engineer,
            "interpretation": self.interpretation,
            "audit": {
                "runs_compared": self.runs_compared,
                "dropped_claims": self.dropped_claims,
                "disagreements": self.disagreements,
                "stripped_keys": self.stripped_keys,
                "rating_prose_removed": self.rating_prose,
            },
        }


# --------------------------------------------------------------------------
# Rule 1 — no citation, no claim
# --------------------------------------------------------------------------

def _citation_valid(claim: dict, valid_prs: set[int]) -> tuple[bool, str]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        return False, "no evidence object"
    quote = (evidence.get("quote") or "").strip()
    if not quote:
        return False, "evidence carries no quote"
    pr = evidence.get("pr")
    if not isinstance(pr, int):
        return False, "evidence cites no PR number"
    if valid_prs and pr not in valid_prs:
        return False, f"cites PR #{pr}, which is not in this engineer's evidence set"
    return True, ""


def drop_uncited(run: dict, valid_prs: set[int]) -> tuple[dict, list[dict]]:
    cleaned = dict(run)
    dropped: list[dict] = []
    for field in CLAIM_LISTS:
        kept = []
        for claim in run.get(field) or []:
            ok, reason = _citation_valid(claim, valid_prs)
            if ok:
                kept.append(claim)
            else:
                dropped.append({
                    "field": field,
                    "claim": claim.get("claim", "") if isinstance(claim, dict) else str(claim),
                    "reason": reason,
                })
        cleaned[field] = kept
    return cleaned, dropped


# --------------------------------------------------------------------------
# Rule 2 — disagreement is flagged, never averaged
# --------------------------------------------------------------------------

def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _match_claims(left: list[dict], right: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Returns (agreed, only_in_left, only_in_right)."""
    agreed, unmatched_right = [], list(right)
    only_left = []
    for claim in left:
        text = claim.get("claim", "")
        best, best_score = None, 0.0
        for candidate in unmatched_right:
            score = _similar(text, candidate.get("claim", ""))
            if score > best_score:
                best, best_score = candidate, score
        if best is not None and best_score >= AGREEMENT_THRESHOLD:
            unmatched_right.remove(best)
            agreed.append(claim)
        else:
            only_left.append(claim)
    return agreed, only_left, unmatched_right


def compare_runs(runs: list[dict]) -> tuple[dict, list[dict]]:
    """
    Returns (agreed_interpretation, disagreements).

    Only claims both runs made survive into the interpretation. Claims from a
    single run are not averaged in at half weight and not silently dropped —
    they are listed as contested, with which run said what.
    """
    if not runs:
        return {}, []
    if len(runs) == 1:
        return dict(runs[0]), [{
            "field": "*",
            "kind": "unverified",
            "detail": "only one interpretation run completed; "
                      "nothing to compare it against",
        }]

    base, other = runs[0], runs[1]
    agreed = dict(base)
    disagreements: list[dict] = []

    for field in CLAIM_LISTS:
        both, only_a, only_b = _match_claims(base.get(field) or [], other.get(field) or [])
        agreed[field] = both
        for claim in only_a:
            disagreements.append({"field": field, "kind": "only_in_run_1",
                                  "claim": claim.get("claim", "")})
        for claim in only_b:
            disagreements.append({"field": field, "kind": "only_in_run_2",
                                  "claim": claim.get("claim", "")})

    for field in NARRATIVE_FIELDS:
        a, b = base.get(field, ""), other.get(field, "")
        if a and b and _similar(a, b) < AGREEMENT_THRESHOLD:
            disagreements.append({
                "field": field, "kind": "narratives_differ",
                "run_1": a, "run_2": b,
            })

    # The union is right for gaps: if either run says the evidence cannot
    # answer something, that doubt stands.
    merged_gaps = list(base.get("insufficient_evidence") or [])
    for gap in other.get("insufficient_evidence") or []:
        if not any(_similar(gap, existing) >= AGREEMENT_THRESHOLD for existing in merged_gaps):
            merged_gaps.append(gap)
    agreed["insufficient_evidence"] = merged_gaps

    return agreed, disagreements


# --------------------------------------------------------------------------
# Rule 3 — no rating, no rank
# --------------------------------------------------------------------------

def strip_ratings(node, path="$") -> tuple[object, list[str]]:
    stripped: list[str] = []
    if isinstance(node, dict):
        clean = {}
        for key, value in node.items():
            if key.lower() in FORBIDDEN_KEYS:
                stripped.append(f"{path}.{key}")
                continue
            child, child_stripped = strip_ratings(value, f"{path}.{key}")
            clean[key] = child
            stripped.extend(child_stripped)
        return clean, stripped
    if isinstance(node, list):
        clean_list = []
        for i, item in enumerate(node):
            child, child_stripped = strip_ratings(item, f"{path}[{i}]")
            clean_list.append(child)
            stripped.extend(child_stripped)
        return clean_list, stripped
    return node, stripped


def scrub_rating_prose(run: dict) -> tuple[dict, list[str]]:
    """A rating written as a sentence is still a rating."""
    cleaned = dict(run)
    removed: list[str] = []
    for field in NARRATIVE_FIELDS:
        text = cleaned.get(field)
        if isinstance(text, str) and _RATING_PROSE.search(text):
            removed.append(f"{field}: {_RATING_PROSE.search(text).group(0)}")
            cleaned[field] = _RATING_PROSE.sub("[comparative claim removed]", text)
    return cleaned, removed


def assert_no_ranked_list(payload) -> None:
    """
    Refuses any structure that is a ranked list of people in disguise: a list
    of engineer records carrying an ordinal.
    """
    def walk(node, path="$"):
        if isinstance(node, list) and len(node) > 1:
            entries = [n for n in node if isinstance(n, dict)]
            if len(entries) == len(node) and entries:
                keys = set().union(*(set(e.keys()) for e in entries))
                if {"engineer"} & keys and keys & {"rank", "position", "place", "index"}:
                    raise ValueError(
                        f"refusing to emit a ranked list of engineers at {path}. "
                        "The architecture does not generate one, so it cannot leak.")
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(payload)


# --------------------------------------------------------------------------

def gate(label: str, runs: list[dict], valid_prs: set[int]) -> GateResult:
    """Runs all three rules over one engineer's interpretation runs."""
    cleaned_runs: list[dict] = []
    dropped: list[dict] = []
    stripped_keys: list[str] = []
    rating_prose: list[str] = []

    for index, run in enumerate(runs, start=1):
        cleaned, run_dropped = drop_uncited(run, valid_prs)
        cleaned, run_prose = scrub_rating_prose(cleaned)
        cleaned, run_keys = strip_ratings(cleaned, f"run_{index}")
        cleaned_runs.append(cleaned)
        dropped.extend(run_dropped)
        stripped_keys.extend(run_keys)
        rating_prose.extend(f"run {index} {item}" for item in run_prose)

    agreed, disagreements = compare_runs(cleaned_runs)

    # The comparison output is rebuilt from already-scrubbed runs, but re-run
    # the rules on it so nothing reintroduced by the merge escapes the gate.
    agreed, merge_keys = strip_ratings(agreed, "agreed")
    agreed, merge_prose = scrub_rating_prose(agreed)
    stripped_keys.extend(merge_keys)
    rating_prose.extend(merge_prose)
    assert_no_ranked_list(agreed)

    return GateResult(
        engineer=label,
        interpretation=agreed,
        dropped_claims=dropped,
        disagreements=disagreements,
        stripped_keys=stripped_keys,
        rating_prose=rating_prose,
        runs_compared=len(cleaned_runs),
    )


def gate_all(interpretations: dict[str, list[dict]],
             valid_prs_by_label: dict[str, set[int]]) -> dict[str, GateResult]:
    return {
        label: gate(label, runs, valid_prs_by_label.get(label, set()))
        for label, runs in interpretations.items()
    }
