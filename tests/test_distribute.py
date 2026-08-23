"""Layer 4 — who sees what, and the embargo that puts engineers first."""
import datetime
import json
import os
import shutil
import tempfile
import unittest

from tests.helpers import claim, make_collection, make_pr, make_run
from metrics.anonymize import build_mapping
from metrics.compute import compute
from metrics.distribute import (EmbargoError, check_embargo, distribute_engineers,
                                distribute_rest, read_manifest, render_founder_page,
                                render_squad_page, write_manifest)
from metrics.guardrails import gate_all

NON_SUBSTANTIVE = ("dependency", "config", "docs")
SOURCES = [{"name": "pull_requests", "availability": "ok", "detail": "8 PRs"},
           {"name": "incidents", "availability": "unconfigured", "detail": "none"}]


def fixture():
    pulls = [
        make_pr(1, "sham", "Bump lodash", ["package-lock.json"],
                "2026-07-02T09:00:00Z", "2026-07-02T10:00:00Z"),
        make_pr(2, "sham", "fix: retry loop", ["src/retry.py"],
                "2026-07-06T09:00:00Z", "2026-07-08T10:00:00Z",
                reviews=(("nadia", "APPROVED", "2026-07-07T09:00:00Z"),)),
        make_pr(3, "nadia", "Add index migration", ["src/db.py"],
                "2026-07-09T09:00:00Z", "2026-07-11T10:00:00Z",
                reviews=(("sham", "APPROVED", "2026-07-10T09:00:00Z"),)),
    ]
    collection = make_collection(pulls)
    computed = compute(collection, NON_SUBSTANTIVE)
    mapping = build_mapping([p["engineer"] for p in computed["individuals"]],
                            "acme/app:2026-07")
    runs = {
        mapping["sham"]: [make_run(mapping["sham"], [claim("Reworked retry", pr=2)]),
                          make_run(mapping["sham"], [claim("Reworked the retry", pr=2)])],
    }
    valid = {mapping[p["engineer"]]: {i["number"] for i in p["evidence_prs"]}
             for p in computed["individuals"]}
    return computed, mapping, gate_all(runs, valid)


class DistributeCase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.computed, self.mapping, self.gated = fixture()

    def release_engineers(self):
        return distribute_engineers(self.root, self.computed, self.gated,
                                    self.mapping, "acme/app", "2026-07",
                                    NON_SUBSTANTIVE)

    def release_rest(self, squads=None, embargo=0):
        return distribute_rest(self.root, self.computed, self.gated, self.mapping,
                               "acme/app", "2026-07", SOURCES,
                               squads or {}, NON_SUBSTANTIVE, embargo)

    def read(self, *parts):
        with open(os.path.join(self.root, *parts), encoding="utf-8") as handle:
            return handle.read()


class TestEngineerPagesComeFirst(DistributeCase):
    def test_one_page_per_engineer(self):
        self.release_engineers()
        self.assertTrue(os.path.exists(os.path.join(self.root, "engineers", "sham.md")))
        self.assertTrue(os.path.exists(os.path.join(self.root, "engineers", "nadia.md")))

    def test_manager_pages_do_not_exist_yet(self):
        self.release_engineers()
        for name in ("em.md", "founder.md"):
            self.assertFalse(os.path.exists(os.path.join(self.root, name)), name)

    def test_an_engineer_page_names_nobody_else(self):
        self.release_engineers()
        page = self.read("engineers", "sham.md")
        self.assertNotIn("nadia", page)

    def test_release_is_stamped_in_the_manifest(self):
        self.release_engineers()
        manifest = read_manifest(self.root)
        self.assertEqual(manifest["audiences_released"], ["engineer"])
        self.assertEqual(manifest["engineer_pages"], 2)
        self.assertTrue(manifest["engineer_pages_released_at"].endswith("Z"))

    def test_page_shows_raw_and_substantive_counts(self):
        self.release_engineers()
        page = self.read("engineers", "sham.md")
        self.assertIn("PRs merged: **2**", page)
        self.assertIn("substantive", page)
        self.assertIn("**1**", page)

    def test_page_shows_both_readings(self):
        self.release_engineers()
        page = self.read("engineers", "sham.md")
        self.assertIn("Most favourable reading", page)
        self.assertIn("Least favourable reading", page)

    def test_page_explains_how_to_file_a_correction(self):
        self.release_engineers()
        self.assertIn("corrections/acme-app/2026-07/",
                      self.read("engineers", "sham.md"))

    def test_page_without_interpretation_still_renders_the_numbers(self):
        distribute_engineers(self.root, self.computed, {}, self.mapping,
                             "acme/app", "2026-07", NON_SUBSTANTIVE)
        page = self.read("engineers", "sham.md")
        self.assertIn("What you shipped", page)
        self.assertIn("Not generated", page)


