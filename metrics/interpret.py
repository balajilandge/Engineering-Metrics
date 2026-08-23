"""
Layer 3 — Interpret. The only place in this pipeline where a model runs.

It reads diffs and review comments for one anonymized engineer and returns
plain English: a summary, complexity claims with the diff cited, blockers, and
evidence of unblocking others. It is required to give both the most and the
least favourable reading of the same evidence, and "insufficient evidence" is
an allowed — often correct — answer.

Three properties are structural, not requests:

  * Input is anonymized upstream and re-verified here before the call.
  * Output is a JSON schema in which every claim has an `evidence` field.
    The schema has no field for a score, a rating or a rank, so the model has
    nowhere to put one.
  * The call runs `interpret_runs` times (default 2). The runs are never
    averaged or merged here — both are handed to the gate, which flags where
    they disagree.

The `anthropic` SDK is imported lazily so layers 1, 2, 4 and the gate keep
running with no third-party dependency installed.
"""
from __future__ import annotations

import json
import sys

from .anonymize import verify_anonymized

MODEL_DEFAULT = "claude-opus-5"


class Layer3Unavailable(RuntimeError):
    """
    Layer 3 cannot run at all — a rejected request, an exhausted credit
    balance, a bad model id. Distinct from a single run failing, and
    deliberately NOT fatal to the pipeline: layers 1, 2 and 4 stand alone, so
    the caller catches this, drops the interpretation, and still ships the
    deterministic report. The run is still marked failed at the end.
    """

SYSTEM_PROMPT = """\
You are reading one engineer's pull requests for a single month and writing \
the interpretation an engineering manager will use to prepare a 1:1. You are \
reading anonymized data: you know this person only as "Engineer X". You do \
not know their name, seniority, tenure, or anything about them beyond the \
evidence in this payload.

Your job is to describe what the evidence shows, not to evaluate the person.

Rules:

1. Every claim you make must cite specific evidence from the payload — a PR \
number, a quoted line from a diff, or a quoted review comment. A claim you \
cannot cite is a claim you must not make.
2. You must give both the most favourable and the least favourable reading a \
reasonable person could take from the same evidence. Both must be genuine \
readings of this evidence, not a compliment paired with a criticism.
3. "Insufficient evidence" is a correct and expected answer. PR counts and \
diffs do not show scope negotiation, mentoring in DMs, incident response, \
design work, or anything that happened outside a pull request. When the \
evidence does not support a conclusion, say so plainly and set the \
insufficient_evidence field.
4. Do not rate, score, rank, grade or compare this engineer against anyone \
else. You have not been given anyone else's data, and a comparison you infer \
from a single profile would be fabricated.
5. Do not speculate about the person behind the work — not their motivation, \
their attitude, their effort level, or whether they are struggling. Describe \
the work.
6. Prefer the specific to the general. "PR 4821 rewrites the retry loop to \
handle partial batch failure (diff: `if resp.partial:`)" beats "made \
improvements to reliability".
"""

# Every claim object carries `evidence`; `additionalProperties: false` and the
# absence of any score field mean the model cannot invent one.
_CLAIM = {
    "type": "object",
    "properties": {
        "claim": {"type": "string",
                  "description": "One specific, falsifiable statement."},
        "evidence": {
            "type": "object",
            "properties": {
                "pr": {"type": "integer",
                       "description": "PR number this claim rests on."},
                "kind": {"type": "string", "enum": ["diff", "review_comment", "metric"]},
                "quote": {"type": "string",
                          "description": "Verbatim excerpt from the cited source."},
            },
            "required": ["pr", "kind", "quote"],
            "additionalProperties": False,
        },
    },
    "required": ["claim", "evidence"],
    "additionalProperties": False,
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "engineer": {"type": "string", "description": "The anonymized label, echoed back."},
        "summary": {"type": "string",
                    "description": "Plain-English account of the month's work, 3-6 sentences."},
        "complexity": {"type": "array", "items": _CLAIM,
                       "description": "What was hard, with the diff cited."},
        "blockers": {"type": "array", "items": _CLAIM,
                     "description": "What slowed this work down, evidenced."},
        "unblocking_others": {"type": "array", "items": _CLAIM,
                              "description": "Evidence this engineer unblocked other people."},
        "most_favourable_reading": {"type": "string"},
        "least_favourable_reading": {"type": "string"},
        "insufficient_evidence": {
            "type": "array", "items": {"type": "string"},
            "description": "Questions this data cannot answer. May be long; empty only if truly nothing is missing.",
        },
        "questions_for_the_1_1": {
            "type": "array", "items": {"type": "string"},
            "description": "Open questions to ask the engineer. Questions, not conclusions.",
        },
    },
    "required": ["engineer", "summary", "complexity", "blockers",
                 "unblocking_others", "most_favourable_reading",
                 "least_favourable_reading", "insufficient_evidence",
                 "questions_for_the_1_1"],
    "additionalProperties": False,
}


