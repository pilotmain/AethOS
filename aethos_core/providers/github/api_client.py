# SPDX-License-Identifier: Apache-2.0
"""GitHub API client — token verification and read-only inventory."""

from __future__ import annotations

import httpx

from aethos_core.security.secret_redaction import redact_text

_GITHUB_API = "https://api.github.com"
_MAX_REPO_PAGES = 3


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def test_connection(token: str) -> dict[str, object]:
    if not token.strip():
        return {"ok": False, "detail": "Token is empty."}
    headers = _auth_headers(token)
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(f"{_GITHUB_API}/user", headers=headers)
        if r.status_code >= 400:
            detail = redact_text(r.text[:200] or f"HTTP {r.status_code}")
            return {"ok": False, "detail": detail}
        data = r.json() if r.content else {}
        login = str(data.get("login") or "")
        return {
            "ok": True,
            "detail": f"GitHub account verified{f' (@{login})' if login else ''}.",
            "account_login": login or None,
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc))}


def list_repositories(token: str) -> dict[str, object]:
    """List repositories visible to the authenticated user (paginated, capped)."""
    if not token.strip():
        return {"ok": False, "repositories": [], "error": "Token is empty."}
    headers = _auth_headers(token)
    repositories: list[dict[str, object]] = []
    try:
        with httpx.Client(timeout=30.0) as client:
            for page in range(1, _MAX_REPO_PAGES + 1):
                r = client.get(
                    f"{_GITHUB_API}/user/repos",
                    headers=headers,
                    params={
                        "affiliation": "owner,collaborator,organization_member",
                        "per_page": 100,
                        "page": page,
                        "sort": "updated",
                        "direction": "desc",
                    },
                )
                if r.status_code >= 400:
                    detail = redact_text(r.text[:240] or f"HTTP {r.status_code}")
                    return {"ok": False, "repositories": [], "error": detail}
                batch = r.json() if r.content else []
                if not isinstance(batch, list) or not batch:
                    break
                for repo in batch:
                    if not isinstance(repo, dict):
                        continue
                    owner = repo.get("owner") if isinstance(repo.get("owner"), dict) else {}
                    repositories.append(
                        {
                            "repo_id": repo.get("id"),
                            "name": str(repo.get("name") or ""),
                            "full_name": str(repo.get("full_name") or ""),
                            "owner": str(owner.get("login") or ""),
                            "private": bool(repo.get("private")),
                            "default_branch": str(repo.get("default_branch") or ""),
                            "html_url": str(repo.get("html_url") or ""),
                            "updated_at": str(repo.get("updated_at") or ""),
                        }
                    )
                if len(batch) < 100:
                    break
        return {"ok": True, "repositories": repositories, "error": None}
    except httpx.HTTPError as exc:
        return {"ok": False, "repositories": [], "error": redact_text(str(exc))}


def request_github(
    token: str,
    method: str,
    path: str,
    *,
    params: dict[str, object] | None = None,
    json_body: dict[str, object] | None = None,
) -> dict[str, object]:
    if not token.strip():
        return {"ok": False, "error": "Token is empty.", "data": None}
    url = path if path.startswith("http") else f"{_GITHUB_API}{path if path.startswith('/') else '/' + path}"
    headers = _auth_headers(token)
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.request(method.upper(), url, headers=headers, params=params, json=json_body)
        if r.status_code >= 400:
            return {
                "ok": False,
                "error": redact_text(r.text[:240] or f"HTTP {r.status_code}"),
                "data": None,
                "http_status": r.status_code,
            }
        data = r.json() if r.content else {}
        return {"ok": True, "error": None, "data": data, "http_status": r.status_code}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": redact_text(str(exc)), "data": None, "http_status": None}


def parse_owner_repo(repository: str) -> tuple[str, str]:
    raw = (repository or "").strip().strip("/")
    if not raw:
        return "", ""
    if "/" in raw:
        owner, repo = raw.split("/", 1)
        return owner.strip(), repo.strip()
    return "", raw


def find_repository_by_name(token: str, name: str) -> dict[str, object] | None:
    hint = (name or "").strip()
    if not hint:
        return None
    listed = list_repositories(token)
    if not listed.get("ok"):
        return None
    repos = listed.get("repositories") or []
    hint_lower = hint.lower()
    if "/" in hint:
        for repo in repos:
            if not isinstance(repo, dict):
                continue
            full_name = str(repo.get("full_name") or "")
            if full_name.lower() == hint_lower:
                return repo
    exact: list[dict[str, object]] = []
    partial: list[dict[str, object]] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        repo_name = str(repo.get("name") or "")
        full_name = str(repo.get("full_name") or "")
        if repo_name.lower() == hint_lower or full_name.lower() == hint_lower:
            exact.append(repo)
        elif hint_lower in repo_name.lower() or hint_lower in full_name.lower():
            partial.append(repo)
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        return None
    if len(partial) == 1:
        return partial[0]
    return None

