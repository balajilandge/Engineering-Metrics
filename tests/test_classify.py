"""Layer 1 — the filename rule. Same files in, same type out, every time."""
import unittest

from tests.helpers import *  # noqa: F401,F403 - sets up sys.path
from metrics.classify import (PR_TYPES, classify_files, classify_pr,
                              classify_title, is_revert, substantive_types)


class TestFilenameRule(unittest.TestCase):
    def test_lockfiles_are_dependency(self):
        for files in (["package-lock.json"], ["go.sum", "go.mod"],
                      ["poetry.lock"], ["vendor/github.com/x/y.go"]):
            self.assertEqual(classify_pr("Bump things", files), "dependency", files)

    def test_ci_and_infra_are_config(self):
        for files in ([".github/workflows/ci.yml"], ["Dockerfile"],
                      ["terraform/main.tf"], [".gitignore"]):
            self.assertEqual(classify_pr("Update", files), "config", files)

    def test_markdown_and_images_are_docs(self):
        self.assertEqual(classify_pr("Update guide", ["docs/a.md", "README.md"]), "docs")
        self.assertEqual(classify_pr("Add diagram", ["docs/arch.png"]), "docs")

    def test_test_files_are_test(self):
        for files in (["tests/test_parser.py"], ["src/parser_test.go"],
                      ["__tests__/ui.spec.ts"], ["e2e/checkout.js"]):
            self.assertEqual(classify_pr("Cover the parser", files), "test", files)

    def test_priority_highest_matching_rule_wins(self):
        # A lockfile bump that also touches a doc is a dependency PR.
        self.assertEqual(
            classify_pr("Bump and note it", ["package-lock.json", "CHANGELOG.md"]),
            "dependency")

    def test_rule_requires_every_file_to_match(self):
        # Source alongside tests means it is not a test PR.
        self.assertIsNone(classify_files(["src/parser.py", "tests/test_parser.py"]))
        self.assertEqual(
            classify_pr("Add parser", ["src/parser.py", "tests/test_parser.py"]),
            "feature")

    def test_source_falls_through_to_title(self):
        self.assertEqual(classify_pr("fix: null deref", ["src/a.py"]), "fix")
        self.assertEqual(classify_pr("Add dark mode", ["src/a.py"]), "feature")

    def test_no_files_degrades_to_title_not_to_a_guess(self):
        self.assertEqual(classify_pr("fix: broken link", []), "fix")
        self.assertEqual(classify_pr("Ship the thing", []), "feature")

    def test_every_pr_gets_exactly_one_known_type(self):
        for files in ([], ["a.md"], ["src/x.py"], ["package.json"]):
            self.assertIn(classify_pr("whatever", files), PR_TYPES)

    def test_classification_is_deterministic(self):
        files = ["src/a.py", "docs/b.md", "package.json"]
        first = classify_pr("Mixed bag", files)
        for _ in range(50):
            self.assertEqual(classify_pr("Mixed bag", files), first)


class TestTitleSplit(unittest.TestCase):
    def test_fix_markers(self):
        for title in ("fix: x", "Fix(parser): x", "hotfix for y",
                      "Bugfix: z", "resolve regression in a"):
            self.assertEqual(classify_title(title), "fix", title)

    def test_feature_is_the_default(self):
        for title in ("Add streaming", "Refactor ingest", ""):
            self.assertEqual(classify_title(title), "feature", title)


class TestReverts(unittest.TestCase):
    def test_detects_github_revert_titles(self):
        self.assertTrue(is_revert('Revert "Add streaming ingest"'))
        self.assertTrue(is_revert("revert commit abc123"))

    def test_does_not_flag_unrelated_titles(self):
        self.assertFalse(is_revert("Add revertible migration step"))


class TestSubstantive(unittest.TestCase):
    def test_deflation_excludes_configured_types(self):
        self.assertEqual(substantive_types(("dependency", "config", "docs")),
                         ("test", "fix", "feature"))

    def test_the_deflation_is_configurable(self):
        self.assertEqual(substantive_types(("docs",)),
                         ("dependency", "config", "test", "fix", "feature"))


if __name__ == "__main__":
    unittest.main()
