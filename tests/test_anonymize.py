"""The Layer 2 -> Layer 3 arrow: names stripped, Engineer A, B, C."""
import unittest

from tests.helpers import *  # noqa: F401,F403 - sets up sys.path
from metrics.anonymize import (anonymize_profile, build_mapping, scrub_text,
                               verify_anonymized)

LOGINS = ["sham", "nadia", "priya", "tom"]
SALT = "acme/app:2026-07"


class TestMapping(unittest.TestCase):
    def test_every_login_gets_a_distinct_label(self):
        mapping = build_mapping(LOGINS, SALT)
        self.assertEqual(len(set(mapping.values())), len(LOGINS))
        for label in mapping.values():
            self.assertTrue(label.startswith("Engineer "))

    def test_mapping_is_stable_across_runs_of_the_same_month(self):
        self.assertEqual(build_mapping(LOGINS, SALT), build_mapping(LOGINS, SALT))

    def test_mapping_changes_between_months(self):
        july = build_mapping(LOGINS, "acme/app:2026-07")
        august = build_mapping(LOGINS, "acme/app:2026-08")
        self.assertNotEqual(july, august)

    def test_letters_are_not_alphabetical_so_the_order_carries_no_signal(self):
        mapping = build_mapping(LOGINS, SALT)
        alphabetical = {login: f"Engineer {chr(65 + i)}"
                        for i, login in enumerate(sorted(LOGINS))}
        self.assertNotEqual(mapping, alphabetical)

    def test_labels_extend_past_z(self):
        mapping = build_mapping([f"user{i}" for i in range(30)], SALT)
        self.assertEqual(len(set(mapping.values())), 30)
        self.assertTrue(any(len(label.split()[1]) == 2 for label in mapping.values()))


class TestScrubbing(unittest.TestCase):
    def setUp(self):
        self.mapping = build_mapping(LOGINS, SALT)

    def test_known_mentions_become_labels(self):
        text = scrub_text("thanks @sham", self.mapping)
        self.assertEqual(text, f"thanks {self.mapping['sham']}")

    def test_unknown_handles_are_redacted_not_left_in(self):
        self.assertIn("[redacted]", scrub_text("cc @someone-else", self.mapping))
        self.assertNotIn("someone-else", scrub_text("cc @someone-else", self.mapping))

    def test_profile_urls_are_replaced(self):
        text = scrub_text("see https://github.com/nadia for context", self.mapping)
        self.assertNotIn("nadia", text)

    def test_bare_logins_in_prose_are_replaced(self):
        text = scrub_text("nadia suggested a different index", self.mapping)
        self.assertNotIn("nadia", text.lower())


class TestProfileAnonymization(unittest.TestCase):
    def setUp(self):
        self.mapping = build_mapping(LOGINS, SALT)
        self.profile = {
            "engineer": "sham",
            "profile_url": "https://github.com/sham",
            "throughput": {"prs_merged": 6},
            "evidence_prs": [
                {"number": 1, "title": "Address nadia's review", "type": "fix",
                 "url": "https://github.com/acme/app/pull/1", "churn": 40},
            ],
        }

    def test_label_replaces_login(self):
        clean = anonymize_profile(self.profile, self.mapping)
        self.assertEqual(clean["engineer"], self.mapping["sham"])

    def test_identity_fields_are_removed(self):
        clean = anonymize_profile(self.profile, self.mapping)
        self.assertNotIn("profile_url", clean)
        self.assertNotIn("url", clean["evidence_prs"][0])

    def test_names_inside_pr_titles_are_scrubbed(self):
        clean = anonymize_profile(self.profile, self.mapping)
        self.assertNotIn("nadia", clean["evidence_prs"][0]["title"].lower())

    def test_the_original_profile_is_not_mutated(self):
        anonymize_profile(self.profile, self.mapping)
        self.assertEqual(self.profile["engineer"], "sham")
        self.assertEqual(self.profile["profile_url"], "https://github.com/sham")

    def test_numbers_survive_untouched(self):
        clean = anonymize_profile(self.profile, self.mapping)
        self.assertEqual(clean["throughput"]["prs_merged"], 6)


class TestVerification(unittest.TestCase):
    """The last check before the only call that leaves the building."""

    def setUp(self):
        self.mapping = build_mapping(LOGINS, SALT)

    def test_clean_payload_passes(self):
        verify_anonymized({"engineer": "Engineer A", "notes": ["all good"]},
                          self.mapping)

    def test_a_surviving_login_raises(self):
        with self.assertRaises(ValueError) as caught:
            verify_anonymized({"engineer": "Engineer A", "notes": ["ask sham"]},
                              self.mapping)
        self.assertIn("sham", str(caught.exception))

    def test_a_surviving_identity_key_raises(self):
        with self.assertRaises(ValueError) as caught:
            verify_anonymized({"engineer": "Engineer A",
                               "profile_url": "https://example.com"}, self.mapping)
        self.assertIn("profile_url", str(caught.exception))

    def test_it_looks_inside_nested_structures(self):
        with self.assertRaises(ValueError):
            verify_anonymized(
                {"pull_requests": [{"diff": "reviewed by priya"}]}, self.mapping)


if __name__ == "__main__":
    unittest.main()
