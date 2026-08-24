"""
Layer 1 fans the per-PR detail fetch out across a thread pool. The layer's
contract is that it is deterministic — "a re-run on the same data produces the
same split" — so the pool must not change the result, only the wall clock.
"""
import contextlib
import json
import threading
import time
import unittest

from metrics import collect as collect_module
from metrics.collect import collect
from metrics.config import Config


class FakeClient:
    """Stands in for GitHubClient with fixed, deterministic responses."""

    def __init__(self, pulls):
        self._pulls = pulls
        self.calls = 0
        self._lock = threading.Lock()
        self.max_concurrent = 0
        self._in_flight = 0

    @contextlib.contextmanager
    def _count(self):
        with self._lock:
            self.calls += 1
            self._in_flight += 1
            self.max_concurrent = max(self.max_concurrent, self._in_flight)
        try:
            # Stand in for network latency, so overlapping calls are actually
            # observable rather than finishing before the next one starts.
            time.sleep(0.005)
            yield
        finally:
            with self._lock:
                self._in_flight -= 1

    def paged_pulls(self, repo, state, sort, sort_field, start_iso, end_iso,
                    filter_field=None):
        with self._count():
            field = filter_field or sort_field
            return [p for p in self._pulls
                    if p.get(field) and start_iso <= p[field] <= end_iso]

    def pull_detail(self, repo, number):
        with self._count():
            return {"additions": number, "deletions": number * 2,
                    "changed_files": number % 5 + 1}

    def pull_files(self, repo, number):
        with self._count():
            return [{"filename": f"src/module_{number}.py"},
                    {"filename": f"tests/test_module_{number}.py"}]

    def pull_reviews(self, repo, number):
        with self._count():
            return [{"user": {"login": f"reviewer{number % 3}", "type": "User"},
                     "state": "APPROVED" if number % 2 else "CHANGES_REQUESTED",
                     "submitted_at":
                         f"2026-07-{(number % 27) + 1:02d}T12:00:00Z"}]

    def get(self, path):
        with self._count():
            return []


def _pulls(count):
    out = []
    for n in range(1, count + 1):
        day = (n % 27) + 1
        out.append({
            "number": n,
            "title": f"Add feature {n}",
            "user": {"login": f"eng{n % 7}", "type": "User",
                     "html_url": f"https://github.com/eng{n % 7}"},
            "html_url": f"https://example.invalid/pr/{n}",
            "created_at": f"2026-07-{day:02d}T09:00:00Z",
            "merged_at": f"2026-07-{day:02d}T17:00:00Z" if n % 3 else None,
            "closed_at": f"2026-07-{day:02d}T17:00:00Z" if n % 3 else None,
            "updated_at": f"2026-07-{day:02d}T17:00:00Z",
            "draft": False,
        })
    return out


class ParallelEnrichmentTest(unittest.TestCase):
    def _run_with(self, workers, pulls):
        config = Config(repo="owner/repo", month="2026-07", token="t",
                        detail_workers=workers)
        client = FakeClient(pulls)
        original = collect_module.github_source.GitHubClient
        collect_module.github_source.GitHubClient = lambda *a, **k: client
        try:
            return collect(config).to_dict(), client
        finally:
            collect_module.github_source.GitHubClient = original

    def test_parallel_matches_serial_exactly(self):
        pulls = _pulls(40)
        serial, serial_client = self._run_with(1, pulls)
        parallel, parallel_client = self._run_with(8, pulls)

        self.assertEqual(json.dumps(serial, sort_keys=True),
                         json.dumps(parallel, sort_keys=True))
        self.assertEqual(serial_client.calls, parallel_client.calls,
                         "the pool must not change how much budget is spent")

    def test_pool_actually_overlaps_requests(self):
        _, client = self._run_with(8, _pulls(40))
        self.assertGreater(client.max_concurrent, 1,
                           "enrichment did not run concurrently")

    def test_single_worker_stays_serial(self):
        _, client = self._run_with(1, _pulls(20))
        self.assertEqual(client.max_concurrent, 1)

    def test_budget_is_still_respected(self):
        config = Config(repo="owner/repo", month="2026-07", token="t",
                        detail_budget=5, detail_workers=8)
        client = FakeClient(_pulls(30))
        original = collect_module.github_source.GitHubClient
        collect_module.github_source.GitHubClient = lambda *a, **k: client
        try:
            result = collect(config)
        finally:
            collect_module.github_source.GitHubClient = original
        detailed = sum(1 for r in {p.number: p for p in
                                   result.created + result.merged}.values()
                       if r.detailed)
        self.assertEqual(detailed, 5)


if __name__ == "__main__":
    unittest.main()
