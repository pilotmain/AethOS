# SPDX-License-Identifier: Apache-2.0
"""Resolve latest operation lifecycle for targets and duplicate detection."""

from __future__ import annotations

import re
from time import time
from typing import Any

from aethos_core.operation_lifecycle.operation_state_store import (
    OperationLifecycleState,
    build_operation_state_from_job,
    list_session_operation_states,
    refresh_operation_state_for_session,
    upsert_operation_state,
)
from aethos_core.operations.mutations.lifecycle_authority import (
    AWAITING_APPROVAL,
    EXECUTION_COMPLETED_STATE,
    EXECUTION_FAILED_STATE,
    STABILIZING_STATE,
    VERIFICATION_RUNNING_STATE,
    VERIFIED_STATE,
)
from aethos_core.operations.preflight_supersede import preflight_match_key

RECENT_COMPLETION_WINDOW_SEC = 3600.0

_COMPLETED_CANONICAL = {
    EXECUTION_COMPLETED_STATE,
    VERIFICATION_RUNNING_STATE,
    STABILIZING_STATE,
    VERIFIED_STATE,
}

_VERIFIED_CANONICAL = {
    VERIFIED_STATE,
}

_OVERRIDE_RX = re.compile(
    r"\b("
    r"restart\s+again"
    r"|another\s+restart"
    r"|force\s+restart"
    r"|restart\s+anyway"
    r"|do\s+it\s+again"
    r"|run\s+again"
    r")\b",
    re.I,
)

_SERVICE_RX = re.compile(
    r"\b(mongodb|postgres(?:ql)?|redis|mysql|speakglobal[\w-]*)\b",
    re.I,
)

_VERIFICATION_CONTEXT_RX = re.compile(
    r"\b("
    r"after\s+restart|post[- ]restart|what\s+changed|fetch\s+logs"
    r"|verify\s+health|check\s+health|did\s+it\s+recover|did\s+it\s+hold"
    r")\b",
    re.I,
)


def _norm(value: str | None) -> str:
    return str(value or "").strip().lower()


def _service_phrase_from_text(text: str) -> str | None:
    from aethos_core.post_mutation_verification.verification_intent_router import (
        extract_explicit_path_target,
        is_intent_word,
    )

    raw = text or ""
    if _VERIFICATION_CONTEXT_RX.search(raw):
        explicit = extract_explicit_path_target(raw)
        if explicit is not None:
            return explicit.service
        return None

    match = _SERVICE_RX.search(raw)
    if match:
        candidate = match.group(1)
        if not is_intent_word(candidate):
            return candidate
    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase

    phrase = extract_operational_resource_phrase(text)
    if phrase and not phrase.startswith("job-") and not is_intent_word(phrase):
        return phrase
    return None


def _matches_target(state: OperationLifecycleState, *, service: str | None, provider: str | None) -> bool:
    if provider and _norm(state.provider) != _norm(provider):
        return False
    if not service:
        return True
    needle = _norm(service)
    hay = _norm(state.service)
    if needle == hay:
        return True
    return needle in hay or hay in needle


def _merge_states(
    preflight_state: OperationLifecycleState | None,
    execution_state: OperationLifecycleState | None,
) -> OperationLifecycleState | None:
    if execution_state and preflight_state:
        merged = OperationLifecycleState(**execution_state.to_dict())
        merged.preflight_job_id = preflight_state.preflight_job_id or execution_state.preflight_job_id
        if not merged.project:
            merged.project = preflight_state.project
        if not merged.service:
            merged.service = preflight_state.service
        if preflight_state.credential_blocked and merged.execution_status != "completed":
            merged.credential_blocked = True
            merged.approval_status = preflight_state.approval_status
        if execution_state.latest_summary:
            merged.latest_summary = execution_state.latest_summary
        merged.updated_at = max(preflight_state.updated_at, execution_state.updated_at)
        return merged
    return execution_state or preflight_state


