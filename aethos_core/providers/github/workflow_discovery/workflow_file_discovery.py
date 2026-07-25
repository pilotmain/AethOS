# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow file discovery via readonly API."""

from __future__ import annotations

import base64
from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github
from aethos_core.providers.github.shared.workflow_resolution import resolve_repository

_WORKFLOWS_DIR = ".github/workflows"
_WORKFLOW_SUFFIXES = (".yml", ".yaml")


def discover_workflow_files(
    token: str,
    *,
    repository: str,
    ref: str | None = None,
) -> dict[str, Any]:
    resolved = resolve_repository(token, repository=repository)
    if not resolved.get("ok"):
        return {
            "ok": False,
            "repository": repository,
            "workflows_dir_found": False,
            "workflow_files": [],
            "error": str(resolved.get("error") or "Repository could not be resolved."),
        }
    owner = str(resolved["owner"])
    repo = str(resolved["repo"])
    full_name = str(resolved["full_name"])
    default_branch = str(resolved.get("default_branch") or "main")
    branch = (ref or default_branch or "main").strip() or "main"

    listing = request_github(
        token,
        "GET",
        f"/repos/{owner}/{repo}/contents/{_WORKFLOWS_DIR}",
        params={"ref": branch},
    )
    if not listing.get("ok"):
        status = listing.get("http_status")
        if status == 404:
            return {
                "ok": True,
                "repository": full_name,
                "default_branch": default_branch,
                "ref": branch,
                "workflows_dir_found": False,
                "workflow_files": [],
                "workflow_file_names": [],
            }
        return {
            "ok": False,
            "repository": full_name,
            "default_branch": default_branch,
            "ref": branch,
            "workflows_dir_found": False,
            "workflow_files": [],
            "error": str(listing.get("error") or "Workflow directory lookup failed."),
        }

    entries = listing.get("data")
    if not isinstance(entries, list):
        return {
            "ok": True,
            "repository": full_name,
            "default_branch": default_branch,
            "ref": branch,
            "workflows_dir_found": False,
            "workflow_files": [],
            "workflow_file_names": [],
        }

    files: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "")
        if entry.get("type") != "file":
            continue
        if not name.endswith(_WORKFLOW_SUFFIXES):
            continue
        content_payload = _fetch_workflow_file_content(
            token,
            owner=owner,
            repo=repo,
            path=str(entry.get("path") or f"{_WORKFLOWS_DIR}/{name}"),
            ref=branch,
            entry=entry,
        )
        files.append(content_payload)

    return {
        "ok": True,
        "repository": full_name,
        "default_branch": default_branch,
        "ref": branch,
        "workflows_dir_found": True,
        "workflow_files": files,
        "workflow_file_names": [str(row.get("name") or "") for row in files if row.get("name")],
    }


def _fetch_workflow_file_content(
    token: str,
    *,
    owner: str,
    repo: str,
    path: str,
    ref: str,
    entry: dict[str, Any],
) -> dict[str, Any]:
    name = str(entry.get("name") or path.rsplit("/", 1)[-1])
    if entry.get("content") and entry.get("encoding") == "base64":
        text = _decode_content(str(entry.get("content") or ""))
    else:
        fetched = request_github(
            token,
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        if not fetched.get("ok"):
            return {
                "name": name,
                "path": path,
                "ok": False,
                "parse_ok": False,
                "error": str(fetched.get("error") or "Could not fetch workflow file."),
                "content": "",
            }
        data = dict(fetched.get("data") or {})
        text = _decode_content(str(data.get("content") or ""))
    return {
        "name": name,
        "path": path,
        "ok": True,
        "content": text,
        "size": len(text),
    }


def _decode_content(raw: str) -> str:
    cleaned = raw.replace("\n", "").strip()
    if not cleaned:
        return ""
    try:
        return base64.b64decode(cleaned).decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_repository_slug(repository: str) -> tuple[str, str]:
    owner, repo = parse_owner_repo(repository)
    return owner, repo
