# SPDX-License-Identifier: Apache-2.0
"""FIX 125D — bounded governed workspace tree (writes under workspace root only)."""

from __future__ import annotations

import difflib
import json
import re
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.engineering.patch_runtime.patch_scope import assert_path_in_repo
from aethos_core.software_delivery.branch_orchestration_store import workspace_path_for_plan

_BLOCKED_PATH_RX = re.compile(
    r"(^|/)\.\.|(^|/)\.env($|/|\.)|(^|/)secrets/|(^|/)\.git/|node_modules/|(^|/)__pycache__/",
    re.I,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def workspace_tree_root(*, plan_id: str) -> Path:
    root = workspace_path_for_plan(plan_id=plan_id) / "tree"
    root.mkdir(parents=True, exist_ok=True)
    return root


def rollback_root(*, plan_id: str) -> Path:
    root = workspace_path_for_plan(plan_id=plan_id) / "rollback"
    root.mkdir(parents=True, exist_ok=True)
    return root


def normalize_relative_path(rel: str) -> str | None:
    raw = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not raw or _BLOCKED_PATH_RX.search(raw):
        return None
    parts = [p for p in raw.split("/") if p and p != "."]
    if ".." in parts:
        return None
    return "/".join(parts)


def validate_paths_in_scope(*, paths: list[str], allowed_files: list[str]) -> tuple[list[str], list[str]]:
    allowed = {normalize_relative_path(f) for f in allowed_files}
    allowed.discard(None)
    valid: list[str] = []
    rejected: list[str] = []
    for rel in paths:
        norm = normalize_relative_path(rel)
        if not norm or norm not in allowed:
            rejected.append(rel)
            continue
        if not assert_path_in_repo(repo_root(), norm):
            rejected.append(rel)
            continue
        valid.append(norm)
    return valid, rejected


def workspace_file_path(*, plan_id: str, rel: str) -> Path | None:
    norm = normalize_relative_path(rel)
    if not norm:
        return None
    tree = workspace_tree_root(plan_id=plan_id)
    target = (tree / norm).resolve()
    if not str(target).startswith(str(tree.resolve())):
        return None
    return target


def read_repo_source(rel: str) -> str | None:
    norm = normalize_relative_path(rel)
    if not norm:
        return None
    path = repo_root() / norm
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def create_rollback_snapshot(*, plan_id: str, files: list[str]) -> dict[str, Any]:
    snapshot_id = f"sdsnap-{uuid.uuid4().hex[:12]}"
    snap_dir = rollback_root(plan_id=plan_id) / snapshot_id
    snap_dir.mkdir(parents=True, exist_ok=True)
    captured: list[str] = []
    for rel in files:
        norm = normalize_relative_path(rel)
        if not norm:
            continue
        ws_path = workspace_file_path(plan_id=plan_id, rel=norm)
        content: str | None = None
        if ws_path and ws_path.is_file():
            content = ws_path.read_text(encoding="utf-8", errors="replace")
        else:
            content = read_repo_source(norm)
        if content is None:
            continue
        dest = snap_dir / norm
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        captured.append(norm)
    meta = {
        "snapshot_id": snapshot_id,
        "plan_id": plan_id,
        "files": captured,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (snap_dir / "_snapshot_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def apply_patch_to_workspace(
    *,
    plan_id: str,
    rel: str,
    new_content: str,
    allowed_files: list[str],
) -> dict[str, Any]:
    valid, rejected = validate_paths_in_scope(paths=[rel], allowed_files=allowed_files)
    if rejected or not valid:
        return {"ok": False, "error": "file_out_of_scope", "file": rel}
    norm = valid[0]
    target = workspace_file_path(plan_id=plan_id, rel=norm)
    if target is None:
        return {"ok": False, "error": "invalid_workspace_path", "file": norm}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_content, encoding="utf-8")
    return {"ok": True, "file": norm, "workspace_path": str(target)}


def restore_rollback_snapshot(*, plan_id: str, snapshot_id: str) -> dict[str, Any]:
    snap_dir = rollback_root(plan_id=plan_id) / snapshot_id
    meta_path = snap_dir / "_snapshot_meta.json"
    if not meta_path.is_file():
        return {"ok": False, "error": "snapshot_missing"}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "error": "snapshot_corrupt"}
    restored: list[str] = []
    for rel in meta.get("files") or []:
        src = snap_dir / str(rel)
        if not src.is_file():
            continue
        target = workspace_file_path(plan_id=plan_id, rel=str(rel))
        if target is None:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        restored.append(str(rel))
    return {"ok": True, "restored_files": restored, "snapshot_id": snapshot_id}


def workspace_unified_diffs(*, plan_id: str, files: list[str]) -> list[dict[str, str]]:
    diffs: list[dict[str, str]] = []
    for rel in files:
        norm = normalize_relative_path(rel)
        if not norm:
            continue
        ws_path = workspace_file_path(plan_id=plan_id, rel=norm)
        if not ws_path or not ws_path.is_file():
            continue
        after = ws_path.read_text(encoding="utf-8", errors="replace")
        before = read_repo_source(norm) or ""
        if before == after:
            continue
        diff = "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{norm}",
                tofile=f"b/{norm}",
            )
        )
        diffs.append({"file": norm, "diff": diff, "lines_changed": diff.count("\n+") + diff.count("\n-")})
    return diffs
