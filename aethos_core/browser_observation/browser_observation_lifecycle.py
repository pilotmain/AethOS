# SPDX-License-Identifier: Apache-2.0
"""Durable browser observation lifecycle — session store + global index + hydration."""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import time
from typing import Any

_ACTIVE_STATUSES = frozenset({"captured", "failed", "blocked"})

_INDEX_MEMORY: dict[str, Any] | None = None
_RUNTIME_CTX: ContextVar["BrowserObservationRuntimeContext | None"] = ContextVar(
    "_browser_observation_runtime_ctx",
    default=None,
)


@dataclass
class BrowserObservationRuntimeContext:
    session_id: str = "default"
    state: dict[str, Any] | None = None
    hydrated: bool = False
    hydration_source: str = ""
    hydration_trace: list[str] = field(default_factory=list)


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "browser_observation"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _index_path() -> Path:
    return _store_dir() / "global_observation_index.json"


def _load_index_raw() -> dict[str, Any]:
    global _INDEX_MEMORY
    if _INDEX_MEMORY is not None:
        return _INDEX_MEMORY
    path = _index_path()
    if not path.is_file():
        _INDEX_MEMORY = {"entries": [], "updated_at": 0.0}
        return _INDEX_MEMORY
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raw = {"entries": [], "updated_at": 0.0}
    except (OSError, json.JSONDecodeError):
        raw = {"entries": [], "updated_at": 0.0}
    _INDEX_MEMORY = raw
    return _INDEX_MEMORY


def _save_index_raw(data: dict[str, Any]) -> None:
    global _INDEX_MEMORY
    data["updated_at"] = time()
    _INDEX_MEMORY = data
    try:
        _index_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def _index_entry_from_state(session_id: str, state: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": (session_id or "default").strip(),
        "artifact_id": str(state.get("artifact_id") or ""),
        "url": str(state.get("url") or ""),
        "type": str(state.get("type") or "screenshot"),
        "status": str(state.get("status") or ""),
        "timestamp": str(state.get("timestamp") or ""),
        "updated_at": str(state.get("updated_at") or datetime.now(UTC).isoformat()),
        "state": dict(state),
    }


def persist_browser_observation(session_id: str, state: dict[str, Any]) -> None:
    """Persist browser observation to per-session file and global index."""
    session_id = (session_id or "default").strip() or "default"
    state = dict(state)
    state["updated_at"] = datetime.now(UTC).isoformat()
    status = str(state.get("status") or "")
    if not status:
        return

    try:
        _session_path(session_id).write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass

    data = _load_index_raw()
    entries = list(data.get("entries") or [])
    entry = _index_entry_from_state(session_id, state)
    key = f"{session_id}:{state.get('artifact_id', '')}"
    entries = [row for row in entries if row.get("index_key") != key]
    entry["index_key"] = key
    entries.append(entry)
    entries.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    data["entries"] = entries[:100]
    _save_index_raw(data)

    bound = _RUNTIME_CTX.get()
    if bound is not None and bound.session_id == session_id:
        bound.state = dict(state)
        bound.hydrated = True


def _read_session_file(session_id: str) -> dict[str, Any] | None:
    path = _session_path(session_id)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("status"):
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _entry_to_state(entry: dict[str, Any]) -> dict[str, Any]:
    full = entry.get("state")
    if isinstance(full, dict) and full.get("status"):
        return dict(full)
    return {
        "artifact_id": str(entry.get("artifact_id") or ""),
        "url": str(entry.get("url") or ""),
        "type": str(entry.get("type") or "screenshot"),
        "timestamp": str(entry.get("timestamp") or ""),
        "artifacts": [],
        "status": str(entry.get("status") or ""),
        "artifact_file_url": "",
        "updated_at": str(entry.get("updated_at") or ""),
    }


def _collect_from_session_file(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    state = _read_session_file(session_id)
    if state:
        return state, "session_file"
    return None, ""


def _collect_from_global_index(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    session = (session_id or "default").strip() or "default"
    entries = list(_load_index_raw().get("entries") or [])
    for entry in entries:
        if str(entry.get("session_id") or "") == session and str(entry.get("status") or "") in _ACTIVE_STATUSES:
            return _entry_to_state(entry), "global_index:session_match"
    for entry in entries:
        if str(entry.get("status") or "") in _ACTIVE_STATUSES:
            return _entry_to_state(entry), "global_index:latest_active"
    return None, ""


def _collect_from_route_trace(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id) or {}
        if str(trace.get("route_id") or "") != "browser_observation":
            return None, ""
        artifact_id = str(trace.get("artifact_id") or "")
        if not artifact_id:
            return None, ""
        return (
            {
                "artifact_id": artifact_id,
                "url": str(trace.get("target_url") or ""),
                "type": "screenshot",
                "timestamp": "",
                "artifacts": [],
                "status": "captured",
                "artifact_file_url": f"/api/v1/browser/artifacts/{artifact_id}/file",
                "hydration_fallback": True,
            },
            "route_trace",
        )
    except Exception:
        return None, ""
    return None, ""


def load_latest_browser_observation(*, session_id: str = "default") -> dict[str, Any] | None:
    """Load latest browser observation from durable stores."""
    bound = _RUNTIME_CTX.get()
    session = (session_id or "default").strip() or "default"
    if bound is not None and bound.state and bound.session_id == session:
        return dict(bound.state)

    for collector in (
        lambda: _collect_from_session_file(session_id=session),
        lambda: _collect_from_global_index(session_id=session),
        lambda: _collect_from_route_trace(session_id=session),
    ):
        state, _source = collector()
        if state:
            return state
    return None


def _bind_runtime_context(ctx: BrowserObservationRuntimeContext) -> BrowserObservationRuntimeContext:
    _RUNTIME_CTX.set(ctx)
    return ctx


def hydrate_browser_observation_context(*, session_id: str = "default") -> BrowserObservationRuntimeContext:
    """Bind durable browser observation onto the active runtime turn before routing."""
    session = (session_id or "default").strip() or "default"
    trace: list[str] = []
    state: dict[str, Any] | None = None
    source = ""

    for collector in (
        lambda: _collect_from_session_file(session_id=session),
        lambda: _collect_from_global_index(session_id=session),
        lambda: _collect_from_route_trace(session_id=session),
    ):
        found, found_source = collector()
        if found:
            state = found
            source = found_source
            trace.append(found_source)
            break

    if state is None:
        ctx = BrowserObservationRuntimeContext(session_id=session, hydrated=False, hydration_trace=["empty"])
        return _bind_runtime_context(ctx)

    if source.startswith("global_index") and source != "session_file":
        persist_browser_observation(session, state)
        trace.append("session_file_rebound")

    ctx = BrowserObservationRuntimeContext(
        session_id=session,
        state=state,
        hydrated=True,
        hydration_source=source,
        hydration_trace=trace,
    )
    return _bind_runtime_context(ctx)


def get_hydrated_browser_observation_context() -> BrowserObservationRuntimeContext | None:
    return _RUNTIME_CTX.get()


def clear_browser_observation_context(*, session_id: str | None = None) -> None:
    """Clear in-memory hydration; optionally remove session file."""
    _RUNTIME_CTX.set(None)
    if session_id:
        path = _session_path(session_id)
        if path.is_file():
            path.unlink()


def clear_lifecycle_for_tests() -> None:
    global _INDEX_MEMORY
    _INDEX_MEMORY = None
    _RUNTIME_CTX.set(None)
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()


def clear_memory_cache_for_tests() -> None:
    _RUNTIME_CTX.set(None)
    global _INDEX_MEMORY
    _INDEX_MEMORY = None
