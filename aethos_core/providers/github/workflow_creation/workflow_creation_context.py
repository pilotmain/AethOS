# SPDX-License-Identifier: Apache-2.0
"""Durable pending workflow-creation context — persists after proposal, consumed by creation plan."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_CONTEXT_STORE: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "workflow_creation"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_pending.json"


def save_pending_workflow_proposal(
    *,
    session_id: str,
    repo: str,
    file_path: str,
    branch: str,
    base_branch: str,
    proposal_yaml: str,
) -> None:
    session_id = (session_id or "default").strip()
    payload = {
        "repo": repo,
        "file_path": file_path,
        "branch": branch,
        "base_branch": base_branch,
        "proposal_yaml": proposal_yaml,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _CONTEXT_STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def get_pending_workflow_proposal(*, session_id: str) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _CONTEXT_STORE.get(session_id)
    if cached is not None:
        return dict(cached)
    path = _session_path(session_id)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and raw.get("repo"):
                _CONTEXT_STORE[session_id] = raw
                return dict(raw)
        except (OSError, json.JSONDecodeError):
            pass
    return None


def clear_pending_workflow_proposal(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _CONTEXT_STORE.pop(session_id, None)
    try:
        _session_path(session_id).unlink(missing_ok=True)
    except OSError:
        pass


def has_pending_workflow_proposal(*, session_id: str) -> bool:
    return get_pending_workflow_proposal(session_id=session_id) is not None


def clear_for_tests() -> None:
    _CONTEXT_STORE.clear()
    root = _store_dir()
    for path in root.glob("*_pending.json"):
        path.unlink(missing_ok=True)
