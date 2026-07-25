# SPDX-License-Identifier: Apache-2.0
"""GitHub read-only inspection jobs — on-demand repository inventory (no operational memory)."""

from __future__ import annotations

import re
from typing import Any

_GITHUB_INVENTORY_RX = re.compile(
    r"\b(show|list|what are)\b.*\b(my )?github\b.*\b(repos(?:itories)?)\b|"
    r"\b(show|list)\b.*\b(github)\b.*\b(repos(?:itories)?)\b|"
    r"\bgithub\b.*\b(repos(?:itories)?)\b.*\b(list|inventory)\b|"
    r"\b(show|list)\b.*\b(my )?repos\b.*\b(on )?github\b",
    re.I,
)

GITHUB_READONLY_JOB_TYPES = frozenset(
    {
        "github_repositories_inventory",
    }
)


def is_github_inventory_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not re.search(r"\bgithub\b", raw, re.I):
        return False
    return bool(_GITHUB_INVENTORY_RX.search(raw))


def infer_github_readonly_job(text: str) -> tuple[str, str, dict[str, Any]] | None:
    """Return (title, job_type, params) or None."""
    raw = (text or "").strip()
    if not is_github_inventory_request(raw):
        return None
    return (
        "GitHub repositories inventory",
        "github_repositories_inventory",
        {"user_request": raw, "provider": "github", "scope": "github"},
    )


def resolve_github_auth_for_chat() -> dict[str, str | None]:
    from aethos_core.providers.github.auth import GitHubAuthAdapter

    resolved = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
    method = str(resolved.get("method") or "")
    if method == "api_token":
        return {
            "auth_method": "api_token",
            "credential_id": str(resolved.get("credential_id") or ""),
            "block_reason": None,
        }
    return {
        "auth_method": None,
        "credential_id": None,
        "block_reason": "missing",
    }


def github_connect_required_reply() -> str:
    return (
        "I need a **GitHub personal access token** before I can list your repositories.\n\n"
        "Open **Mission Control → Advanced settings → Credentials → GitHub** and add a token.\n\n"
        "AethOS never asks for tokens in chat."
    )
