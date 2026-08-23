"""The gate: no citation, no claim. Disagreement flagged, never averaged."""
import unittest

from tests.helpers import claim, make_run
from metrics.guardrails import (assert_no_ranked_list, compare_runs,
                                corroboration, drop_uncited, gate,
                                scrub_rating_prose, strip_ratings)

VALID = {1, 2, 3}


class TestNoCitationNoClaim(unittest.TestCase):
    def test_claim_with_good_citation_survives(self):
        run = make_run("Engineer A", [claim("Reworked retry", pr=1)])
        cleaned, dropped = drop_uncited(run, VALID)
        self.assertEqual(len(cleaned["complexity"]), 1)
        self.assertEqual(dropped, [])

    def test_missing_evidence_object_is_dropped(self):
        run = make_run("Engineer A", [{"claim": "Vibes", "evidence": {}}])
        cleaned, dropped = drop_uncited(run, VALID)
        self.assertEqual(cleaned["complexity"], [])
        self.assertEqual(dropped[0]["reason"], "no evidence object")

    def test_empty_quote_is_dropped(self):
        run = make_run("Engineer A",
                       [{"claim": "X", "evidence": {"pr": 1, "kind": "diff", "quote": "  "}}])
        _, dropped = drop_uncited(run, VALID)
        self.assertIn("no quote", dropped[0]["reason"])

    def test_citation_to_a_pr_the_engineer_did_not_author_is_dropped(self):
        run = make_run("Engineer A", [claim("Fixed someone else's bug", pr=999)])
        cleaned, dropped = drop_uncited(run, VALID)
        self.assertEqual(cleaned["complexity"], [])
        self.assertIn("#999", dropped[0]["reason"])

    def test_dropping_is_recorded_not_silent(self):
        run = make_run("Engineer A", [{"claim": "Unsupported", "evidence": {}}])
        _, dropped = drop_uncited(run, VALID)
        self.assertEqual(dropped[0]["claim"], "Unsupported")
        self.assertEqual(dropped[0]["field"], "complexity")


class TestDisagreementIsFlaggedNotAveraged(unittest.TestCase):
    def test_claims_in_both_runs_survive(self):
        runs = [make_run("A", [claim("Reworked the retry loop", pr=1)]),
                make_run("A", [claim("Reworked retry loop", pr=1)])]
        agreed, disagreements = compare_runs(runs)
        self.assertEqual(len(agreed["complexity"]), 1)
        self.assertEqual(disagreements, [])

    def test_claim_in_only_one_run_is_flagged_and_excluded(self):
        runs = [make_run("A", [claim("Reworked retry", pr=1),
                               claim("Rewrote the scheduler", pr=2)]),
                make_run("A", [claim("Reworked retry", pr=1)])]
        agreed, disagreements = compare_runs(runs)
        self.assertEqual([c["claim"] for c in agreed["complexity"]], ["Reworked retry"])
        self.assertEqual(len(disagreements), 1)
        self.assertEqual(disagreements[0]["kind"], "only_in_run_1")
        self.assertEqual(disagreements[0]["claim"], "Rewrote the scheduler")

    def test_differing_narratives_are_surfaced_verbatim_both_ways(self):
        runs = [make_run("A", [], summary="Delivered a large refactor of ingest."),
                make_run("A", [], summary="Mostly small maintenance work.")]
        _, disagreements = compare_runs(runs)
        narrative = next(d for d in disagreements if d["kind"] == "narratives_differ")
        # Both readings are kept intact — nothing is blended into a middle.
        self.assertEqual(narrative["run_1"], "Delivered a large refactor of ingest.")
        self.assertEqual(narrative["run_2"], "Mostly small maintenance work.")

    def test_nothing_is_averaged(self):
        runs = [make_run("A", [claim("Only mine", pr=1)]),
                make_run("A", [claim("Only theirs", pr=2)])]
        agreed, disagreements = compare_runs(runs)
        self.assertEqual(agreed["complexity"], [])
        self.assertEqual(len(disagreements), 2)

    def test_gaps_are_unioned_because_doubt_stands(self):
        runs = [make_run("A", [], gaps=["design work"]),
                make_run("A", [], gaps=["mentoring"])]
        agreed, _ = compare_runs(runs)
        self.assertEqual(sorted(agreed["insufficient_evidence"]),
                         ["design work", "mentoring"])

    def test_a_single_run_is_marked_unverified_not_agreed(self):
        agreed, disagreements = compare_runs([make_run("A", [claim("X", pr=1)])])
        self.assertEqual(len(agreed["complexity"]), 1)
        self.assertEqual(disagreements[0]["kind"], "unverified")