def build_payload(profile: dict, diffs: dict[int, str], comments: dict[int, list[str]],
                  corrections: list[str], max_diff_chars: int) -> dict:
    """Assembles the anonymized evidence bundle for one engineer."""
    evidence = []
    for item in profile.get("evidence_prs", []):
        number = item["number"]
        diff = (diffs.get(number) or "")[:max_diff_chars]
        evidence.append({
            "pr": number,
            "title": item.get("title", ""),
            "type": item.get("type", ""),
            "churn": item.get("churn"),
            "diff": diff,
            "review_comments": comments.get(number, []),
        })
    payload = {
        "engineer": profile.get("engineer"),
        "metrics": {k: v for k, v in profile.items()
                    if k in ("throughput", "reviews", "rework")},
        "pull_requests": evidence,
    }
    if corrections:
        payload["corrections_from_the_engineer"] = corrections
    return payload


def _user_message(payload: dict) -> str:
    parts = [
        "Here is one month of anonymized evidence for a single engineer.",
        "",
        json.dumps(payload, indent=2, ensure_ascii=False),
    ]
    if payload.get("corrections_from_the_engineer"):
        parts += [
            "",
            "The engineer has read a previous version of this interpretation and "
            "filed the corrections listed under `corrections_from_the_engineer`. "
            "Treat them as first-hand evidence about work the data does not show. "
            "Where a correction contradicts an earlier reading, follow the "
            "correction and say what changed.",
        ]
    return "\n".join(parts)


def _extract_json(response) -> dict:
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ValueError("model returned no text block")
    return json.loads(text)


def interpret_one(client, payload: dict, config) -> list[dict]:
    """
    Runs the interpretation `config.interpret_runs` times and returns every
    run. Nothing is merged or averaged here — that is the gate's decision, and
    the gate's rule is to flag disagreement rather than smooth it over.
    """
    import anthropic  # noqa: PLC0415 - lazy: layers 1/2/4 need no SDK

    runs: list[dict] = []
    for attempt in range(config.interpret_runs):
        try:
            with client.beta.messages.stream(
                model=config.model,
                max_tokens=64000,
                system=SYSTEM_PROMPT,
                thinking={"type": "adaptive"},
                output_config={
                    "effort": config.effort,
                    "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
                },
                # Route around a safety refusal instead of dropping the engineer
                # silently: a missing page is worse than a fallback-model page.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=[{"role": "user", "content": _user_message(payload)}],
            ) as stream:
                response = stream.get_final_message()

            if response.stop_reason == "refusal":
                category = getattr(response.stop_details, "category", None)
                print(f"  run {attempt + 1}: refused ({category}); skipping run",
                      file=sys.stderr)
                continue

            runs.append(_extract_json(response))

        except anthropic.RateLimitError as exc:
            print(f"  run {attempt + 1}: rate limited: {exc}", file=sys.stderr)
        except anthropic.BadRequestError as exc:
            # A rejected request will not fix itself on the next engineer:
            # a bad schema, an unavailable model or an empty credit balance
            # applies to every call. Abandon Layer 3 rather than sending the
            # same doomed request once per engineer.
            raise Layer3Unavailable(f"request rejected: {exc}") from exc
        except anthropic.AuthenticationError as exc:
            raise Layer3Unavailable(f"ANTHROPIC_API_KEY rejected: {exc}") from exc
        except anthropic.PermissionDeniedError as exc:
            raise Layer3Unavailable(f"API key lacks access: {exc}") from exc
        except anthropic.APIStatusError as exc:
            print(f"  run {attempt + 1}: API error {exc.status_code}: {exc}",
                  file=sys.stderr)
        except anthropic.APIConnectionError as exc:
            print(f"  run {attempt + 1}: connection error: {exc}", file=sys.stderr)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"  run {attempt + 1}: unparseable response: {exc}", file=sys.stderr)

    return runs


def interpret(profiles: list[dict], mapping: dict[str, str], diffs, comments,
              corrections: dict[str, list[str]], config) -> dict[str, list[dict]]:
    """
    Returns {anonymized_label: [run, run]}. Layer 3 is skipped entirely unless
    INTERPRET is on — the deterministic layers stand alone, and a run with no
    API key still produces every number.
    """
    if not config.interpret:
        print("Layer 3 interpret: disabled (INTERPRET=false) — "
              "deterministic layers only")
        return {}

    try:
        import anthropic
    except ImportError:
        print("Layer 3 interpret: `anthropic` not installed "
              "(pip install -r requirements.txt) — skipping", file=sys.stderr)
        return {}

    client = anthropic.Anthropic()
    results: dict[str, list[dict]] = {}

    selected = profiles[:config.interpret_engineers]
    print(f"Layer 3 interpret: {len(selected)} engineers x "
          f"{config.interpret_runs} runs, model={config.model}")

    for profile in selected:
        label = profile["engineer"]
        payload = build_payload(
            profile, diffs.get(label, {}), comments.get(label, {}),
            corrections.get(label, []), config.max_diff_chars,
        )
        # Last check before the payload leaves the building.
        verify_anonymized(payload, mapping)

        runs = interpret_one(client, payload, config)
        if runs:
            results[label] = runs
            print(f"  {label}: {len(runs)} run(s) returned")
        else:
            print(f"  {label}: no usable runs", file=sys.stderr)

    return results
