# SPDX-License-Identifier: Apache-2.0
"""Arbiter session store — in-memory cache backed by the durable tenant store.

Completed sessions are persisted (per tenant) to ``tenant_data_store`` (Postgres on
hosted, SQLite locally), so the Mission Control → Arbiter panel keeps its per-model
breakdown across restarts/deploys. The in-memory dict stays as a fast cache for the
current process. Persistence failures never break a run — we fall back to memory.
"""

from __future__ import annotations

import dataclasses
import logging
import threading
from typing import Any

from aethos_core.arbiter.models import (
    ArbiterSession,
    ArbiterStatus,
    ConsensusResult,
    CritiqueScore,
    ModelResponse,
)

_log = logging.getLogger("aethos.arbiter.session_store")

_lock = threading.Lock()
_sessions: "dict[str, ArbiterSession]" = {}
_MAX_SESSIONS = 200  # in-memory LRU cap — oldest dropped when exceeded

_NS = "arbiter_sessions"
# Only persist terminal sessions: an interrupted run must not leave a stale
# "dispatching" row in the durable history.
_TERMINAL = {
    ArbiterStatus.COMPLETED,
    ArbiterStatus.FAILED,
    ArbiterStatus.NO_CONSENSUS,
    ArbiterStatus.TIMEOUT,
}


def _serialize(session: ArbiterSession) -> dict[str, Any]:
    data = dataclasses.asdict(session)
    data["status"] = session.status.value
    return data


def _deserialize(data: dict[str, Any]) -> ArbiterSession | None:
    try:
        responses = [ModelResponse(**r) for r in data.get("responses", []) or []]
        critiques = [CritiqueScore(**c) for c in data.get("critiques", []) or []]
        cons = data.get("consensus")
        consensus = ConsensusResult(**cons) if isinstance(cons, dict) else None
        return ArbiterSession(
            session_id=str(data["session_id"]),
            chat_session_id=str(data.get("chat_session_id") or "default"),
            tenant_id=str(data.get("tenant_id") or "default"),
            prompt=str(data.get("prompt") or ""),
            status=ArbiterStatus(str(data.get("status") or "completed")),
            model_pool=list(data.get("model_pool") or []),
            responses=responses,
            critiques=critiques,
            consensus=consensus,
            rounds_completed=int(data.get("rounds_completed") or 0),
            started_at=float(data.get("started_at") or 0.0),
            completed_at=data.get("completed_at"),
            artifact_id=data.get("artifact_id"),
            error=data.get("error"),
        )
    except Exception:  # noqa: BLE001 — never let a malformed row break the panel.
        return None


def put_session(session: ArbiterSession) -> None:
    with _lock:
        if session.session_id in _sessions:
            del _sessions[session.session_id]
        elif len(_sessions) >= _MAX_SESSIONS:
            del _sessions[next(iter(_sessions))]
        _sessions[session.session_id] = session

    if session.status in _TERMINAL:
        try:
            from aethos_core.tenancy.tenant_data_store import set_record

            set_record(_NS, session.session_id, _serialize(session), tenant_id=session.tenant_id)
        except Exception as exc:  # noqa: BLE001 — durability is best-effort.
            _log.warning("arbiter session persist failed (%s): %s", session.session_id, exc.__class__.__name__)


def get_session(session_id: str) -> ArbiterSession | None:
    with _lock:
        cached = _sessions.get(session_id)
    if cached is not None:
        return cached
    # Not in this process (e.g. after a restart) — load from the durable store, scoped
    # to the caller's current tenant.
    try:
        from aethos_core.tenancy.tenant_data_store import get_record

        data = get_record(_NS, session_id, default=None)
    except Exception:
        return None
    return _deserialize(data) if isinstance(data, dict) else None


def list_sessions(limit: int = 20) -> list[dict[str, Any]]:
    cap = max(1, limit)
    merged: dict[str, ArbiterSession] = {}

    # Durable history first (current tenant), then overlay fresher in-memory sessions.
    try:
        from aethos_core.tenancy.tenant_data_store import list_records

        for row in list_records(_NS, limit=cap * 2):
            sess = _deserialize(row)
            if sess is not None:
                merged[sess.session_id] = sess
    except Exception:
        pass

    with _lock:
        for sid, sess in _sessions.items():
            merged[sid] = sess  # in-memory wins (newer state)

    items = sorted(merged.values(), key=lambda s: s.started_at, reverse=True)
    return [s.to_dict() for s in items[:cap]]


def delete_session(session_id: str) -> bool:
    found = False
    with _lock:
        if session_id in _sessions:
            del _sessions[session_id]
            found = True
    try:
        from aethos_core.tenancy.tenant_data_store import delete_record

        if delete_record(_NS, session_id):
            found = True
    except Exception:
        pass
    return found
