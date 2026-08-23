"""
The Layer 2 -> Layer 3 arrow: names stripped, Engineer A, B, C.

The model never sees a login, a display name, a profile URL or an avatar. It
sees "Engineer A" and that engineer's own numbers and diffs. This is not
decoration: it removes the model's ability to draw on anything it might
associate with a real person's name, and it means a leaked Layer 3 payload
identifies nobody.

Letters are assigned by a salted hash of the login, not alphabetically and not
by volume, so the label ordering itself carries no signal. The salt is derived
from repo and month, so a re-run of the same month produces the same mapping
(stable diffs) while the same person gets a different letter next month.
"""
from __future__ import annotations

import copy
import hashlib
import re
import string

# Anything in a PR title or diff that looks like an @mention or a GitHub URL
# is scrubbed too — a name in free text leaks just as effectively as a field.
_MENTION = re.compile(r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
_PROFILE_URL = re.compile(r"https?://github\.com/([A-Za-z0-9-]+)(?=[/\s)\]]|$)")


def _label(index: int) -> str:
    """0 -> 'Engineer A', 25 -> 'Engineer Z', 26 -> 'Engineer AA'."""
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = string.ascii_uppercase[remainder] + letters
    return f"Engineer {letters}"


def build_mapping(logins: list[str], salt: str) -> dict[str, str]:
    ordered = sorted(
        set(logins),
        key=lambda login: hashlib.sha256(f"{salt}:{login}".encode()).hexdigest(),
    )
    return {login: _label(i) for i, login in enumerate(ordered)}


def scrub_text(text: str, mapping: dict[str, str]) -> str:
    """Replaces known logins in free text; unknown handles are redacted."""
    if not text:
        return text

    lowered = {login.lower(): label for login, label in mapping.items()}

    def replace_mention(match: re.Match) -> str:
        handle = match.group(0)[1:]
        return lowered.get(handle.lower(), "@[redacted]")

    def replace_url(match: re.Match) -> str:
        return lowered.get(match.group(1).lower(), "[redacted profile]")

    text = _PROFILE_URL.sub(replace_url, text)
    text = _MENTION.sub(replace_mention, text)
    for login, label in mapping.items():
        text = re.sub(rf"\b{re.escape(login)}\b", label, text, flags=re.IGNORECASE)
    return text


# Keys carrying identity that must never cross the arrow.
_IDENTITY_KEYS = ("profile_url", "author_url", "avatar_url", "email", "name")


def anonymize_profile(profile: dict, mapping: dict[str, str]) -> dict:
    """Returns a copy safe to send to Layer 3."""
    clean = copy.deepcopy(profile)
    login = clean.get("engineer", "")
    clean["engineer"] = mapping.get(login, "Engineer ?")

    for key in _IDENTITY_KEYS:
        clean.pop(key, None)

    for item in clean.get("evidence_prs", []):
        item.pop("url", None)
        item["title"] = scrub_text(item.get("title", ""), mapping)

    return clean


def anonymize_diff(diff: str, mapping: dict[str, str]) -> str:
    return scrub_text(diff, mapping)


def verify_anonymized(payload, mapping: dict[str, str]) -> None:
    """
    Belt and braces before the only network call that leaves the building:
    walk the payload and fail if any known login survives anywhere in it.
    """
    logins = [login for login in mapping if login]
    pattern = re.compile("|".join(rf"\b{re.escape(login)}\b" for login in logins),
                         re.IGNORECASE) if logins else None
    if pattern is None:
        return

    def walk(node, path="$"):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in _IDENTITY_KEYS:
                    raise ValueError(f"identity key {path}.{key} survived anonymization")
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")
        elif isinstance(node, str):
            found = pattern.search(node)
            if found:
                raise ValueError(
                    f"login {found.group(0)!r} survived anonymization at {path}")

    walk(payload)
