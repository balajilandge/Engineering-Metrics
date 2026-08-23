"""Environment-driven configuration, read once at startup."""
from __future__ import annotations

import dataclasses
import os


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


def env_int(name: str, default: int) -> int:
    raw = env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def env_bool(name: str, default: bool) -> bool:
    raw = env(name).lower()
    if not raw:
        return default
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be a boolean, got {raw!r}")


def env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = env(name)
    if not raw:
        return default
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclasses.dataclass(frozen=True)
class Config:
    repo: str
    month: str
    token: str

    # Layer 1
    max_pages: int = 300
    detail_budget: int = 400          # per-PR API calls allowed per run
    board_path: str = ""
    deploys_path: str = ""
    incidents_path: str = ""
    squads_path: str = "config/squads.json"

    # Layer 2
    non_substantive: tuple[str, ...] = ("dependency", "config", "docs")

    # Layer 3
    interpret: bool = False
    model: str = "claude-opus-5"
    effort: str = "high"
    interpret_runs: int = 2           # the gate needs two runs to compare
    interpret_engineers: int = 12     # cap on how many profiles get interpreted
    max_diff_chars: int = 40_000

    # Layer 4
    embargo_hours: int = 24

    @classmethod
    def from_env(cls, repo: str, month: str) -> "Config":
        return cls(
            repo=repo,
            month=month,
            token=env("GH_TOKEN") or env("GITHUB_TOKEN"),
            max_pages=env_int("MAX_PAGES", 300),
            detail_budget=env_int("DETAIL_BUDGET", 400),
            board_path=env("BOARD_PATH"),
            deploys_path=env("DEPLOYS_PATH"),
            incidents_path=env("INCIDENTS_PATH"),
            squads_path=env("SQUADS_PATH", "config/squads.json"),
            non_substantive=env_list(
                "NON_SUBSTANTIVE_TYPES", ("dependency", "config", "docs")
            ),
            interpret=env_bool("INTERPRET", False),
            model=env("INTERPRET_MODEL", "claude-opus-5"),
            effort=env("INTERPRET_EFFORT", "high"),
            interpret_runs=env_int("INTERPRET_RUNS", 2),
            interpret_engineers=env_int("INTERPRET_ENGINEERS", 12),
            max_diff_chars=env_int("MAX_DIFF_CHARS", 40_000),
            embargo_hours=env_int("EMBARGO_HOURS", 24),
        )
