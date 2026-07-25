# SPDX-License-Identifier: Apache-2.0
"""Deployment target registry — explicit repo/provider profiles."""

from __future__ import annotations

import json
import re
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.deployment_targets.paths import targets_index_path
from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import normalize_github_repository_slug

_ALIAS_RX = re.compile(r"\b([a-z0-9][a-z0-9._-]*)\b", re.I)


def _atomic_write(path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _load_index() -> dict[str, Any]:
    path = targets_index_path()
    if not path.is_file():
        return {"targets": [], "updated_at": None}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"targets": [], "updated_at": None}
    if not isinstance(raw, dict):
        return {"targets": [], "updated_at": None}
    rows = raw.get("targets")
    if not isinstance(rows, list):
        raw["targets"] = []
    return raw


def list_targets() -> list[dict[str, Any]]:
    rows = _load_index().get("targets") or []
    return [dict(r) for r in rows if isinstance(r, dict)]


def get_target(target_id: str) -> dict[str, Any] | None:
    for row in list_targets():
        if str(row.get("target_id") or "") == target_id:
            return row
    return None


def _all_aliases(row: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    primary = str(row.get("alias") or "").strip().lower()
    if primary:
        aliases.append(primary)
    extra = row.get("aliases") or []
    if isinstance(extra, list):
        for item in extra:
            token = str(item or "").strip().lower()
            if token and token not in aliases:
                aliases.append(token)
    repo = normalize_github_repository_slug(str(row.get("repo") or ""))
    if repo and "/" in repo:
        basename = repo.split("/")[-1].lower()
        if basename and basename not in aliases:
            aliases.append(basename)
    return aliases


def find_target_by_alias(alias: str) -> dict[str, Any] | None:
    normalized = (alias or "").strip().lower().replace("_", "-")
    if not normalized:
        return None
    for row in list_targets():
        for token in _all_aliases(row):
            if token == normalized or normalized.replace("-", "") == token.replace("-", ""):
                return row
    return None


def find_target_by_repo(repo: str) -> dict[str, Any] | None:
    slug = normalize_github_repository_slug(repo)
    if not slug:
        return None
    for row in list_targets():
        if normalize_github_repository_slug(str(row.get("repo") or "")) == slug:
            return row
    return None


def find_target_by_workspace_id(workspace_id: str) -> dict[str, Any] | None:
    wid = (workspace_id or "").strip()
    if not wid:
        return None
    for row in list_targets():
        if str(row.get("workspace_id") or "") == wid:
            return row
    return None


def match_aliases_in_text(text: str) -> dict[str, Any] | None:
    """Return first registry target whose alias appears as a word in text."""
    raw = (text or "").strip()
    if not raw:
        return None
    tokens = {m.group(1).lower() for m in _ALIAS_RX.finditer(raw)}
    for row in list_targets():
        for alias in _all_aliases(row):
            if alias in tokens:
                return row
    return None


def register_target(
    *,
    alias: str,
    repo: str,
    branch: str = "main",
    aliases: list[str] | None = None,
    workspace_id: str = "",
    local_path: str = "",
    vercel_project: str = "",
    railway_project: str = "",
    railway_service: str = "",
    railway_environment: str = "",
    root_directory: str = "",
    default_provider: str = "",
) -> dict[str, Any]:
    slug = normalize_github_repository_slug(repo)
    if not slug or "/" not in slug:
        raise ValueError("repo must be owner/name")
    alias_clean = (alias or slug.split("/")[-1]).strip().lower()
    if not alias_clean:
        raise ValueError("alias is required")

    record: dict[str, Any] = {
        "target_id": f"dt-{uuid4().hex[:12]}",
        "alias": alias_clean,
        "aliases": list(aliases or []),
        "repo": slug,
        "branch": (branch or "main").strip() or "main",
        "workspace_id": (workspace_id or "").strip(),
        "local_path": (local_path or "").strip(),
        "vercel_project": (vercel_project or alias_clean).strip(),
        "railway_project": (railway_project or "").strip(),
        "railway_service": (railway_service or "").strip(),
        "railway_environment": (railway_environment or "").strip(),
        "root_directory": (root_directory or "").strip(),
        "default_provider": (default_provider or "").strip().lower(),
        "registered_at": time(),
        "updated_at": time(),
    }

    index = _load_index()
    rows = list(index.get("targets") or [])
    for i, row in enumerate(rows):
        if str(row.get("alias") or "").lower() == alias_clean:
            record["target_id"] = str(row.get("target_id") or record["target_id"])
            record["registered_at"] = row.get("registered_at") or record["registered_at"]
            rows[i] = record
            index["targets"] = rows
            index["updated_at"] = time()
            _atomic_write(targets_index_path(), index)
            return record
        if normalize_github_repository_slug(str(row.get("repo") or "")) == slug:
            record["target_id"] = str(row.get("target_id") or record["target_id"])
            record["registered_at"] = row.get("registered_at") or record["registered_at"]
            rows[i] = record
            index["targets"] = rows
            index["updated_at"] = time()
            _atomic_write(targets_index_path(), index)
            return record

    rows.append(record)
    index["targets"] = rows
    index["updated_at"] = time()
    _atomic_write(targets_index_path(), index)
    return record


def update_target(target_id: str, *, patch: dict[str, Any]) -> dict[str, Any] | None:
    index = _load_index()
    rows = list(index.get("targets") or [])
    for i, row in enumerate(rows):
        if str(row.get("target_id") or "") != target_id:
            continue
        updated = {**row, **patch, "updated_at": time()}
        if "repo" in patch:
            slug = normalize_github_repository_slug(str(updated.get("repo") or ""))
            if not slug:
                raise ValueError("repo must be owner/name")
            updated["repo"] = slug
        rows[i] = updated
        index["targets"] = rows
        index["updated_at"] = time()
        _atomic_write(targets_index_path(), index)
        return updated
    return None


def delete_target(target_id: str) -> bool:
    index = _load_index()
    rows = list(index.get("targets") or [])
    kept = [r for r in rows if str(r.get("target_id") or "") != target_id]
    if len(kept) == len(rows):
        return False
    index["targets"] = kept
    index["updated_at"] = time()
    _atomic_write(targets_index_path(), index)
    return True


def target_to_resolution(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    repo = normalize_github_repository_slug(str(row.get("repo") or ""))
    alias = str(row.get("alias") or "")
    project_name = str(row.get("vercel_project") or alias or (repo.split("/")[-1] if repo else "app"))
    return {
        "ok": True,
        "source": source,
        "target_id": str(row.get("target_id") or ""),
        "alias": alias,
        "repo": repo,
        "branch": str(row.get("branch") or "main"),
        "project_name": project_name,
        "vercel_project": str(row.get("vercel_project") or project_name),
        "railway_project": str(row.get("railway_project") or ""),
        "railway_service": str(row.get("railway_service") or ""),
        "railway_environment": str(row.get("railway_environment") or ""),
        "root_directory": str(row.get("root_directory") or ""),
        "default_provider": str(row.get("default_provider") or ""),
        "workspace_id": str(row.get("workspace_id") or ""),
        "local_path": str(row.get("local_path") or ""),
    }
