"""
Layer 1 — PR type classification. Deterministic, no model.

Every PR gets exactly one type, decided in this priority order:

    dependency -> config -> docs -> test -> fix -> feature

The first five are decided by the *filenames* a PR touches, which is why the
result is not arguable: given the same file list, the rule always returns the
same type. `fix` vs `feature` is the leftover bucket — filenames cannot tell
those apart, so the title's conventional-commit prefix decides, and a PR whose
title says nothing lands in `feature`.

Each file is categorised on its own, by the first rule that matches it in
priority order. The PR then takes the category most of its files fall into,
ties broken by the same priority order — so a lockfile bump that also edits a
changelog is a dependency PR, not a docs PR and certainly not a feature.

One file type overrides all of this: source. A PR touching any file that no
filename rule claims is real code, so it falls through to the fix/feature
split — which is why `src/parser.py` plus `test/parser_test.py` is a feature,
not a test PR.
"""
from __future__ import annotations

import posixpath
import re
from collections import Counter

# The full, ordered set of types. Order is the classification priority.
PR_TYPES = ("dependency", "config", "docs", "test", "fix", "feature")

# Exact basenames that mean "this PR moves dependencies around".
_DEPENDENCY_FILES = frozenset({
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
    "pnpm-lock.yaml", "bun.lockb", "requirements.txt", "requirements-dev.txt",
    "pipfile", "pipfile.lock", "poetry.lock", "pyproject.toml", "setup.cfg",
    "go.mod", "go.sum", "cargo.toml", "cargo.lock", "gemfile", "gemfile.lock",
    "composer.json", "composer.lock", "pom.xml", "build.gradle",
    "build.gradle.kts", "gradle.lockfile", "packages.lock.json", "podfile.lock",
    "flake.lock", "vendor.json",
})

_CONFIG_SUFFIXES = (".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf",
                    ".properties", ".tfvars", ".tf", ".env")
_CONFIG_FILES = frozenset({
    "dockerfile", "makefile", ".gitignore", ".gitattributes", ".dockerignore",
    ".editorconfig", ".eslintrc", ".eslintrc.json", ".prettierrc",
    ".pre-commit-config.yaml", "docker-compose.yml", "docker-compose.yaml",
})
_CONFIG_DIRS = (".github/", ".circleci/", ".devcontainer/", "ci/", "deploy/",
                "charts/", "helm/", "k8s/", "terraform/", "infra/")

_DOC_SUFFIXES = (".md", ".mdx", ".rst", ".txt", ".adoc", ".png", ".jpg",
                 ".jpeg", ".gif", ".svg")
_DOC_DIRS = ("docs/", "doc/", "documentation/", "website/", "examples/")

_TEST_DIRS = ("test/", "tests/", "spec/", "specs/", "__tests__/", "e2e/",
              "integration-tests/", "testdata/", "fixtures/")
_TEST_NAME = re.compile(
    r"(^|[._-])(test|tests|spec|specs)([._-]|$)|_test\.|\.test\.|\.spec\."
)

# Conventional-commit and plain-English markers for the fix/feature split.
_FIX_TITLE = re.compile(
    r"^\s*(fix|bugfix|hotfix|patch|revert)\b|^\s*fix\s*[(:\[]"
    r"|\b(bug ?fix|regression|hotfix)\b",
    re.IGNORECASE,
)
_REVERT_TITLE = re.compile(r"^\s*revert\b|\brevert(s|ed)?\s+(commit|pr|#)",
                           re.IGNORECASE)


def _norm(path: str) -> str:
    return posixpath.normpath(path.strip().lstrip("/")).lower()


def _in_dirs(path: str, dirs: tuple[str, ...]) -> bool:
    return any(path.startswith(d) or f"/{d}" in f"/{path}" for d in dirs)


def is_dependency_file(path: str) -> bool:
    path = _norm(path)
    base = posixpath.basename(path)
    if base in _DEPENDENCY_FILES:
        return True
    return path.startswith("vendor/") or "/vendor/" in path


def is_config_file(path: str) -> bool:
    path = _norm(path)
    base = posixpath.basename(path)
    if base in _CONFIG_FILES or base.startswith("dockerfile"):
        return True
    if _in_dirs(path, _CONFIG_DIRS):
        return True
    if base.endswith(_CONFIG_SUFFIXES):
        return True
    # A dotfile at any level is config, unless it is really documentation.
    return base.startswith(".") and not base.endswith(_DOC_SUFFIXES)


def is_doc_file(path: str) -> bool:
    path = _norm(path)
    return posixpath.basename(path).endswith(_DOC_SUFFIXES) or _in_dirs(path, _DOC_DIRS)


def is_test_file(path: str) -> bool:
    path = _norm(path)
    if _in_dirs(path, _TEST_DIRS):
        return True
    return bool(_TEST_NAME.search(posixpath.basename(path)))


_FILE_RULES = (
    ("dependency", is_dependency_file),
    ("config", is_config_file),
    ("docs", is_doc_file),
    ("test", is_test_file),
)

_FILE_RULE_ORDER = {pr_type: i for i, (pr_type, _) in enumerate(_FILE_RULES)}


def classify_file(path: str) -> str | None:
    """One file's category, or None when no rule claims it (i.e. it is source)."""
    for pr_type, rule in _FILE_RULES:
        if rule(path):
            return pr_type
    return None


def classify_files(paths: list[str]) -> str | None:
    """
    Returns the filename-derived type, or None when the PR touches any source
    file — in which case it falls through to the fix/feature split.

    With no source file present, the winning category is the one holding the
    most files; a tie goes to the higher-priority category, so the result never
    depends on dict or filesystem ordering.
    """
    if not paths:
        return None

    categories = [classify_file(path) for path in paths]
    if any(category is None for category in categories):
        return None

    counts = Counter(categories)
    return min(counts, key=lambda t: (-counts[t], _FILE_RULE_ORDER[t]))


def classify_title(title: str) -> str:
    """The fix/feature split, decided by the title. `feature` is the default."""
    return "fix" if _FIX_TITLE.search(title or "") else "feature"


def classify_pr(title: str, paths: list[str]) -> str:
    """
    The full rule. `paths` empty (file list unavailable within the API budget)
    falls back to the title split, which is the honest degradation: we say
    feature/fix rather than inventing a filename-derived answer.
    """
    return classify_files(paths) or classify_title(title)


def is_revert(title: str, body: str = "") -> bool:
    """Reverts are counted separately; they keep whatever type their files say."""
    return bool(_REVERT_TITLE.search(title or "") or
                _REVERT_TITLE.search((body or "").split("\n")[0]))


def substantive_types(non_substantive: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(t for t in PR_TYPES if t not in set(non_substantive))
