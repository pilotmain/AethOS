# SPDX-License-Identifier: Apache-2.0
"""Durable workflow lane execution lifecycle — global index + hydration."""

from __future__ import annotations

import json
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import time
from typing import Any

_ACTIVE_STAGES = frozenset({
    "proposal_ready",
    "creation_plan_ready",
    "execution_blocked",
    "executed",
    "execution_failed",
})

_INDEX_MEMORY: dict[str, Any] | None = None
_RUNTIME_CTX: ContextVar["WorkflowLaneRuntimeContext | None"] = ContextVar(
    "_workflow_lane_runtime_ctx",
    default=None,
)


@dataclass
class WorkflowLaneRuntimeContext:
    session_id: str = "default"
    state: dict[str, Any] | None = None
    hydrated: bool = False
    hydration_source: str = ""
    hydration_trace: list[str] = field(default_factory=list)


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "github_workflow_lane"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _index_path() -> Path:
    return _store_dir() / "global_execution_index.json"


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
    progress = state.get("execution_progress") if isinstance(state.get("execution_progress"), dict) else {}
    return {
        "session_id": (session_id or "default").strip(),
        "repo": str(state.get("repo") or ""),
        "file_path": str(state.get("file_path") or ".github/workflows/ci.yml"),
        "base_branch": str(state.get("base_branch") or "main"),
        "branch": str(state.get("branch") or "add-ci-workflow"),
        "stage": str(state.get("stage") or ""),
        "blocker": str(state.get("blocker") or ""),
        "branch_created": bool(state.get("branch_created") or progress.get("branch_created")),
        "file_committed": bool(state.get("file_committed") or progress.get("file_committed")),
        "pr_opened": bool(state.get("pr_opened") or progress.get("pr_opened")),
        "workflow_run_triggered": bool(
            state.get("workflow_run_triggered") or progress.get("workflow_run_detected")
        ),
        "last_successful_step": state.get("last_successful_step") or progress.get("last_successful_step"),
        "last_failed_step": state.get("last_failed_step") or progress.get("last_failed_step"),
        "execution_attempts": int(
            state.get("execution_attempts") or progress.get("execution_attempts") or 0
        ),
        "updated_at": str(state.get("updated_at") or datetime.now(UTC).isoformat()),
        "state": dict(state),
    }


def remove_workflow_lane_from_index(*, session_id: str) -> None:
    """Remove all index entries for a session (e.g. after cancel)."""
    session = (session_id or "default").strip() or "default"
    data = _load_index_raw()
    entries = list(data.get("entries") or [])
    entries = [row for row in entries if str(row.get("session_id") or "") != session]
    data["entries"] = entries
    _save_index_raw(data)


def persist_workflow_lane_state(session_id: str, state: dict[str, Any]) -> None:
    """Persist workflow lane state to session file and global execution index."""
    session_id = (session_id or "default").strip() or "default"
    state = dict(state)
    state["updated_at"] = datetime.now(UTC).isoformat()

    try:
        _session_path(session_id).write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass

    stage = str(state.get("stage") or "")
    if not stage:
        return

    data = _load_index_raw()
    entries = list(data.get("entries") or [])
    entry = _index_entry_from_state(session_id, state)
    key = f"{session_id}:{stage}:{state.get('repo', '')}"
    entries = [row for row in entries if row.get("index_key") != key]
    entry["index_key"] = key
    entries.append(entry)
    entries.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    data["entries"] = entries[:100]
    _save_index_raw(data)


