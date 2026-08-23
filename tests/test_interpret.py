"""
Layer 3's contract, tested without a network call.

What matters here is the shape of what we ask for and what we send: the schema
has nowhere to put a score, every claim needs evidence, and the payload that
leaves the building carries no name.
"""
import json
import unittest

from tests.helpers import *  # noqa: F401,F403 - sets up sys.path
from metrics.anonymize import build_mapping, verify_anonymized
from metrics.config import Config
from metrics.interpret import (MODEL_DEFAULT, OUTPUT_SCHEMA, SYSTEM_PROMPT,
                               build_payload, interpret)


class TestOutputSchema(unittest.TestCase):
    def test_every_claim_list_requires_an_evidence_field(self):
        for field in ("complexity", "blockers", "unblocking_others"):
            item = OUTPUT_SCHEMA["properties"][field]["items"]
            self.assertIn("evidence", item["required"], field)
            self.assertIn("claim", item["required"], field)

    def test_evidence_requires_a_pr_a_kind_and_a_quote(self):
        evidence = (OUTPUT_SCHEMA["properties"]["complexity"]["items"]
                    ["properties"]["evidence"])
        self.assertEqual(sorted(evidence["required"]), ["kind", "pr", "quote"])
        self.assertIs(evidence["additionalProperties"], False)

    def test_both_readings_are_required_not_optional(self):
        self.assertIn("most_favourable_reading", OUTPUT_SCHEMA["required"])
        self.assertIn("least_favourable_reading", OUTPUT_SCHEMA["required"])

    def test_insufficient_evidence_is_a_first_class_field(self):
        self.assertIn("insufficient_evidence", OUTPUT_SCHEMA["required"])

    def test_schema_has_no_field_for_a_score_rating_or_rank(self):
        serialized = json.dumps(OUTPUT_SCHEMA).lower()
        for forbidden in ("score", "rating", "rank", "grade", "percentile", "tier"):
            self.assertNotIn(f'"{forbidden}"', serialized, forbidden)

    def test_schema_is_closed_so_the_model_cannot_add_fields(self):
        self.assertIs(OUTPUT_SCHEMA["additionalProperties"], False)


class TestSystemPrompt(unittest.TestCase):
    def test_it_forbids_comparison_and_ranking(self):
        lowered = SYSTEM_PROMPT.lower()
        for phrase in ("rate, score, rank", "insufficient evidence",
                       "most favourable and the least favourable"):
            self.assertIn(phrase, lowered)

    def test_it_requires_a_citation_per_claim(self):
        self.assertIn("cite specific evidence", SYSTEM_PROMPT.lower())

    def test_it_forbids_speculating_about_the_person(self):
        self.assertIn("do not speculate about the person", SYSTEM_PROMPT.lower())


class TestPayload(unittest.TestCase):
    def setUp(self):
        self.mapping = build_mapping(["sham", "nadia"], "acme/app:2026-07")
        self.label = self.mapping["sham"]
        self.profile = {
            "engineer": self.label,
            "throughput": {"prs_merged": 6, "prs_merged_substantive": 2},
            "reviews": {"given": 3},
            "rework": {"rate_pct": 20.0},
            "evidence_prs": [{"number": 5, "title": "fix: retry", "type": "fix",
                              "churn": 240}],
        }

    def test_payload_carries_metrics_and_evidence(self):
        payload = build_payload(self.profile, {5: "diff text"},
                                {5: ["a review comment"]}, [], 40_000)
        self.assertEqual(payload["engineer"], self.label)
        self.assertEqual(payload["metrics"]["throughput"]["prs_merged"], 6)
        self.assertEqual(payload["pull_requests"][0]["diff"], "diff text")
        self.assertEqual(payload["pull_requests"][0]["review_comments"],
                         ["a review comment"])

    def test_payload_has_no_name_in_it(self):
        payload = build_payload(self.profile, {5: "diff"}, {5: []}, [], 40_000)
        verify_anonymized(payload, self.mapping)

    def test_long_diffs_are_capped(self):
        payload = build_payload(self.profile, {5: "x" * 5000}, {}, [], 100)
        self.assertEqual(len(payload["pull_requests"][0]["diff"]), 100)

    def test_corrections_are_included_when_present(self):
        payload = build_payload(self.profile, {}, {},
                                ["The revert was planned."], 40_000)
        self.assertEqual(payload["corrections_from_the_engineer"],
                         ["The revert was planned."])

    def test_corrections_key_is_absent_when_there_are_none(self):
        payload = build_payload(self.profile, {}, {}, [], 40_000)
        self.assertNotIn("corrections_from_the_engineer", payload)


class TestLayerThreeIsOptional(unittest.TestCase):
    def test_interpretation_is_skipped_when_disabled(self):
        config = Config(repo="acme/app", month="2026-07", token="", interpret=False)
        self.assertEqual(interpret([], {}, {}, {}, {}, config), {})

    def test_default_model_is_the_current_opus(self):
        self.assertEqual(MODEL_DEFAULT, "claude-opus-5")
        self.assertEqual(Config(repo="a/b", month="2026-07", token="").model,
                         "claude-opus-5")

    def test_two_runs_by_default_so_the_gate_has_something_to_compare(self):
        self.assertEqual(Config(repo="a/b", month="2026-07", token="").interpret_runs, 2)


if __name__ == "__main__":
    unittest.main()
