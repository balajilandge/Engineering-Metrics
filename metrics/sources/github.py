"""
GitHub source adapter: pull requests, the files each one touched, and the
reviews given on them.

Paging the `pulls` list endpoint (rather than the Search API) is deliberate and
unchanged from the original pipeline: Search truncates at 1,000 results and a
busy repo exceeds that in merged PRs per month.

The new cost here is per-PR detail. `additions`/`deletions`/`changed_files`
are absent from list responses, and files and reviews have no repo-wide
endpoint at all — so each is one call per PR. `detail_budget` caps how many
PRs get that treatment; PRs beyond the cap keep their list-level fields and
are marked `detailed: False`, which downstream layers treat as missing
evidence rather than as zeros.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from .base import Availability, SourceStatus

API_ROOT = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, max_pages: int = 300):
        self.token = token
        self.max_pages = max_pages
        self.calls = 0
        # Per-PR detail is fetched from a thread pool, so the counter needs a
        # lock to stay an accurate record of how much of the budget was spent.
        self._calls_lock = threading.Lock()

    def get(self, path_and_query: str) -> list | dict:
        url = f"{API_ROOT}{path_and_query}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "engineering-metrics-pipeline",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(url, headers=headers)
        for attempt in range(1, 6):
            try:
                with self._calls_lock:
                    self.calls += 1
                with urllib.request.urlopen(request, timeout=30) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code in (403, 429) and attempt < 5:
                    wait = int(exc.headers.get("Retry-After", "0")) or (2 ** attempt)
                    print(f"  rate limited (HTTP {exc.code}), retrying in {wait}s...",
                          file=sys.stderr)
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"Failed to fetch {url} after retries")

    def paged_pulls(
        self,
        repo: str,
        state: str,
        sort: str,
        sort_field: str,
        start_iso: str,
        end_iso: str,
        filter_field: str | None = None,
    ) -> list[dict]:
        """
        Pages `/repos/{repo}/pulls` sorted desc, stopping once items fall
        before `start_iso`. Returns items whose `filter_field` is inside the
        window.
        """
        filter_field = filter_field or sort_field
        matched: list[dict] = []
        page = 1
        while page <= self.max_pages:
            path = (f"/repos/{repo}/pulls?state={state}&sort={sort}"
                    f"&direction=desc&per_page=100&page={page}")
            batch = self.get(path)
            if not batch:
                break

            reached_start = False
            for item in batch:
                sort_value = item.get(sort_field)
                if sort_value is None:
                    continue
                if sort_value < start_iso:
                    reached_start = True
                    break
                filter_value = item.get(filter_field)
                if filter_value is not None and start_iso <= filter_value <= end_iso:
                    matched.append(item)

            if reached_start or len(batch) < 100:
                break
            page += 1
            time.sleep(0.2)
        else:
            print(f"  warning: hit max_pages={self.max_pages} scanning {repo} "
                  f"pulls (state={state}, sort={sort})", file=sys.stderr)
        return matched

    def pull_detail(self, repo: str, number: int) -> dict:
        return self.get(f"/repos/{repo}/pulls/{number}")

    def pull_files(self, repo: str, number: int, per_page: int = 100) -> list[dict]:
        return self.get(f"/repos/{repo}/pulls/{number}/files?per_page={per_page}")

    def pull_reviews(self, repo: str, number: int, per_page: int = 100) -> list[dict]:
        return self.get(f"/repos/{repo}/pulls/{number}/reviews?per_page={per_page}")

    def pull_review_comments(self, repo: str, number: int, per_page: int = 100) -> list[dict]:
        return self.get(f"/repos/{repo}/pulls/{number}/comments?per_page={per_page}")


def is_bot(user: dict | None) -> bool:
    if not user:
        return True
    if user.get("type") == "Bot":
        return True
    return str(user.get("login", "")).endswith("[bot]")


def status_for(pulls: list[dict], token: str) -> SourceStatus:
    if not token:
        detail = "no token; anonymous rate limits apply"
    else:
        detail = f"{len(pulls)} pull requests in window"
    if not pulls:
        return SourceStatus("pull_requests", Availability.EMPTY, detail)
    return SourceStatus("pull_requests", Availability.OK, detail)
