# SPDX-License-Identifier: Apache-2.0
"""Discover verification lifecycle context across sessions and global index."""

from __future__ import annotations

from aethos_core.operation_lifecycle.global_lifecycle_index import (
    dedupe_lifecycles_by_target_operation,
    ensure_global_lifecycle_index_loaded,
    find_latest_logical_mutation,
    find_latest_mutation_any_session,
    find_latest_mutation_by_target,
    find_latest_mutation_for_text,
    find_recent_mutations,
)
from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState


def _verifiable(state: OperationLifecycleState | None) -> bool:
    if state is None:
        return False
    if state.execution_job_id:
        return True
    if state.execution_status in {"completed", "running"}:
        return True
    if state.verification_status not in {"", "none"}:
        return True
    return state.canonical_state in {
        "execution_completed",
        "verification_running",
        "stabilizing",
        "verified",
    }


def global_mutation_lifecycle_exists() -> bool:
    ensure_global_lifecycle_index_loaded()
    return find_latest_mutation_any_session() is not None


def discover_verification_lifecycle(
    text: str,
    *,
    session_id: str = "default",
) -> OperationLifecycleState | None:
    """Resolve lifecycle for verification prompts using global discovery order."""
    ensure_global_lifecycle_index_loaded()
    raw = (text or "").strip()

    from aethos_core.post_mutation_verification.verification_intent_router import (
        extract_explicit_path_target,
        get_pending_verification_request,
    )

    pending = get_pending_verification_request(session_id)
    if pending is not None:
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

    from aethos_core.operation_lifecycle.lifecycle_resolver import get_latest_operation_state

    session_state = get_latest_operation_state(session_id=session_id, text=None)
    if _verifiable(session_state):
        return session_state

    indexed = find_latest_mutation_for_text(raw)
    if _verifiable(indexed):
        return indexed

    explicit = extract_explicit_path_target(raw)
    if explicit is not None:
        found = find_latest_mutation_by_target(
            provider=explicit.provider or "railway",
            project=explicit.project,
            environment=explicit.environment,
            service=explicit.service,
        )
        if _verifiable(found):
            return found

    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id)
        if trace:
            service = str(trace.get("service") or trace.get("matched_target") or "").strip()
            project = str(trace.get("project") or "").strip()
            environment = str(trace.get("environment") or "production").strip()
            provider = str(trace.get("provider") or "railway").strip()
            if service and service != "—":
                found = find_latest_mutation_by_target(
                    provider=provider,
                    project=project or None,
                    environment=environment or None,
                    service=service.split("/")[-1].strip() if " / " in service else service,
                )
                if _verifiable(found):
                    return found
    except Exception:
        pass

    latest = find_latest_mutation_any_session()
    if _verifiable(latest):
        return latest
    return None


def list_discovered_recent_mutations(*, session_id: str = "default", limit: int = 5) -> list[OperationLifecycleState]:
    ensure_global_lifecycle_index_loaded()
    rows = dedupe_lifecycles_by_target_operation(find_recent_mutations(limit=max(limit * 5, 20)))
    if rows:
        return rows[:limit]
    from aethos_core.operation_lifecycle.lifecycle_resolver import list_recent_mutation_lifecycles

    return dedupe_lifecycles_by_target_operation(list_recent_mutation_lifecycles(session_id=session_id, limit=limit))
