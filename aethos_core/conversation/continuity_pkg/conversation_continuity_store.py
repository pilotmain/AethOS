# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — session topic state store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_contract import (
    CONTINUITY_REVIEW_RECORD_KINDS,
    CONTINUITY_REVIEW_RECORD_SCHEMA_VERSION,
    MAX_CONTINUITY_REVIEW_CONTENT_LEN,
    MAX_PERSISTED_CONTINUITY_REVIEW_RECORDS,
)

_DEFAULT_SESSION_STORE = Path("data/conversation_continuity/session_state.json")
_DEFAULT_REVIEW_STORE = Path("data/conversation_continuity/review_records.json")

_SESSION_CACHE: dict[str, dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _session_store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_CONVERSATION_CONTINUITY_SESSION_STORE",
            str(_DEFAULT_SESSION_STORE),
        )
    )


def _review_store_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_CONVERSATION_CONTINUITY_STORE",
            str(_DEFAULT_REVIEW_STORE),
        )
    )


def _load_sessions() -> dict[str, Any]:
    path = _session_store_path()
    if not path.exists():
        return {"sessions": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"sessions": {}}
    if not isinstance(payload, dict):
        return {"sessions": {}}
    if not isinstance(payload.get("sessions"), dict):
        payload["sessions"] = {}
    return payload


def _save_sessions(payload: dict[str, Any]) -> None:
    path = _session_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_session_state_for_tests() -> None:
    global _SESSION_CACHE
    _SESSION_CACHE = {}
    path = _session_store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def get_session_state(*, session_id: str) -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    if sid in _SESSION_CACHE:
        return dict(_SESSION_CACHE[sid])

    payload = _load_sessions()
    sessions = payload.get("sessions") or {}
    state = sessions.get(sid)
    if not isinstance(state, dict):
        state = {
            "session_id": sid,
            "active_topic": None,
            "parent_topic": None,
            "confidence": 0.0,
            "active_mode": "general",
            "last_classification": None,
            "last_intent": None,
            "turn_count": 0,
            "updated_at": None,
        }
    _SESSION_CACHE[sid] = dict(state)
    return dict(state)


def update_session_state(
    *,
    session_id: str,
    active_topic: str | None = None,
    parent_topic: str | None = None,
    confidence: float | None = None,
    active_mode: str | None = None,
    last_classification: str | None = None,
    last_intent: str | None = None,
    increment_turn: bool = False,
) -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    state = get_session_state(session_id=sid)

    if active_topic is not None:
        state["active_topic"] = active_topic
    if parent_topic is not None:
        state["parent_topic"] = parent_topic
    if confidence is not None:
        state["confidence"] = round(float(confidence), 2)
    if active_mode is not None:
        state["active_mode"] = active_mode
    if last_classification is not None:
        state["last_classification"] = last_classification
    if last_intent is not None:
        state["last_intent"] = last_intent
    if increment_turn:
        state["turn_count"] = int(state.get("turn_count") or 0) + 1
    state["updated_at"] = _utc_now()

    _SESSION_CACHE[sid] = dict(state)
    payload = _load_sessions()
    sessions = dict(payload.get("sessions") or {})
    sessions[sid] = state
    payload["sessions"] = sessions
    _save_sessions(payload)
    return dict(state)


def _load_review_raw() -> dict[str, Any]:
    path = _review_store_path()
    if not path.exists():
        return {"records": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"records": []}
    if not isinstance(payload, dict):
        return {"records": []}
    if not isinstance(payload.get("records"), list):
        payload["records"] = []
    return payload


def _save_review_raw(payload: dict[str, Any]) -> None:
    path = _review_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def list_continuity_review_records() -> list[dict[str, Any]]:
    return list(_load_review_raw().get("records") or [])


def clear_continuity_review_records_for_tests() -> None:
    path = _review_store_path()
    if path.exists():
        path.unlink(missing_ok=True)


def append_continuity_review_record(
    *,
    kind: str,
    content: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    if kind not in CONTINUITY_REVIEW_RECORD_KINDS:
        raise ValueError(f"unsupported continuity review kind: {kind}")

    trimmed = (content or "").strip()
    if not trimmed:
        raise ValueError("continuity review content required")
    if len(trimmed) > MAX_CONTINUITY_REVIEW_CONTENT_LEN:
        trimmed = trimmed[:MAX_CONTINUITY_REVIEW_CONTENT_LEN]

    record = {
        "schema_version": CONTINUITY_REVIEW_RECORD_SCHEMA_VERSION,
        "kind": kind,
        "content": trimmed,
        "session_id": (session_id or "").strip()[:64] or None,
        "recorded_at": _utc_now(),
    }

    payload = _load_review_raw()
    records = list(payload.get("records") or [])
    records.append(record)
    payload["records"] = records[-MAX_PERSISTED_CONTINUITY_REVIEW_RECORDS:]
    _save_review_raw(payload)
    return record