def _find_jobs_for_target(
    *,
    session_id: str,
    provider: str | None = None,
    service: str | None = None,
    operation: str | None = None,
) -> tuple[Any | None, Any | None]:
    from aethos_core.runtime.job_types import uses_mutation_execution, uses_mutation_preflight
    from aethos_core.runtime.jobs import job_store

    latest_preflight = None
    latest_execution = None
    latest_pf_ts = 0.0
    latest_exec_ts = 0.0

    for job in job_store.list_all():
        if str(getattr(job, "session_id", "") or "") != session_id:
            continue
        state = build_operation_state_from_job(job)
        if state is None:
            continue
        if not _matches_target(state, service=service, provider=provider):
            continue
        if operation and _norm(state.operation) != _norm(operation):
            continue
        ts = float(getattr(job, "updated_at", 0) or 0)
        if uses_mutation_preflight(job.job_type):
            if job.params.get("is_current") is False:
                continue
            if ts >= latest_pf_ts:
                latest_pf_ts = ts
                latest_preflight = job
        elif uses_mutation_execution(job.job_type):
            if ts >= latest_exec_ts:
                latest_exec_ts = ts
                latest_execution = job

    return latest_preflight, latest_execution


def get_latest_operation_state(
    *,
    session_id: str = "default",
    provider: str | None = None,
    service: str | None = None,
    operation: str | None = None,
    text: str | None = None,
) -> OperationLifecycleState | None:
    """Resolve the freshest lifecycle state for a session/target."""
    refresh_operation_state_for_session(session_id)

    if text and not service:
        service = _service_phrase_from_text(text)

    preflight_job, execution_job = _find_jobs_for_target(
        session_id=session_id,
        provider=provider,
        service=service,
        operation=operation,
    )
    pf_state = build_operation_state_from_job(preflight_job) if preflight_job else None
    exec_state = build_operation_state_from_job(execution_job) if execution_job else None
    merged = _merge_states(pf_state, exec_state)
    if merged:
        return upsert_operation_state(merged)

    states = list_session_operation_states(session_id)
    for state in states:
        if _matches_target(state, service=service, provider=provider):
            if operation and _norm(state.operation) != _norm(operation):
                continue
            return state
    return states[0] if states and not service and not provider else None


def find_latest_mutation_lifecycle_across_sessions(
    *,
    session_id: str = "default",
    provider: str | None = None,
    service: str | None = None,
) -> OperationLifecycleState | None:
    """Resolve the freshest mutation lifecycle, including cross-session fallback."""
    from aethos_core.operation_lifecycle.global_lifecycle_index import (
        ensure_global_lifecycle_index_loaded,
        find_latest_mutation_any_session,
        find_latest_mutation_by_target,
    )
    from aethos_core.post_mutation_verification.verification_context_discovery import discover_verification_lifecycle

    ensure_global_lifecycle_index_loaded()

    direct = get_latest_operation_state(
        session_id=session_id,
        provider=provider,
        service=service,
        text=None,
    )
    if direct is not None and (direct.execution_job_id or direct.execution_status in {"completed", "running"}):
        return direct

    if service:
        indexed = find_latest_mutation_by_target(
            provider=provider or "railway",
            project=None,
            environment=None,
            service=service,
        )
        if indexed is not None:
            return indexed

    indexed = find_latest_mutation_any_session(provider=provider)
    if indexed is not None:
        return indexed

    discovered = discover_verification_lifecycle("", session_id=session_id)
    if discovered is not None:
        return discovered

    from aethos_core.runtime.job_types import uses_mutation_execution
    from aethos_core.runtime.jobs import job_store

    best_state: OperationLifecycleState | None = None
    best_ts = 0.0
    for job in job_store.list_all():
        if not uses_mutation_execution(getattr(job, "job_type", "")):
            continue
        params = dict(getattr(job, "params", None) or {})
        if params.get("executed") is not True and params.get("execution_state") not in {
            "execution_completed",
            "stabilizing",
        }:
            continue
        state = build_operation_state_from_job(job)
        if state is None:
            continue
        if provider and _norm(state.provider) != _norm(provider):
            continue
        if service and not _matches_target(state, service=service, provider=provider):
            continue
        ts = float(getattr(job, "updated_at", 0) or 0)
        if ts >= best_ts:
            best_ts = ts
            best_state = upsert_operation_state(state)
    return best_state


def list_recent_mutation_lifecycles(
    *,
    session_id: str = "default",
    limit: int = 5,
) -> list[OperationLifecycleState]:
    from aethos_core.post_mutation_verification.verification_context_discovery import (
        list_discovered_recent_mutations,
    )

    return list_discovered_recent_mutations(session_id=session_id, limit=limit)


