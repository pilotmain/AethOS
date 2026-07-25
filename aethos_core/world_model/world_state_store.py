# SPDX-License-Identifier: Apache-2.0
"""Persistent world-model storage."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from aethos_core.world_model.investigation_state import InvestigationState

_MEMORY: dict[str, InvestigationState] = {}
_CORRUPT_SESSIONS: set[str] = set()


def _storage_key(*, session_id: str, target: str) -> str:
    return f"{session_id}::{target}"


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "world_model"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_investigations.json"


def _quarantine_dir() -> Path:
    root = _store_dir() / ".quarantine"
    root.mkdir(parents=True, exist_ok=True)
    return root


def session_store_is_corrupt(*, session_id: str) -> bool:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    if safe in _CORRUPT_SESSIONS:
        return True
    path = _session_path(session_id)
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return True
        investigations = payload.get("investigations")
        if investigations is not None and not isinstance(investigations, list):
            return True
        for row in investigations or []:
            if not isinstance(row, dict):
                return True
            InvestigationState.from_dict(row)
        return False
    except Exception:
        return True


def quarantine_session_store(*, session_id: str, reason: str = "corrupt_investigation_state") -> bool:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    path = _session_path(session_id)
    if not path.exists():
        _CORRUPT_SESSIONS.add(safe)
        return False
    stamp = __import__("uuid").uuid4().hex[:8]
    dest = _quarantine_dir() / f"{safe}_{reason}_{stamp}.json"
    try:
        shutil.move(str(path), str(dest))
        prefix = f"{session_id}::"
        for key in list(_MEMORY.keys()):
            if key.startswith(prefix):
                del _MEMORY[key]
        _CORRUPT_SESSIONS.add(safe)
        return True
    except Exception:
        _CORRUPT_SESSIONS.add(safe)
        return False


def load_investigation_state(*, session_id: str, target: str) -> InvestigationState | None:
    key = _storage_key(session_id=session_id, target=target)
    if key in _MEMORY:
        return _MEMORY[key]
    if session_store_is_corrupt(session_id=session_id):
        return None
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("investigations") or []:
            if str(row.get("target") or "") == target:
                state = InvestigationState.from_dict(row)
                _MEMORY[key] = state
                return state
    except Exception:
        _CORRUPT_SESSIONS.add((session_id or "default").strip().replace("/", "_")[:128])
        return None
    return None


def save_investigation_state(state: InvestigationState) -> InvestigationState:
    key = _storage_key(session_id=state.session_id, target=state.target)
    _MEMORY[key] = state
    path = _session_path(state.session_id)
    existing: dict[str, Any] = {"investigations": []}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = {"investigations": []}
    rows = [row for row in existing.get("investigations") or [] if str(row.get("target") or "") != state.target]
    rows.append(state.to_dict())
    existing["investigations"] = rows[-20:]
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return state


def get_active_investigation(*, session_id: str) -> InvestigationState | None:
    prefix = f"{session_id}::"
    active = [state for key, state in _MEMORY.items() if key.startswith(prefix) and state.active_investigation]
    if active:
        return sorted(active, key=lambda s: s.updated_at, reverse=True)[0]
    if session_store_is_corrupt(session_id=session_id):
        return None
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates = [
            InvestigationState.from_dict(row)
            for row in payload.get("investigations") or []
            if row.get("active_investigation")
        ]
        if not candidates:
            return None
        state = sorted(candidates, key=lambda s: s.updated_at, reverse=True)[0]
        _MEMORY[_storage_key(session_id=session_id, target=state.target)] = state
        return state
    except Exception:
        _CORRUPT_SESSIONS.add((session_id or "default").strip().replace("/", "_")[:128])
        return None


def clear_world_model_for_tests() -> None:
    _MEMORY.clear()
    _CORRUPT_SESSIONS.clear()
    root = _store_dir()
    for path in root.glob("*_investigations.json"):
        path.unlink(missing_ok=True)
    quarantine = root / ".quarantine"
    if quarantine.exists():
        for path in quarantine.glob("*.json"):
            path.unlink(missing_ok=True)
