#!/usr/bin/env python3
"""
Monthly PR metrics generator.

Queries the GitHub REST API for a target repository (default:
microsoft/vscode) and, for a given calendar month, computes per-engineer
(PR author) counts of PRs created and PRs merged, then writes:

  - data/<repo-slug>/<YYYY-MM>.json   machine-readable results
  - reports/<repo-slug>/<YYYY-MM>.md  human-readable leaderboard
  - reports/<repo-slug>/latest.md     pointer/copy of the newest report

Uses the paginated `/repos/{owner}/{repo}/pulls` list endpoint (sorted by
created/updated) rather than the Search API, since Search caps results at
1000 items and a high-traffic repo like microsoft/vscode comfortably
exceeds that in merged PRs per month.

Configuration is via environment variables so the same script can be
invoked from a GitHub Actions workflow or run locally:

  SOURCE_REPO   "owner/name" of the repo to read stats from (default microsoft/vscode)
  TARGET_MONTH  "YYYY-MM" to report on (default: previous calendar month, UTC)
  GH_TOKEN      token used for GitHub API auth (optional but recommended)
  TOP_N         how many rows to show in the month-detail table (default 25)
  TREND_MONTHS  how many months wide the "Merged PRs by month" table is (default 3)
  TREND_TOP_N   how many rows to show in that table (default 15)

The trend table reads earlier months back from the JSON files previous runs
committed, so no extra API calls are made for history.
"""
from __future__ import annotations

import calendar
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

API_ROOT = "https://api.github.com"
MAX_PAGES = 300  # safety cap: 300 pages * 100/page = 30,000 PRs scanned


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


def previous_month(today: datetime.date) -> str:
    first_of_this_month = today.replace(day=1)
    last_of_prev_month = first_of_this_month - datetime.timedelta(days=1)
    return last_of_prev_month.strftime("%Y-%m")


