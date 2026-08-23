"""Layer 2 — team metrics, individual profiles, and the absence of a score."""
import unittest

from tests.helpers import END, START, make_collection, make_pr
from metrics.compute import (Metric, assert_no_scores, compute,
                             compute_individuals, compute_team)

NON_SUBSTANTIVE = ("dependency", "config", "docs")


def metric(block, name):
    return next(Metric(**m) for m in block if m["name"] == name)


class TestDeflation(unittest.TestCase):
    """The 23-becomes-14 arrow, in code."""

    def setUp(self):
        self.pulls = [
            make_pr(1, "sham", "Bump lodash", ["package-lock.json"],
                    "2026-07-02T09:00:00Z", "2026-07-02T10:00:00Z"),
            make_pr(2, "sham", "Bump axios", ["package.json"],
                    "2026-07-03T09:00:00Z", "2026-07-03T10:00:00Z"),
            make_pr(3, "sham", "CI tweak", [".github/workflows/ci.yml"],
                    "2026-07-04T09:00:00Z", "2026-07-04T10:00:00Z"),
            make_pr(4, "sham", "Docs", ["docs/a.md"],
                    "2026-07-05T09:00:00Z", "2026-07-05T10:00:00Z"),
            make_pr(5, "sham", "fix: retry loop", ["src/retry.py"],
                    "2026-07-06T09:00:00Z", "2026-07-08T10:00:00Z"),
            make_pr(6, "sham", "Add streaming", ["src/ingest.py"],
                    "2026-07-09T09:00:00Z", "2026-07-15T10:00:00Z"),
        ]

    def test_raw_count_and_substantive_count_both_reported(self):
        profiles = compute_individuals(make_collection(self.pulls), NON_SUBSTANTIVE)
        sham = profiles[0]
        self.assertEqual(sham["throughput"]["prs_merged"], 6)
        self.assertEqual(sham["throughput"]["prs_merged_substantive"], 2)

    def test_full_type_split_is_always_shown(self):
        profiles = compute_individuals(make_collection(self.pulls), NON_SUBSTANTIVE)
        by_type = profiles[0]["throughput"]["by_type"]
        self.assertEqual(by_type["dependency"], 2)
        self.assertEqual(by_type["config"], 1)
        self.assertEqual(by_type["docs"], 1)
        self.assertEqual(by_type["fix"], 1)
        self.assertEqual(by_type["feature"], 1)
        # Nothing is hidden: the split sums back to the raw count.
        self.assertEqual(sum(by_type.values()), 6)

    def test_deflation_is_deterministic(self):
        collection = make_collection(self.pulls)
        first = compute_individuals(collection, NON_SUBSTANTIVE)
        for _ in range(10):
            self.assertEqual(compute_individuals(collection, NON_SUBSTANTIVE), first)


class TestMissingSourcesAreNotZero(unittest.TestCase):
    """A metric with no source says so; it never reports 0."""

    def setUp(self):
        self.collection = make_collection([
            make_pr(1, "a", "fix: x", ["src/x.py"],
                    "2026-07-01T09:00:00Z", "2026-07-02T09:00:00Z"),
        ])

    def test_deployment_frequency_without_deploy_feed(self):
        team = compute_team(self.collection)
        deploy_freq = metric(team["dora"], "deployment_frequency")
        self.assertFalse(deploy_freq.available)
        self.assertIsNone(deploy_freq.value)
        self.assertEqual(deploy_freq.render(), "insufficient evidence")
        self.assertIn("deploy feed", deploy_freq.basis)

    def test_incident_metrics_without_incident_feed(self):
        team = compute_team(self.collection)
        for name in ("change_failure_rate", "time_to_restore"):
            self.assertFalse(metric(team["dora"], name).available, name)

    def test_lead_time_says_it_is_merge_time_not_deploy_time(self):
        lead = metric(compute_team(self.collection)["dora"], "lead_time_for_changes")
        self.assertTrue(lead.available)
        self.assertIn("not deploy time", lead.basis)

    def test_deploy_feed_unlocks_deployment_frequency(self):
        collection = make_collection(
            [make_pr(1, "a", "fix: x", ["src/x.py"],
                     "2026-07-01T09:00:00Z", "2026-07-02T09:00:00Z")],
            deploys=[{"id": "d1", "deployed_at": "2026-07-02T10:00:00Z"},
                     {"id": "d2", "deployed_at": "2026-07-03T10:00:00Z"}],
        )
        deploy_freq = metric(compute_team(collection)["dora"], "deployment_frequency")
        self.assertTrue(deploy_freq.available)
        self.assertAlmostEqual(deploy_freq.value, round(2 / 31, 2))

    def test_incident_feed_unlocks_restore_time(self):
        collection = make_collection(
            [make_pr(1, "a", "fix: x", ["src/x.py"],
                     "2026-07-01T09:00:00Z", "2026-07-02T09:00:00Z")],
            incidents=[{"id": "INC-1", "started_at": "2026-07-05T00:00:00Z",
                        "resolved_at": "2026-07-05T04:00:00Z"}],
        )
        restore = metric(compute_team(collection)["dora"], "time_to_restore")
        self.assertTrue(restore.available)
        self.assertEqual(restore.value, 4.0)