class TestEmbargo(DistributeCase):
    def test_manager_pages_are_refused_before_any_engineer_release(self):
        with self.assertRaises(EmbargoError) as caught:
            self.release_rest()
        self.assertIn("engineer pages have not been released", str(caught.exception))

    def test_manager_pages_are_refused_while_the_embargo_runs(self):
        self.release_engineers()
        with self.assertRaises(EmbargoError) as caught:
            self.release_rest(embargo=24)
        self.assertIn("remain", str(caught.exception))

    def test_manager_pages_are_allowed_once_the_embargo_expires(self):
        self.release_engineers()
        manifest = read_manifest(self.root)
        stale = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=30)
        manifest["engineer_pages_released_at"] = stale.isoformat().replace("+00:00", "Z")
        write_manifest(self.root, manifest)
        self.release_rest(embargo=24)
        self.assertTrue(os.path.exists(os.path.join(self.root, "em.md")))

    def test_zero_hours_disables_the_wait_but_not_the_ordering(self):
        with self.assertRaises(EmbargoError):
            check_embargo(self.root, 0)
        self.release_engineers()
        check_embargo(self.root, 0)


class TestAudienceBoundaries(DistributeCase):
    def setUp(self):
        super().setUp()
        self.release_engineers()
        self.release_rest(squads={"platform": ["sham"], "data": ["nadia"]})

    def test_founder_page_contains_no_individual(self):
        page = self.read("founder.md")
        for login in ("sham", "nadia"):
            self.assertNotIn(login, page)

    def test_founder_page_carries_team_metrics_and_risk(self):
        page = self.read("founder.md")
        self.assertIn("deployment frequency", page)
        self.assertIn("## Risk", page)

    def test_founder_risk_names_unmeasurable_metrics(self):
        self.assertIn("cannot be measured", self.read("founder.md"))

    def test_squad_page_shows_only_its_own_members(self):
        platform = self.read("squads", "platform.md")
        self.assertIn("sham", platform)
        self.assertNotIn("nadia", platform)

    def test_squad_page_includes_the_team_aggregate(self):
        self.assertIn("Team aggregate", self.read("squads", "platform.md"))

    def test_em_page_sees_everyone_and_is_framed_as_an_agenda(self):
        page = self.read("em.md")
        self.assertIn("agenda, not a verdict", page)
        self.assertIn("Questions to ask", page)
        self.assertIn("sham", page)

    def test_em_page_records_that_the_model_never_saw_the_name(self):
        self.assertIn("the model never saw the name", self.read("em.md"))

    def test_all_four_audiences_are_marked_released(self):
        self.assertEqual(read_manifest(self.root)["audiences_released"],
                         ["engineer", "em", "squad_lead", "founder"])

    def test_no_squad_config_falls_back_to_a_single_team(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        distribute_engineers(root, self.computed, self.gated, self.mapping,
                             "acme/app", "2026-07", NON_SUBSTANTIVE)
        distribute_rest(root, self.computed, self.gated, self.mapping, "acme/app",
                        "2026-07", SOURCES, {}, NON_SUBSTANTIVE, 0)
        self.assertTrue(os.path.exists(os.path.join(root, "squads", "team.md")))


class TestNoRankedListAnywhere(DistributeCase):
    def test_no_output_file_contains_a_rank_column(self):
        self.release_engineers()
        self.release_rest(squads={"platform": ["sham", "nadia"]})
        for directory, _, files in os.walk(self.root):
            for name in files:
                if not name.endswith(".md"):
                    continue
                with open(os.path.join(directory, name), encoding="utf-8") as handle:
                    text = handle.read().lower()
                self.assertNotIn("| rank |", text, name)
                self.assertNotIn("rank |", text, name)

    def test_squad_table_is_alphabetical_not_ordered_by_output(self):
        page = render_squad_page("platform", ["sham", "nadia"], self.computed,
                                 "acme/app", "2026-07", NON_SUBSTANTIVE)
        self.assertLess(page.index("| nadia |"), page.index("| sham |"))
        self.assertIn("Rows are alphabetical", page)

    def test_founder_page_states_the_individual_boundary(self):
        page = render_founder_page(self.computed, "acme/app", "2026-07", SOURCES)
        self.assertIn("No individual data appears on this page", page)


if __name__ == "__main__":
    unittest.main()
