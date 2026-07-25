# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — GitHub pull request open mutation."""

from __future__ import annotations

import os
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


def find_open_pull_request(
    token: str,
    *,
    owner: str,
    repo: str,
    head: str,
    base: str,
) -> dict[str, Any]:
    if _certification_mode():
        return {
            "ok": True,
            "url": f"https://github.com/{owner}/{repo}/pull/1",
            "number": 1,
            "simulated": True,
        }
    result = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/pulls",
        params={"head": f"{owner}:{head}", "base": base, "state": "open"},
    )
    if result.get("ok"):
        data = result.get("data")
        if isinstance(data, list) and data:
            pr = data[0]
            return {
                "ok": True,
                "url": pr.get("html_url"),
                "number": pr.get("number"),
                "idempotent": True,
            }
    return {"ok": False}


def open_governed_pull_request(
    *,
    token: str,
    repository: str,
    head: str,
    base: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "error": "invalid_repository"}

    if _certification_mode():
        return {
            "ok": True,
            "url": f"https://github.com/{owner}/{repo}/pull/125",
            "number": 125,
            "simulated": True,
        }

    result = request_github(
        token,
        "POST",
        f"/repos/{owner}/{repo}/pulls",
        json_body={"title": title, "body": body, "head": head, "base": base},
    )
    if result.get("ok"):
        data = result.get("data") or {}
        if isinstance(data, dict):
            return {
                "ok": True,
                "url": data.get("html_url"),
                "number": data.get("number"),
            }
        return {"ok": False, "error": "unexpected_response"}

    error_text = str(result.get("error") or "")
    if result.get("http_status") == 422 and "already exists" in error_text.lower():
        existing = find_open_pull_request(token, owner=owner, repo=repo, head=head, base=base)
        if existing.get("ok"):
            existing["already_exists"] = True
            return existing
    return {"ok": False, "error": error_text, "already_exists": False}