class TestFlowMetrics(unittest.TestCase):
    def test_carryover_counts_prs_opened_in_an_earlier_month(self):
        collection = make_collection([
            make_pr(1, "a", "Old work", ["src/a.py"],
                    "2026-06-20T09:00:00Z", "2026-07-02T09:00:00Z"),
            make_pr(2, "a", "New work", ["src/b.py"],
                    "2026-07-10T09:00:00Z", "2026-07-11T09:00:00Z"),
        ])
        carry = metric(compute_team(collection)["flow"], "carryover")
        self.assertEqual(carry.value, 50.0)

    def test_unreviewed_prs_report_the_real_finding_not_a_budget_hint(self):
        collection = make_collection([
            make_pr(1, "a", "Work", ["src/a.py"],
                    "2026-07-01T00:00:00Z", "2026-07-05T00:00:00Z", detailed=True),
        ])
        latency = metric(compute_team(collection)["flow"], "review_latency")
        self.assertFalse(latency.available)
        self.assertIn("none of the 1 PRs inspected had one", latency.basis)
        self.assertNotIn("DETAIL_BUDGET", latency.basis)

    def test_uninspected_prs_do_point_at_the_budget(self):
        collection = make_collection([
            make_pr(1, "a", "Work", ["src/a.py"],
                    "2026-07-01T00:00:00Z", "2026-07-05T00:00:00Z", detailed=False),
        ])
        latency = metric(compute_team(collection)["flow"], "review_latency")
        self.assertFalse(latency.available)
        self.assertIn("DETAIL_BUDGET", latency.basis)

    def test_review_latency_uses_first_review(self):
        collection = make_collection([
            make_pr(1, "a", "Work", ["src/a.py"],
                    "2026-07-01T00:00:00Z", "2026-07-05T00:00:00Z",
                    reviews=(("b", "APPROVED", "2026-07-03T00:00:00Z"),
                             ("c", "APPROVED", "2026-07-04T00:00:00Z"))),
        ])
        latency = metric(compute_team(collection)["flow"], "review_latency")
        self.assertEqual(latency.value, 48.0)


class TestIndividualProfiles(unittest.TestCase):
    def setUp(self):
        self.collection = make_collection([
            make_pr(1, "sham", "Add ingest", ["src/i.py"],
                    "2026-07-01T00:00:00Z", "2026-07-04T00:00:00Z",
                    reviews=(("nadia", "CHANGES_REQUESTED", "2026-07-02T00:00:00Z"),)),
            make_pr(2, "nadia", "fix: db", ["src/db.py"],
                    "2026-07-05T00:00:00Z", "2026-07-06T00:00:00Z",
                    reviews=(("sham", "APPROVED", "2026-07-05T12:00:00Z"),)),
        ])
        self.profiles = {p["engineer"]: p
                         for p in compute_individuals(self.collection, NON_SUBSTANTIVE)}

    def test_reviews_given_are_credited_to_the_reviewer(self):
        self.assertEqual(self.profiles["nadia"]["reviews"]["given"], 1)
        self.assertEqual(self.profiles["sham"]["reviews"]["given"], 1)

    def test_self_reviews_are_not_counted(self):
        collection = make_collection([
            make_pr(1, "sham", "Add x", ["src/x.py"],
                    "2026-07-01T00:00:00Z", "2026-07-02T00:00:00Z",
                    reviews=(("sham", "APPROVED", "2026-07-01T06:00:00Z"),)),
        ])
        # make_pr keeps whatever reviews it is given; collect() filters
        # self-reviews, so assert the profile does not credit the author.
        profiles = compute_individuals(collection, NON_SUBSTANTIVE)
        sham = next(p for p in profiles if p["engineer"] == "sham")
        self.assertEqual(sham["reviews"]["authors_reviewed"], 0)

    def test_rework_is_a_rate_over_measured_prs_not_all_prs(self):
        rework = self.profiles["sham"]["rework"]
        self.assertEqual(rework["prs_with_changes_requested"], 1)
        self.assertEqual(rework["measured_over"], 1)
        self.assertEqual(rework["rate_pct"], 100.0)

    def test_rework_rate_is_none_when_nothing_was_measured(self):
        collection = make_collection([
            make_pr(1, "sham", "Add x", ["src/x.py"],
                    "2026-07-01T00:00:00Z", "2026-07-02T00:00:00Z", detailed=False),
        ])
        profiles = compute_individuals(collection, NON_SUBSTANTIVE)
        self.assertIsNone(profiles[0]["rework"]["rate_pct"])

    def test_profiles_are_sorted_by_name_not_by_output(self):
        profiles = compute_individuals(self.collection, NON_SUBSTANTIVE)
        self.assertEqual([p["engineer"] for p in profiles], ["nadia", "sham"])


class TestNoScoreExists(unittest.TestCase):
    """Not withheld at render time — never computed."""

    def test_no_profile_carries_a_score_rating_or_rank(self):
        collection = make_collection([
            make_pr(1, "a", "Add x", ["src/x.py"],
                    "2026-07-01T00:00:00Z", "2026-07-02T00:00:00Z"),
        ])
        result = compute(collection, NON_SUBSTANTIVE)
        for profile in result["individuals"]:
            for forbidden in ("score", "rating", "rank", "grade", "percentile"):
                self.assertNotIn(forbidden, profile)

    def test_assert_no_scores_rejects_an_injected_score(self):
        with self.assertRaises(ValueError) as caught:
            assert_no_scores([{"engineer": "a", "score": 9.1}])
        self.assertIn("never one score", str(caught.exception))

    def test_assert_no_scores_rejects_a_nested_rank(self):
        with self.assertRaises(ValueError):
            assert_no_scores([{"engineer": "a", "throughput": {"rank": 3}}])


if __name__ == "__main__":
    unittest.main()
