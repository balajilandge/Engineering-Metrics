"""The v1 migration: rank removed, counts preserved, ranked reports deleted."""
import json
import os
import shutil
import tempfile
import unittest

from tests.helpers import *  # noqa: F401,F403 - sets up sys.path
from scripts.migrate_v1_artifacts import migrate_data_file

V1_PAYLOAD = {
    "repo": "acme/app",
    "month": "2026-07",
    "totals": {"prs_created": 10, "prs_merged": 8, "engineers": 2},
    "leaderboard": [
        {"engineer": "sham", "profile_url": "https://github.com/sham",
         "prs_created": 6, "prs_merged": 5, "rank": 1},
        {"engineer": "nadia", "profile_url": "https://github.com/nadia",
         "prs_created": 4, "prs_merged": 3, "rank": 2},
    ],
}


class TestMigration(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.path = os.path.join(self.dir, "2026-07.json")
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(V1_PAYLOAD, handle)

    def migrated(self):
        migrate_data_file(self.path, dry_run=False)
        with open(self.path, encoding="utf-8") as handle:
            return json.load(handle)

    def test_rank_fields_are_removed(self):
        payload = self.migrated()
        # The field, not the word: `schema_v1_import` legitimately explains in
        # prose that a rank used to be here.
        self.assertNotIn('"rank"', json.dumps(payload))
        for individual in payload["individuals"]:
            self.assertNotIn("rank", individual)

    def test_leaderboard_key_is_gone(self):
        self.assertNotIn("leaderboard", self.migrated())

    def test_counts_are_preserved_exactly(self):
        by_name = {i["engineer"]: i for i in self.migrated()["individuals"]}
        self.assertEqual(by_name["sham"]["throughput"]["prs_merged"], 5)
        self.assertEqual(by_name["nadia"]["throughput"]["prs_created"], 4)

    def test_ordering_becomes_alphabetical_not_by_output(self):
        names = [i["engineer"] for i in self.migrated()["individuals"]]
        self.assertEqual(names, ["nadia", "sham"])

    def test_missing_type_split_is_null_not_zero(self):
        throughput = self.migrated()["individuals"][0]["throughput"]
        self.assertIsNone(throughput["by_type"])
        self.assertIsNone(throughput["prs_merged_substantive"])

    def test_schema_version_and_provenance_marker_are_set(self):
        payload = self.migrated()
        self.assertEqual(payload["schema_version"], 2)
        self.assertIn("before PR classification", payload["schema_v1_import"])

    def test_dry_run_writes_nothing(self):
        before = open(self.path, encoding="utf-8").read()
        rows, ranks = migrate_data_file(self.path, dry_run=True)
        self.assertEqual((rows, ranks), (2, 2))
        self.assertEqual(open(self.path, encoding="utf-8").read(), before)

    def test_an_already_migrated_file_is_left_alone(self):
        self.migrated()
        before = open(self.path, encoding="utf-8").read()
        self.assertEqual(migrate_data_file(self.path, dry_run=False), (0, 0))
        self.assertEqual(open(self.path, encoding="utf-8").read(), before)


class TestCommittedDataIsClean(unittest.TestCase):
    """The repository itself must not still contain a ranked artifact."""

    def test_no_committed_data_file_carries_a_rank(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for directory, _, files in os.walk(os.path.join(root, "data")):
            for name in files:
                if not name.endswith(".json"):
                    continue
                with open(os.path.join(directory, name), encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.assertNotIn("leaderboard", payload, name)
                self.assertNotIn('"rank"', json.dumps(payload), name)


if __name__ == "__main__":
    unittest.main()
