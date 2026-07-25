# SPDX-License-Identifier: Apache-2.0
"""Persist per-chat-session model overrides."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root

_STORE_FILE = "session_model_overrides.json"


def _store_path():
    return agent_artifacts_root() / _STORE_FILE


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"overrides": {}, "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"overrides": {}, "updated_at": None}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _normalize_session_id(session_id: str) -> str:
    return (session_id or "default").strip()[:64] or "default"


def get_session_model_override(session_id: str) -> str | None:
    sid = _normalize_session_id(session_id)
    raw = (_load().get("overrides") or {}).get(sid)
    if not isinstance(raw, str):
        return None
    cleaned = raw.strip()
    return cleaned or None


def set_session_model_override(session_id: str, catalog_id: str | None) -> dict[str, Any]:
    from aethos_core.llm.model_catalog import DEFAULT_CATALOG_ID, catalog_entry_for_id
    from aethos_core.llm.effective_model import resolve_effective_model

    sid = _normalize_session_id(session_id)
    data = _load()
    overrides = dict(data.get("overrides") or {})
    cleaned = (catalog_id or "").strip()
    if not cleaned or cleaned.lower() in ("default", "env"):
        overrides.pop(sid, None)
    else:
        entry = catalog_entry_for_id(cleaned)
        if entry is None or not entry.get("configured"):
            return {"ok": False, "error": "model_not_available", "catalog_id": cleaned}
        overrides[sid] = cleaned if cleaned != DEFAULT_CATALOG_ID else DEFAULT_CATALOG_ID
    data["overrides"] = overrides
    _save(data)
    effective = resolve_effective_model(session_id=sid)
    return {
        "ok": True,
        "session_id": sid,
        "catalog_id": overrides.get(sid) or DEFAULT_CATALOG_ID,
        "effective": {
            "catalog_id": effective.catalog_id,
            "provider": effective.provider,
            "model": effective.model,
            "label": effective.label,
            "source": effective.source,
        },
    }


def clear_session_model_override(session_id: str) -> dict[str, Any]:
    return set_session_model_override(session_id, None)
