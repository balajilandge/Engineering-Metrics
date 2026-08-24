"""
The cohort limit narrows the report to N engineers. It must stay a *filter*
and never become a ranking, and it must not break the engineer-FIRST
guarantee: no audience may discuss an engineer who got no page of their own.
"""
import pathlib
import unittest

from metrics.compute import select_engineer_cohort, assert_no_scores
from metrics.config import Config
from metrics.guardrails import assert_no_ranked_list


def _profile(login, merged=0, given=0):
    return {
        "engineer": login,
        "profile_url": f"https://example.invalid/{login}",
        "throughput": {"prs_created": merged, "prs_merged": merged,
                       "prs_merged_substantive": merged, "by_type": {},
                       "median_churn": None, "median_time_to_merge_h": None},
        "reviews": {"given": given, "authors_reviewed": 0,
                    "median_latency_h": None, "changes_requested_given": 0},
        "rework": {"prs_with_changes_requested": 0, "measured_over": 0,
                   "rate_pct": None, "reverts_authored": 0},
        "evidence_prs": [],
    }


# Deliberately built so alphabetical order and activity order disagree.
POPULATION = [
    _profile("alice", merged=1, given=0),
    _profile("bob", merged=40, given=2),
    _profile("carol", merged=0, given=90),
    _profile("dave", merged=3, given=1),
    _profile("erin", merged=20, given=20),
]


class CohortSelectionTest(unittest.TestCase):
    def test_limit_zero_returns_everyone(self):
        self.assertEqual(select_engineer_cohort(POPULATION, 0), POPULATION)

    def test_limit_above_population_returns_everyone(self):
        self.assertEqual(select_engineer_cohort(POPULATION, 99), POPULATION)

    def test_activity_rule_picks_by_evidence_volume(self):
        cohort = select_engineer_cohort(POPULATION, 3, "activity")
        # bob 42, carol 90, erin 40 beat dave 4 and alice 1.
        self.assertEqual([p["engineer"] for p in cohort],
                         ["bob", "carol", "erin"])

    def test_reviews_count_toward_selection(self):
        """carol authors nothing and reviews most — she must not be filtered
        out, or the cap would erase exactly the reviewer the README defends."""
        cohort = select_engineer_cohort(POPULATION, 1, "activity")
        self.assertEqual([p["engineer"] for p in cohort], ["carol"])

    def test_output_order_is_alphabetical_not_selection_order(self):
        """The selection order must not survive into the output, or the cohort
        leaks a ranking through its ordering alone."""
        cohort = select_engineer_cohort(POPULATION, 3, "activity")
        logins = [p["engineer"] for p in cohort]
        self.assertEqual(logins, sorted(logins))

    def test_alphabetical_rule(self):
        cohort = select_engineer_cohort(POPULATION, 2, "alphabetical")
        self.assertEqual([p["engineer"] for p in cohort], ["alice", "bob"])

    def test_profiles_are_returned_untouched(self):
        cohort = select_engineer_cohort(POPULATION, 3, "activity")
        for profile in cohort:
            self.assertIn(profile, POPULATION)
            self.assertNotIn("rank", profile)
            self.assertNotIn("score", profile)
            self.assertNotIn("position", profile)

    def test_cohort_passes_both_anti_ranking_gates(self):
        cohort = select_engineer_cohort(POPULATION, 3, "activity")
        assert_no_scores(cohort)          # Layer 2's guard
        assert_no_ranked_list(cohort)     # the gate's guard

    def test_unknown_rule_is_rejected(self):
        with self.assertRaises(ValueError):
            select_engineer_cohort(POPULATION, 2, "by_performance")

    def test_selection_is_deterministic(self):
        first = select_engineer_cohort(POPULATION, 3, "activity")
        second = select_engineer_cohort(list(POPULATION), 3, "activity")
        self.assertEqual([p["engineer"] for p in first],
                         [p["engineer"] for p in second])

    def test_ties_break_deterministically(self):
        tied = [_profile("zed", merged=5), _profile("adam", merged=5),
                _profile("mary", merged=5)]
        self.assertEqual(
            [p["engineer"] for p in select_engineer_cohort(tied, 2, "activity")],
            ["adam", "mary"])