def _read_session_file(session_id: str) -> dict[str, Any] | None:
    path = _session_path(session_id)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("stage"):
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _entry_to_state(entry: dict[str, Any]) -> dict[str, Any]:
    full = entry.get("state")
    if isinstance(full, dict) and full.get("stage"):
        return dict(full)
    return {
        "repo": entry.get("repo") or "pilotmain/aethos",
        "file_path": entry.get("file_path") or ".github/workflows/ci.yml",
        "base_branch": entry.get("base_branch") or "main",
        "branch": entry.get("branch") or "add-ci-workflow",
        "stage": entry.get("stage") or "",
        "blocker": entry.get("blocker") or "",
        "branch_created": entry.get("branch_created"),
        "file_committed": entry.get("file_committed"),
        "pr_opened": entry.get("pr_opened"),
        "workflow_run_triggered": entry.get("workflow_run_triggered"),
        "last_successful_step": entry.get("last_successful_step"),
        "last_failed_step": entry.get("last_failed_step"),
        "execution_attempts": entry.get("execution_attempts"),
        "updated_at": entry.get("updated_at"),
        "proposal_yaml": (entry.get("state") or {}).get("proposal_yaml") if isinstance(entry.get("state"), dict) else "",
        "execution_progress": (entry.get("state") or {}).get("execution_progress") if isinstance(entry.get("state"), dict) else {},
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
        if str(entry.get("session_id") or "") == session and str(entry.get("stage") or "") in _ACTIVE_STAGES:
            return _entry_to_state(entry), "global_index:session_match"
    for entry in entries:
        stage = str(entry.get("stage") or "")
        if stage in _ACTIVE_STAGES:
            return _entry_to_state(entry), "global_index:latest_active"
    return None, ""


def _collect_from_route_trace(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id) or {}
        route_id = str(trace.get("route_id") or "")
        if route_id != "github_workflow_lane":
            return None, ""
        stage = str(trace.get("workflow_lane_stage") or "")
        if not stage:
            return None, ""
        return (
            {
                "repo": "pilotmain/aethos",
                "file_path": ".github/workflows/ci.yml",
                "base_branch": "main",
                "branch": "add-ci-workflow",
                "stage": stage,
                "blocker": "missing_github_mutation_credential",
                "branch_created": False,
                "file_committed": False,
                "pr_opened": False,
                "workflow_run_triggered": False,
                "hydration_fallback": True,
            },
            "route_trace",
        )
    except Exception:
        return None, ""


def load_latest_workflow_lane_state(*, session_id: str = "default") -> dict[str, Any] | None:
    """Load workflow lane state from durable stores (session → global → trace)."""
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


def list_recent_workflow_lanes(*, limit: int = 10) -> list[dict[str, Any]]:
    entries = list(_load_index_raw().get("entries") or [])
    return entries[:limit]


def hydrate_workflow_lane_context(*, session_id: str = "default") -> WorkflowLaneRuntimeContext:
    """Bind durable workflow lane state onto the active runtime turn before routing."""
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
        ctx = WorkflowLaneRuntimeContext(session_id=session, hydrated=False, hydration_trace=["empty"])
        return _bind_runtime_context(ctx)

    if source.startswith("global_index") and source != "session_file":
        persist_workflow_lane_state(session, state)
        trace.append("session_file_rebound")

    ctx = WorkflowLaneRuntimeContext(
        session_id=session,
        state=state,
        hydrated=True,
        hydration_source=source,
        hydration_trace=trace,
    )
    return _bind_runtime_context(ctx)


def get_hydrated_workflow_lane_context() -> WorkflowLaneRuntimeContext | None:
    return _RUNTIME_CTX.get()


def get_resolved_workflow_lane_state(*, session_id: str = "default") -> dict[str, Any] | None:
    """Return workflow lane state for routing, hydrating if needed."""
    bound = get_hydrated_workflow_lane_context()
    session = (session_id or "default").strip() or "default"
    if bound is not None and bound.state and bound.session_id == session:
        return dict(bound.state)
    hydrate_workflow_lane_context(session_id=session)
    bound = get_hydrated_workflow_lane_context()
    if bound is None or not bound.state:
        return load_latest_workflow_lane_state(session_id=session)
    return dict(bound.state)


def ensure_global_execution_index_loaded() -> None:
    _load_index_raw()


def bootstrap_workflow_lane_lifecycle() -> int:
    ensure_global_execution_index_loaded()
    return len(list_recent_workflow_lanes(limit=100))


def clear_lifecycle_for_tests() -> None:
    global _INDEX_MEMORY
    _INDEX_MEMORY = None
    _RUNTIME_CTX.set(None)
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink(missing_ok=True)


def _bind_runtime_context(ctx: WorkflowLaneRuntimeContext) -> WorkflowLaneRuntimeContext:
    _RUNTIME_CTX.set(ctx)
    return ctx