class TestClaimMatchingRestsOnTheCitedPR(unittest.TestCase):
    """
    Real two-run output paired a claim about one PR with an unrelated claim
    about another purely on shared phrasing. Requiring the same PR removes
    that class of error outright.
    """

    def test_similar_wording_about_different_prs_never_matches(self):
        runs = [make_run("A", [claim("Reworked the retry loop for batches", pr=1)]),
                make_run("A", [claim("Reworked the retry loop for batches", pr=2)])]
        agreed, disagreements = compare_runs(runs)
        self.assertEqual(agreed["complexity"], [])
        self.assertEqual({d["kind"] for d in disagreements},
                         {"only_in_run_1", "only_in_run_2"})

    def test_paraphrase_of_one_claim_on_one_pr_is_matched(self):
        runs = [make_run("A", [claim("PR 1 chose the paginated pulls listing "
                                     "over the Search API because Search "
                                     "truncates at 1000 results", pr=1)]),
                make_run("A", [claim("PR 1 chose the paginated pulls REST "
                                     "endpoint over the Search API because "
                                     "Search truncates at 1000 results", pr=1)])]
        agreed, disagreements = compare_runs(runs)
        self.assertEqual(len(agreed["complexity"]), 1)
        self.assertEqual(disagreements, [])

    def test_disagreements_record_the_cited_pr_for_diagnosis(self):
        runs = [make_run("A", [claim("Something only run 1 said", pr=7)]),
                make_run("A", [])]
        _, disagreements = compare_runs(runs)
        self.assertEqual(disagreements[0]["pr"], 7)


class TestCorroborationNeedsNoTextMatching(unittest.TestCase):
    def test_prs_both_runs_discussed_are_corroborated(self):
        runs = [make_run("A", [claim("worded one way", pr=1),
                               claim("about three", pr=3)]),
                make_run("A", [claim("worded completely differently", pr=1)])]
        corroborated, one_sided = corroboration(runs)
        self.assertEqual(corroborated, [1])
        self.assertEqual(one_sided, [3])

    def test_a_single_run_corroborates_nothing(self):
        self.assertEqual(corroboration([make_run("A", [claim("x", pr=1)])]), ([], []))

    def test_gate_exposes_corroboration_in_the_audit(self):
        runs = [make_run("A", [claim("one phrasing", pr=1)]),
                make_run("A", [claim("an entirely different phrasing", pr=1)])]
        result = gate("A", runs, {1})
        self.assertEqual(result.corroborated_prs, [1])
        self.assertEqual(result.to_dict()["audit"]["corroborated_prs"], [1])


class TestNoRatingNoRank(unittest.TestCase):
    def test_score_keys_are_stripped_anywhere_in_the_tree(self):
        payload = {"a": {"score": 9, "b": [{"rank": 1, "keep": "yes"}]}}
        cleaned, stripped = strip_ratings(payload)
        self.assertEqual(cleaned, {"a": {"b": [{"keep": "yes"}]}})
        self.assertEqual(len(stripped), 2)

    def test_rating_written_as_prose_is_removed(self):
        run = make_run("A", [], summary="A top performer this quarter.")
        cleaned, removed = scrub_rating_prose(run)
        self.assertNotIn("top performer", cleaned["summary"])
        self.assertIn("[comparative claim removed]", cleaned["summary"])
        self.assertTrue(removed)

    def test_comparative_prose_variants(self):
        for text in ("They are above average.", "Ranked #2 on the team.",
                     "One of the best engineers here.", "In the top 10% of the org."):
            _, removed = scrub_rating_prose(make_run("A", [], summary=text))
            self.assertTrue(removed, text)

    def test_ordinary_prose_is_left_alone(self):
        text = "Shipped a retry fix; the diff is small but the failure mode was subtle."
        cleaned, removed = scrub_rating_prose(make_run("A", [], summary=text))
        self.assertEqual(cleaned["summary"], text)
        self.assertEqual(removed, [])

    def test_a_ranked_list_of_engineers_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            assert_no_ranked_list([{"engineer": "a", "rank": 1},
                                   {"engineer": "b", "rank": 2}])
        self.assertIn("cannot leak", str(caught.exception))

    def test_an_unranked_list_of_engineers_is_fine(self):
        assert_no_ranked_list([{"engineer": "a", "prs_merged": 4},
                               {"engineer": "b", "prs_merged": 9}])


class TestGateEndToEnd(unittest.TestCase):
    def test_audit_records_every_intervention(self):
        runs = [
            {**make_run("Engineer A", [claim("Reworked retry", pr=1),
                                       {"claim": "Uncited", "evidence": {}}],
                        summary="A top performer."),
             "score": 9},
            make_run("Engineer A", [claim("Reworked the retry", pr=1)],
                     summary="Solid month of maintenance."),
        ]
        result = gate("Engineer A", runs, VALID)
        self.assertEqual(result.runs_compared, 2)
        self.assertEqual(len(result.dropped_claims), 1)
        self.assertIn("run_1.score", result.stripped_keys)
        self.assertTrue(result.rating_prose)
        self.assertTrue(result.contested)
        # The surviving claim is the one both runs made.
        self.assertEqual(len(result.interpretation["complexity"]), 1)

    def test_gated_output_carries_no_forbidden_key(self):
        runs = [{**make_run("Engineer A", [claim("X", pr=1)]), "rating": "A"},
                {**make_run("Engineer A", [claim("X", pr=1)]), "percentile": 90}]
        result = gate("Engineer A", runs, VALID)
        serialized = str(result.interpretation).lower()
        for forbidden in ("rating", "percentile", "score"):
            self.assertNotIn(f"'{forbidden}'", serialized)


if __name__ == "__main__":
    unittest.main()