class CohortConfigTest(unittest.TestCase):
    def test_default_is_uncapped(self):
        config = Config(repo="o/r", month="2026-07", token="")
        self.assertEqual(config.report_engineers, 0)
        self.assertEqual(config.report_engineer_select, "activity")


class EngineerFirstUnderCapTest(unittest.TestCase):
    """
    The invariant the cap could most easily break: manager-facing pages are
    rendered from the same trimmed `individuals` list, so every engineer they
    mention has a page. If the cap were applied only at page-writing time this
    would fail.
    """

    def test_manager_pages_see_only_engineers_with_pages(self):
        from metrics import distribute

        cohort = select_engineer_cohort(POPULATION, 3, "activity")
        computed = {
            "team": {"dora": [], "flow": [], "totals": {
                "prs_created": 64, "prs_merged": 64, "contributors": 5,
                "merged_by_type": {}, "reverts": 0}},
            "individuals": cohort,
            "cohort": {"contributors_total": 5, "engineers_reported": 3,
                       "capped": True, "rule": "activity", "note": "sample"},
        }
        page = distribute.render_squad_page(
            "team", [p["engineer"] for p in POPULATION], computed,
            "o/r", "2026-07", ("dependency", "config", "docs"))

        for absent in ("alice", "dave"):
            self.assertNotIn(absent, page,
                             f"{absent} has no engineer page but appears to a manager")
        self.assertIn("cover 3 of the 5 people", page)
        self.assertIn("not a ranking", page)


class StalePagePruningTest(unittest.TestCase):
    """
    A capped run must not leave the previous uncapped run's pages behind: they
    carry a stale release date and numbers that contradict the manifest, and
    nothing on the page marks them as superseded.
    """

    def _run_distribute(self, tmp, profiles):
        from metrics import distribute
        computed = {
            "team": {"dora": [], "flow": [], "totals": {
                "prs_created": 64, "prs_merged": 64, "contributors": 5,
                "merged_by_type": {}, "reverts": 0}},
            "individuals": profiles,
            "cohort": {"contributors_total": 5,
                       "engineers_reported": len(profiles),
                       "capped": len(profiles) < 5, "rule": "activity",
                       "note": "sample"},
        }
        return distribute.distribute_engineers(
            tmp, computed, {}, {p["engineer"]: p["engineer"] for p in profiles},
            "o/r", "2026-07", ("dependency", "config", "docs"))

    def test_capped_run_removes_the_previous_runs_extra_pages(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._run_distribute(tmp, POPULATION)
            engineers = pathlib.Path(tmp) / "engineers"
            self.assertEqual(len(list(engineers.glob("*.md"))), 5)

            cohort = select_engineer_cohort(POPULATION, 3, "activity")
            self._run_distribute(tmp, cohort)

            remaining = sorted(f.stem for f in engineers.glob("*.md"))
            self.assertEqual(remaining, ["bob", "carol", "erin"])

    def test_page_count_on_disk_matches_the_manifest(self):
        import json as _json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._run_distribute(tmp, POPULATION)
            self._run_distribute(tmp, select_engineer_cohort(POPULATION, 3))

            manifest = _json.loads(
                (pathlib.Path(tmp) / "release-manifest.json").read_text())
            on_disk = len(list((pathlib.Path(tmp) / "engineers").glob("*.md")))
            self.assertEqual(manifest["engineer_pages"], on_disk)

    def test_non_markdown_files_are_left_alone(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            engineers = pathlib.Path(tmp) / "engineers"
            engineers.mkdir(parents=True)
            keep = engineers / "NOTES.txt"
            keep.write_text("hand-written, not generated")
            self._run_distribute(tmp, select_engineer_cohort(POPULATION, 2))
            self.assertTrue(keep.exists())


if __name__ == "__main__":
    unittest.main()