def is_operation_verified(state: OperationLifecycleState | None) -> bool:
    if state is None:
        return False
    return state.verification_status == "verified" or state.canonical_state in _VERIFIED_CANONICAL


def has_recent_mutation_execution(
    state: OperationLifecycleState | None,
    *,
    within_seconds: float = RECENT_COMPLETION_WINDOW_SEC,
) -> bool:
    """Recent governed mutation was submitted (may still be unverified on the provider)."""
    if state is None:
        return False
    if state.execution_status not in {"completed", "running"}:
        return False
    if state.canonical_state in _COMPLETED_CANONICAL or state.executed_recently(within_seconds):
        if state.completed_at:
            return (time() - state.completed_at) <= within_seconds
        return (time() - state.updated_at) <= within_seconds
    return False


def has_completed_operation(
    state: OperationLifecycleState | None,
    *,
    within_seconds: float = RECENT_COMPLETION_WINDOW_SEC,
) -> bool:
    """Provider-verified completion only — do not use for optimistic success claims."""
    if not has_recent_mutation_execution(state, within_seconds=within_seconds):
        return False
    return is_operation_verified(state)


def is_waiting_for_approval(state: OperationLifecycleState | None) -> bool:
    if state is None:
        return False
    if state.execution_status in {"completed", "running"}:
        return False
    if state.credential_blocked:
        return True
    return state.approval_status == "pending" or state.canonical_state == AWAITING_APPROVAL


def is_blocked_by_credentials(state: OperationLifecycleState | None) -> bool:
    if state is None:
        return False
    if state.execution_status == "completed":
        return False
    return state.credential_blocked


def is_duplicate_mutation_request(
    text: str,
    *,
    session_id: str = "default",
    provider: str | None = None,
    operation: str | None = None,
    service: str | None = None,
) -> tuple[bool, OperationLifecycleState | None]:
    """Return (is_duplicate, state) when a recent completed operation matches."""
    from aethos_core.post_mutation_verification.verification_intent_router import (
        is_post_mutation_verification_intent,
    )

    if is_post_mutation_verification_intent(text, session_id=session_id):
        return False

    from aethos_core.post_mutation_verification.verification_intent_router import (
        has_pending_verification_disambiguation,
        looks_like_verification_target_selection,
    )

    if has_pending_verification_disambiguation(session_id=session_id) or looks_like_verification_target_selection(text):
        return False, None

    if _OVERRIDE_RX.search(text or "") or re.search(r"\bagain\b", text or "", re.I):
        return False, None

    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb

    if not has_explicit_mutation_verb(text):
        return False, None

    if not service:
        service = _service_phrase_from_text(text)

    state = get_latest_operation_state(
        session_id=session_id,
        provider=provider,
        service=service,
        operation=operation,
        text=text,
    )
    if state and has_recent_mutation_execution(state):
        return True, state
    return False, None


def compose_duplicate_mutation_reply(state: OperationLifecycleState) -> str:
    target = state.target_path()
    op = state.operation.replace("_", " ")
    elapsed = _elapsed_phrase(state.completed_at or state.updated_at)
    verified = is_operation_verified(state)
    if verified:
        headline = f"**{target}** was already **{op}** successfully {elapsed}."
    else:
        headline = (
            f"A **{op}** for **{target}** was already requested {elapsed}. "
            "The provider accepted the command, but **Railway deployment is not confirmed yet**."
        )
    lines = [
        headline,
        "",
        "**Current state:**",
        f"- execution: {state.execution_status}",
        f"- verification: {state.verification_status}",
    ]
    if state.latest_summary:
        lines.append(f"- latest: {state.latest_summary}")
    lines.extend(
        [
            "",
            "Do you want to:",
            "- verify health",
            "- fetch logs",
        ]
    )
    if verified:
        lines.append(f"- perform another {op} anyway")
    else:
        lines.append(f"- wait for verification to finish before requesting another {op}")
    lines.extend(
        [
            "",
            f"Say **{op} again** if you want a new governed preflight anyway.",
        ]
    )
    return "\n".join(lines)


def _elapsed_phrase(ts: float) -> str:
    delta = max(0, int(time() - ts))
    if delta < 60:
        return f"{delta} seconds ago"
    if delta < 3600:
        mins = max(1, delta // 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    hours = max(1, delta // 3600)
    return f"{hours} hour{'s' if hours != 1 else ''} ago"