def month_bounds(year_month: str) -> tuple[str, str]:
    """Returns (start_iso, end_iso) covering the full UTC calendar month."""
    year, month = (int(part) for part in year_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    start_iso = f"{year:04d}-{month:02d}-01T00:00:00Z"
    end_iso = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z"
    return start_iso, end_iso


def api_get(path_and_query: str, token: str) -> list | dict:
    url = f"{API_ROOT}{path_and_query}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "engineering-metrics-action",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429) and attempt < 5:
                wait = int(exc.headers.get("Retry-After", "0")) or (2 ** attempt)
                print(f"  rate limited (HTTP {exc.code}), retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url} after retries")


def list_repo_pulls(
    repo: str,
    token: str,
    state: str,
    sort: str,
    sort_field: str,
    start_iso: str,
    end_iso: str,
    filter_field: str | None = None,
) -> list[dict]:
    """
    Pages through /repos/{repo}/pulls sorted desc by `sort`, stopping once
    items fall before `start_iso` (safe because the list is sorted desc by
    `sort_field`). Returns items whose `filter_field` (defaults to
    `sort_field`) falls within [start_iso, end_iso].
    """
    filter_field = filter_field or sort_field
    matched: list[dict] = []
    page = 1
    while page <= MAX_PAGES:
        path = f"/repos/{repo}/pulls?state={state}&sort={sort}&direction=desc&per_page=100&page={page}"
        batch = api_get(path, token)
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
        print(f"  warning: hit MAX_PAGES={MAX_PAGES} while scanning {repo} pulls (state={state}, sort={sort})", file=sys.stderr)

    return matched


def is_bot(user: dict) -> bool:
    if not user:
        return True
    if user.get("type") == "Bot":
        return True
    return user.get("login", "").endswith("[bot]")


def build_leaderboard(created_items: list[dict], merged_items: list[dict]) -> list[dict]:
    created_counts: Counter[str] = Counter()
    merged_counts: Counter[str] = Counter()
    profile_urls: dict[str, str] = {}

    for item in created_items:
        user = item.get("user") or {}
        if is_bot(user):
            continue
        login = user.get("login")
        created_counts[login] += 1
        profile_urls.setdefault(login, user.get("html_url", ""))

    for item in merged_items:
        user = item.get("user") or {}
        if is_bot(user):
            continue
        login = user.get("login")
        merged_counts[login] += 1
        profile_urls.setdefault(login, user.get("html_url", ""))

    logins = set(created_counts) | set(merged_counts)
    rows = [
        {
            "engineer": login,
            "profile_url": profile_urls.get(login, ""),
            "prs_created": created_counts.get(login, 0),
            "prs_merged": merged_counts.get(login, 0),
        }
        for login in logins
    ]
    rows.sort(key=lambda r: (-r["prs_merged"], -r["prs_created"], r["engineer"].lower()))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows


def month_label(year_month: str) -> str:
    """'2026-07' -> 'Jul'."""
    year, month = (int(part) for part in year_month.split("-"))
    return calendar.month_abbr[month]


def trailing_months(year_month: str, count: int) -> list[str]:
    """['2026-05', '2026-06', '2026-07'] for ('2026-07', 3) — oldest first."""
    year, month = (int(part) for part in year_month.split("-"))
    months = []
    for offset in range(count - 1, -1, -1):
        total = (year * 12 + (month - 1)) - offset
        months.append(f"{total // 12:04d}-{total % 12 + 1:02d}")
    return months


def load_month_leaderboard(data_dir: str, year_month: str) -> dict[str, dict] | None:
    """Reads a previously generated month's JSON, keyed by engineer. None if absent."""
    path = os.path.join(data_dir, f"{year_month}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return {row["engineer"]: row for row in payload.get("leaderboard", [])}


def render_trend_markdown(
    repo: str,
    target_month: str,
    months: list[str],
    by_month: dict[str, dict[str, dict] | None],
    top_n: int,
) -> str:
    """
    Renders the "Merged PRs by month" view: one row per engineer, one column
    per month, ranked by merged PRs in the target month.

    A month we have no data file for renders as a blank column; an engineer
    absent from a month we *do* have renders as an em dash, meaning no merged
    PRs that month (they may not have joined yet).
    """
    target = by_month.get(target_month) or {}
    ranked = sorted(
        target.values(),
        key=lambda r: (-r["prs_merged"], -r["prs_created"], r["engineer"].lower()),
    )[:top_n]

    labels = [month_label(m) for m in months]
    header = "| Engineer | " + " | ".join(labels) + f" | {month_label(target_month)} rank |"
    divider = "|---|" + "|".join(["---:"] * len(labels)) + "|---:|"
    lines = [
        f"## Merged PRs by month — {repo}",
        "",
        header,
        divider,
    ]

    for rank, row in enumerate(ranked, start=1):
        engineer = row["engineer"]
        cells = []
        for month in months:
            month_data = by_month.get(month)
            if month_data is None:
                cells.append("")  # no data file for this month yet
            elif engineer in month_data:
                cells.append(str(month_data[engineer]["prs_merged"]))
            else:
                cells.append("—")
        link = f"[{engineer}]({row['profile_url']})" if row.get("profile_url") else engineer
        lines.append(f"| {link} | " + " | ".join(cells) + f" | {rank} |")

    missing = [m for m in months if by_month.get(m) is None]
    if missing:
        lines.append("")
        lines.append(
            "_No data yet for: " + ", ".join(missing) +
            ". Run the workflow with that `month` input to backfill._"
        )
    lines.append("")
    return "\n".join(lines)


def render_markdown(
    repo: str,
    year_month: str,
    leaderboard: list[dict],
    top_n: int,
    trend_section: str = "",
) -> str:
    total_created = sum(r["prs_created"] for r in leaderboard)
    total_merged = sum(r["prs_merged"] for r in leaderboard)
    lines = [
        f"# Monthly Engineering Metrics — {repo} — {year_month}",
        "",
        f"- Source repo: [{repo}](https://github.com/{repo}) (read-only)",
        f"- Period: {year_month} (UTC calendar month)",
        f"- Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- Engineers with activity: {len(leaderboard)}",
        f"- Total PRs created: {total_created}",
        f"- Total PRs merged: {total_merged}",
        "",
    ]
    if trend_section:
        lines.append(trend_section)
    lines += [
        f"## {year_month} detail (ranked by PRs merged)",
        "",
        "| Rank | Engineer | PRs Created | PRs Merged |",
        "|---:|---|---:|---:|",
    ]
    for row in leaderboard[:top_n]:
        engineer_cell = f"[{row['engineer']}]({row['profile_url']})" if row["profile_url"] else row["engineer"]
        lines.append(f"| {row['rank']} | {engineer_cell} | {row['prs_created']} | {row['prs_merged']} |")

    if len(leaderboard) > top_n:
        lines.append("")
        lines.append(f"_Showing top {top_n} of {len(leaderboard)} engineers. Full data in the matching JSON file under `data/`._")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    repo = env("SOURCE_REPO", "microsoft/vscode")
    token = env("GH_TOKEN") or env("GITHUB_TOKEN")
    top_n = int(env("TOP_N", "25"))
    trend_months = int(env("TREND_MONTHS", "3"))
    trend_top_n = int(env("TREND_TOP_N", "15"))

    target_month = env("TARGET_MONTH")
    if not target_month:
        target_month = previous_month(datetime.datetime.now(datetime.timezone.utc).date())

    start_iso, end_iso = month_bounds(target_month)
    print(f"Fetching PR metrics for {repo}, {target_month} ({start_iso}..{end_iso})")

    created_items = list_repo_pulls(
        repo, token, state="all", sort="created", sort_field="created_at",
        start_iso=start_iso, end_iso=end_iso,
    )
    print(f"  created PRs found: {len(created_items)}")

    merged_items = list_repo_pulls(
        repo, token, state="closed", sort="updated", sort_field="updated_at",
        filter_field="merged_at", start_iso=start_iso, end_iso=end_iso,
    )
    print(f"  merged PRs found: {len(merged_items)}")

    leaderboard = build_leaderboard(created_items, merged_items)

    repo_slug = repo.replace("/", "-")
    data_dir = os.path.join("data", repo_slug)
    reports_dir = os.path.join("reports", repo_slug)
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    result = {
        "repo": repo,
        "month": target_month,
        "period": {"start": start_iso, "end": end_iso},
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "totals": {
            "prs_created": sum(r["prs_created"] for r in leaderboard),
            "prs_merged": sum(r["prs_merged"] for r in leaderboard),
            "engineers": len(leaderboard),
        },
        "leaderboard": leaderboard,
    }

    data_path = os.path.join(data_dir, f"{target_month}.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    # Trend view: this month plus the preceding TREND_MONTHS-1 months, read
    # back from the JSON files previous runs committed.
    months = trailing_months(target_month, trend_months)
    by_month: dict[str, dict[str, dict] | None] = {}
    for month in months:
        if month == target_month:
            by_month[month] = {row["engineer"]: row for row in leaderboard}
        else:
            by_month[month] = load_month_leaderboard(data_dir, month)

    trend_markdown = render_trend_markdown(repo, target_month, months, by_month, trend_top_n)
    markdown = render_markdown(repo, target_month, leaderboard, top_n, trend_markdown)

    report_path = os.path.join(reports_dir, f"{target_month}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    latest_path = os.path.join(reports_dir, "latest.md")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Wrote {data_path}")
    print(f"Wrote {report_path}")
    print(f"Wrote {latest_path}")


if __name__ == "__main__":
    main()
