# SPDX-License-Identifier: Apache-2.0
"""Global mutation lifecycle index — provider/target discovery across sessions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time
from typing import Any

from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState

_MEMORY: dict[str, Any] | None = None

_SNAPSHOT_KEYS = (
    "executed",
    "execution_state",
    "verification_state",
    "restart_verification_state",
    "restart_command_submitted",
    "provider_result",
    "railway_before_snapshot",
    "railway_after_snapshot",
    "provider_evidence_bundle",
    "lifecycle_summary",
    "restart_service_health",
    "target",
    "target_name",
    "canonical_lifecycle_state",
    "mutation_execution",
    "verification_artifact",
)

_PATH_TARGET_RX = re.compile(
    r"(?P<project>[a-z0-9][\w-]*)\s*[/\\]\s*(?P<environment>[a-z0-9][\w-]*)\s*[/\\]\s*(?P<service>[\w-]+)",
    re.I,
)


def _index_path() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "operation_lifecycle"
    root.mkdir(parents=True, exist_ok=True)
    return root / "global_index.json"


def _norm(value: str | None) -> str:
    return str(value or "").strip().lower()


def _load_raw() -> dict[str, Any]:
    global _MEMORY
    if _MEMORY is not None:
        return _MEMORY
    path = _index_path()
    if not path.is_file():
        _MEMORY = {"entries": [], "updated_at": 0.0}
        return _MEMORY
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raw = {"entries": [], "updated_at": 0.0}
    except (OSError, json.JSONDecodeError):
        raw = {"entries": [], "updated_at": 0.0}
    _MEMORY = raw
    return _MEMORY


def _save_raw(data: dict[str, Any]) -> None:
    global _MEMORY
    data["updated_at"] = time()
    _MEMORY = data
    _index_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _snapshot_params(params: dict[str, Any] | None) -> dict[str, Any]:
    if not params:
        return {}
    return {key: params[key] for key in _SNAPSHOT_KEYS if key in params}


def _entry_from_state(
    state: OperationLifecycleState,
    *,
    execution_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = execution_params
    if snapshot is None and state.execution_job_id:
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(state.execution_job_id)
        if job is not None:
            snapshot = dict(getattr(job, "params", None) or {})
    return {
        "provider": state.provider,
        "project": state.project or "",
        "environment": state.environment or "",
        "service": state.service or "",
        "operation": state.operation,
        "execution_job_id": state.execution_job_id or "",
        "preflight_job_id": state.preflight_job_id or "",
        "timestamp": float(state.updated_at or time()),
        "session_id": state.session_id,
        "status": state.execution_status,
        "verification_status": state.verification_status,
        "approval_status": state.approval_status,
        "canonical_state": state.canonical_state,
        "match_key": state.match_key,
        "latest_summary": state.latest_summary,
        "state": state.to_dict(),
        "execution_params_snapshot": _snapshot_params(snapshot),
        "indexed_at": time(),
    }


def _state_from_entry(entry: dict[str, Any]) -> OperationLifecycleState:
    state_dict = dict(entry.get("state") or {})
    if not state_dict:
        state_dict = {
            "provider": entry.get("provider") or "railway",
            "project": entry.get("project") or None,
            "environment": entry.get("environment") or None,
            "service": entry.get("service") or None,
            "operation": entry.get("operation") or "restart",
            "preflight_job_id": entry.get("preflight_job_id") or None,
            "execution_job_id": entry.get("execution_job_id") or None,
            "approval_status": entry.get("approval_status") or "not_required",
            "execution_status": entry.get("status") or "none",
            "verification_status": entry.get("verification_status") or "none",
            "canonical_state": entry.get("canonical_state") or "preflight_pending",
            "latest_summary": entry.get("latest_summary") or "",
            "session_id": entry.get("session_id") or "default",
            "match_key": entry.get("match_key") or "",
            "updated_at": float(entry.get("timestamp") or time()),
        }
    return OperationLifecycleState(**state_dict)


def _is_indexable(state: OperationLifecycleState) -> bool:
    if not state.provider or not state.operation:
        return False
    if state.execution_job_id:
        return True
    if state.preflight_job_id and state.approval_status in {"pending", "approved", "blocked"}:
        return True
    return state.execution_status in {"completed", "running"}


def _dedupe_key(entry: dict[str, Any]) -> str:
    return str(
        entry.get("execution_job_id")
        or entry.get("match_key")
        or f"{entry.get('provider')}:{entry.get('project')}:{entry.get('environment')}:{entry.get('service')}:{entry.get('operation')}"
    )


def index_mutation_lifecycle(
    state: OperationLifecycleState,
    *,
    execution_params: dict[str, Any] | None = None,
) -> None:
    """Persist or update a mutation lifecycle entry in the global index."""
    if not _is_indexable(state):
        return
    data = _load_raw()
    entries = list(data.get("entries") or [])
    entry = _entry_from_state(state, execution_params=execution_params)
    key = _dedupe_key(entry)
    entries = [row for row in entries if _dedupe_key(row) != key]
    entries.append(entry)
    entries.sort(key=lambda row: float(row.get("timestamp") or 0), reverse=True)
    data["entries"] = entries[:100]
    _save_raw(data)


def get_execution_params_snapshot(execution_job_id: str) -> dict[str, Any]:
    if not execution_job_id:
        return {}
    for entry in _load_raw().get("entries") or []:
        if str(entry.get("execution_job_id") or "") == execution_job_id:
            snapshot = entry.get("execution_params_snapshot")
            return dict(snapshot) if isinstance(snapshot, dict) else {}
    return {}


def find_recent_mutations(*, limit: int = 10) -> list[OperationLifecycleState]:
    rows: list[OperationLifecycleState] = []
    for entry in _load_raw().get("entries") or []:
        state = _state_from_entry(entry)
        if state.execution_job_id or state.execution_status in {"completed", "running"}:
            rows.append(state)
        if len(rows) >= limit:
            break
    return rows


def logical_target_operation_key(state: OperationLifecycleState) -> str:
    return ":".join(
        [
            _norm(state.provider),
            _norm(state.project),
            _norm(state.environment),
            _norm(state.service),
            _norm(state.operation),
        ]
    )


def dedupe_lifecycles_by_target_operation(
    lifecycles: list[OperationLifecycleState],
) -> list[OperationLifecycleState]:
    """Keep the latest execution per provider/project/environment/service/operation."""
    best: dict[str, OperationLifecycleState] = {}
    for state in lifecycles:
        key = logical_target_operation_key(state)
        existing = best.get(key)
        if existing is None or float(state.updated_at or 0) >= float(existing.updated_at or 0):
            best[key] = state
    rows = list(best.values())
    rows.sort(key=lambda row: float(row.updated_at or 0), reverse=True)
    return rows


def find_latest_logical_mutation(
    *,
    provider: str | None = None,
    operation: str | None = None,
    limit: int = 10,
) -> list[OperationLifecycleState]:
    rows = find_recent_mutations(limit=max(limit * 5, 20))
    if provider:
        rows = [row for row in rows if _norm(row.provider) == _norm(provider)]
    if operation:
        rows = [row for row in rows if _norm(row.operation) == _norm(operation)]
    return dedupe_lifecycles_by_target_operation(rows)[:limit]


def find_latest_mutation_any_session(
    *,
    provider: str | None = None,
    operation: str | None = None,
) -> OperationLifecycleState | None:
    logical = find_latest_logical_mutation(provider=provider, operation=operation, limit=1)
    return logical[0] if logical else None


def find_latest_mutation_by_target(
    *,
    provider: str,
    project: str | None,
    environment: str | None,
    service: str | None,
    operation: str | None = None,
) -> OperationLifecycleState | None:
    best: OperationLifecycleState | None = None
    best_ts = 0.0
    for entry in _load_raw().get("entries") or []:
        if _norm(entry.get("provider")) != _norm(provider):
            continue
        if project and _norm(entry.get("project")) != _norm(project):
            continue
        if environment and _norm(entry.get("environment")) != _norm(environment):
            continue
        if service and _norm(entry.get("service")) != _norm(service):
            continue
        if operation and _norm(entry.get("operation")) != _norm(operation):
            continue
        ts = float(entry.get("timestamp") or 0)
        if ts >= best_ts:
            state = _state_from_entry(entry)
            if state.execution_job_id or state.execution_status in {"completed", "running"}:
                best_ts = ts
                best = state
    return best


def _service_from_text(text: str) -> str | None:
    from aethos_core.post_mutation_verification.verification_intent_router import (
        extract_explicit_path_target,
        is_intent_word,
    )

    raw = (text or "").strip()
    if not raw:
        return None
    explicit = extract_explicit_path_target(raw)
    if explicit is not None:
        return explicit.service
    match = re.search(r"\b(mongodb|postgres(?:ql)?|redis|mysql|speakglobal[\w-]*)\b", raw, re.I)
    if match and not is_intent_word(match.group(1)):
        return match.group(1)
    return None


def find_latest_mutation_for_text(text: str) -> OperationLifecycleState | None:
    raw = (text or "").strip()
    if not raw:
        return find_latest_mutation_any_session()

    from aethos_core.post_mutation_verification.verification_intent_router import (
        extract_explicit_path_target,
        is_intent_word,
    )

    explicit = extract_explicit_path_target(raw)
    if explicit is not None:
        found = find_latest_mutation_by_target(
            provider=explicit.provider or "railway",
            project=explicit.project,
            environment=explicit.environment,
            service=explicit.service,
        )
        if found is not None:
            return found

    service = _service_from_text(raw)
    if service and not is_intent_word(service):
        found = find_latest_mutation_by_target(
            provider="railway",
            project=None,
            environment=None,
            service=service,
        )
        if found is not None:
            return found

    return find_latest_mutation_any_session()


def rebuild_global_lifecycle_index_from_jobs() -> int:
    """Rebuild the global index from in-memory jobs (dev/tests/backfill)."""
    from aethos_core.operation_lifecycle.operation_state_store import build_operation_state_from_job
    from aethos_core.runtime.job_types import uses_mutation_execution, uses_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    count = 0
    for job in job_store.list_all():
        if not uses_mutation_preflight(job.job_type) and not uses_mutation_execution(job.job_type):
            continue
        state = build_operation_state_from_job(job)
        if state is None:
            continue
        params = dict(getattr(job, "params", None) or {}) if uses_mutation_execution(job.job_type) else None
        index_mutation_lifecycle(state, execution_params=params)
        count += 1
    return count


def ensure_global_lifecycle_index_loaded() -> None:
    _load_raw()


def bootstrap_global_lifecycle_index() -> int:
    ensure_global_lifecycle_index_loaded()
    if _load_raw().get("entries"):
        return 0
    return rebuild_global_lifecycle_index_from_jobs()


def reset_global_lifecycle_index_for_tests() -> None:
    global _MEMORY
    _MEMORY = {"entries": [], "updated_at": 0.0}
    path = _index_path()
    if path.is_file():
        path.unlink()


def list_lifecycle_entries_for_session(session_id: str, *, limit: int = 40) -> list[dict[str, Any]]:
    """Session-scoped lifecycle index rows for operator evidence export (FIX 136)."""
    sid = (session_id or "default").strip() or "default"
    entries = list((_load_raw().get("entries") or []))
    scoped = [e for e in entries if isinstance(e, dict) and str(e.get("session_id") or "default") == sid]
    scoped.sort(key=lambda row: float(row.get("timestamp") or 0), reverse=True)
    out: list[dict[str, Any]] = []
    for entry in scoped[:limit]:
        row = dict(entry)
        params = entry.get("execution_params_snapshot")
        if isinstance(params, dict):
            row["execution_params_snapshot"] = _snapshot_params(params)
        out.append(row)
    return out
