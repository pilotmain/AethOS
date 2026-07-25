# SPDX-License-Identifier: Apache-2.0
"""Crash-isolated world-model follow-up runtime."""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any

from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_model_followup_router import (
    WorldModelIntent,
    _compose_followup_reply,
    _meta_from_state,
    _resolve_service_row,
    classify_world_model_followup,
)
from aethos_core.world_model.world_state_store import (
    get_active_investigation,
    load_investigation_state,
    quarantine_session_store,
    save_investigation_state,
)

_log = logging.getLogger(__name__)

_BOOTSTRAP_TIMEOUT_SECONDS = 8.0


def safe_route_world_model_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Never raises — returns bounded fallback when the world-model route fails."""
    # Explicit multi-agent orchestration requests belong to the agent-runtime
    # orchestration lane, never to single-service world-model recall. Decline up
    # front so this router cannot claim (and then degrade) a fresh orchestration
    # ask. A genuine single-service follow-up still routes here.
    try:
        from aethos_core.agents.runtime.planner import is_command_center_orchestration_request

        if is_command_center_orchestration_request(text, session_id=session_id):
            return None
    except Exception:  # pragma: no cover - detector must never break recall
        _log.warning("Command-center orchestration probe failed in world-model runtime", exc_info=True)

    from aethos_core.post_mutation_verification.global_verification_preemption import (
        verification_preemption_blocks_route,
    )

    # Classification must not crash the turn. If the preemption probe or the
    # follow-up classifier raises, decline cleanly (return ``None``) so the next
    # router handles the request — never bubble up into the cognition crash
    # boundary, which would mask an unrelated fresh request as a world-model recall.
    try:
        if verification_preemption_blocks_route(text, session_id=session_id):
            return None
        intent = classify_world_model_followup(text, session_id=session_id)
    except Exception:
        _log.warning("World-model follow-up classification failed; declining route", exc_info=True)
        return None
    if intent is None:
        return None

    partial_context: dict[str, Any] = {"session_id": session_id, "intent": intent}
    try:
        if not _safe_has_investigation_context(text=text, session_id=session_id, partial_context=partial_context):
            return None

        state, load_errors, recovery_notes, recovery_meta = safe_recover_or_rebuild_investigation(
            text=text,
            session_id=session_id,
        )
        partial_context["state"] = state
        partial_context["row"] = recovery_meta.get("row")
        if state is None:
            return _fallback_reply(
                error="investigation_state_unavailable",
                partial_context=partial_context,
                recovery_meta=recovery_meta,
            )

        body, reply_intent = _safe_compose_followup_reply(
            state,
            intent=intent,
            partial_context=partial_context,
            text=text,
        )
        body = _apply_recovery_prefix(
            body,
            state=state,
            load_errors=load_errors,
            recovery_notes=recovery_notes,
            recovery_meta=recovery_meta,
        )
        meta = _meta_from_state(state, intent=reply_intent, degraded=bool(load_errors or recovery_meta.get("recovered")))
        meta.update(_recovery_meta_to_strings(recovery_meta))
        return body, reply_intent, meta
    except Exception as exc:
        _log.exception("World-model follow-up crashed for session=%s", session_id)
        return _fallback_reply(
            error=str(exc),
            partial_context=partial_context,
            recovery_meta={"recovered": True, "fallback_used": "exception_isolation", "error_type": type(exc).__name__},
        )


def safe_load_investigation_state(
    *,
    session_id: str,
    target: str,
) -> tuple[InvestigationState | None, str | None, bool]:
    """Load investigation state without raising; quarantine unreadable session files."""
    try:
        state = load_investigation_state(session_id=session_id, target=target)
        if state is not None:
            return state, None, False
    except Exception as exc:
        return None, str(exc), False

    from aethos_core.world_model.world_state_store import session_store_is_corrupt

    if session_store_is_corrupt(session_id=session_id):
        quarantined = quarantine_session_store(session_id=session_id, reason="corrupt_investigation_state")
        return None, "corrupt_investigation_state", quarantined
    return None, None, False


def safe_recover_or_rebuild_investigation(
    *,
    text: str,
    session_id: str,
) -> tuple[InvestigationState | None, list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    notes: list[str] = []
    recovery_meta: dict[str, Any] = {"recovered": False}

    row = _safe_resolve_service_row(text=text, session_id=session_id)
    if row is None:
        from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context

        fallback = resolve_fallback_context(text=text, session_id=session_id)
        if fallback is not None:
            row = {
                "service": fallback.service,
                "project": fallback.project,
                "environment": fallback.environment,
                "status": fallback.status,
                "provider": fallback.provider,
            }
            recovery_meta["row"] = row
            recovery_meta["fallback_context"] = fallback.to_dict()
    if row is not None:
        recovery_meta.setdefault("row", row)

    state = _safe_load_existing_state(text=text, session_id=session_id, row=row)
    if state is not None:
        return state, errors, notes, recovery_meta

    if row is None:
        return None, errors, notes, recovery_meta

    target = target_label_from_row(row)
    state, load_error, quarantined = safe_load_investigation_state(session_id=session_id, target=target)
    if quarantined:
        errors.append(load_error or "corrupt_investigation_state")
        notes.append("quarantined_corrupt_state")
        recovery_meta.update(
            {
                "recovered": True,
                "fallback_used": "rebuild_from_health_report",
                "error_type": "corrupt_investigation_state",
            }
        )
    if state is not None:
        return state, errors, notes, recovery_meta

    bootstrapped, bootstrap_errors, timed_out = _safe_bootstrap_investigation_from_row(row, session_id=session_id)
    if bootstrap_errors:
        errors.extend(bootstrap_errors)
    if timed_out:
        notes.append("bootstrap_timed_out")
        recovery_meta["error_type"] = "bootstrap_timeout"
    if bootstrapped is not None:
        notes.append("bootstrapped_from_health_report")
        return bootstrapped, errors, notes, recovery_meta

    minimal = _minimal_state_from_row(row, session_id=session_id, recovery_meta=recovery_meta)
    notes.append("partial_bootstrap")
    recovery_meta.update(
        {
            "recovered": True,
            "fallback_used": "rebuild_from_health_report",
            "error_type": recovery_meta.get("error_type") or "evidence_source_failure",
        }
    )
    try:
        save_investigation_state(minimal)
    except Exception as exc:
        errors.append(str(exc))
    return minimal, errors, notes, recovery_meta


def compose_world_model_error_fallback(
    error: str,
    *,
    partial_context: dict[str, Any] | None = None,
) -> str:
    partial_context = partial_context or {}
    state = partial_context.get("state")
    row = partial_context.get("row") or {}
    intent = partial_context.get("intent")
    service = ""
    project = ""
    if isinstance(state, InvestigationState):
        service = state.service or service
        project = state.project or project
    if not service:
        service = str(row.get("service") or "the service")
    if not project:
        project = str(row.get("project") or "")

    if intent == "safety_check":
        return (
            "Not yet.\n\n"
            f"Restart is not recommended because investigation recall hit an internal error "
            f"(`{error}`) while loading **{service}** state.\n\n"
            "Safer next step:\n"
            "Refresh service events and inspect failure-window logs before any mutation."
        )

    if intent == "next_step":
        return (
            "Best next step:\n"
            "Refresh Railway service events and fetch logs around the latest failed deployment window "
            f"for **{service}**.\n\n"
            f"I could not load the full investigation state ({error})."
        )

    opener = f"We're investigating **{service}**"
    if project:
        opener += f" in **{project}**"
    opener += "."
    return (
        f"{opener}\n\n"
        f"I could not load the full saved investigation state ({error}).\n\n"
        "Reliable context:\n"
        f"- **{service}** remains under active investigation.\n"
        "- Use fresh Railway logs and service events to rebuild confidence.\n\n"
        "Best next step:\n"
        "Refresh Railway service events and fetch logs around the latest failed deployment window.\n\n"
        "No mutation is recommended yet."
    )


def _safe_has_investigation_context(
    *,
    text: str,
    session_id: str,
    partial_context: dict[str, Any],
) -> bool:
    try:
        from aethos_core.world_model.safety_question_classifier import is_safety_question

        if is_safety_question(text):
            return True
        if _safe_load_existing_state(text=text, session_id=session_id) is not None:
            return True
        row = _safe_resolve_service_row(text=text, session_id=session_id)
        if row is not None:
            partial_context["row"] = row
            return True
        from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context

        fallback = resolve_fallback_context(text=text, session_id=session_id)
        if fallback is not None:
            partial_context["fallback_context"] = fallback.to_dict()
            partial_context["row"] = {
                "service": fallback.service,
                "project": fallback.project,
                "environment": fallback.environment,
                "status": fallback.status,
                "provider": fallback.provider,
            }
            return True
        return get_active_investigation(session_id=session_id) is not None
    except Exception as exc:
        _log.warning("World-model context probe failed: %s", exc)
        from aethos_core.world_model.safety_question_classifier import is_safety_question

        return is_safety_question(text) or partial_context.get("row") is not None


def _safe_load_existing_state(
    *,
    text: str,
    session_id: str,
    row: dict[str, Any] | None = None,
) -> InvestigationState | None:
    try:
        from aethos_core.world_model.investigation_engine import get_investigation_for_text

        state = get_investigation_for_text(text=text, session_id=session_id)
        if state is not None:
            return state
    except Exception as exc:
        _log.warning("Existing investigation load failed: %s", exc)

    if row is None:
        return None
    target = target_label_from_row(row)
    try:
        return load_investigation_state(session_id=session_id, target=target)
    except Exception as exc:
        _log.warning("Target investigation load failed: %s", exc)
        return None


def _safe_resolve_service_row(*, text: str, session_id: str) -> dict[str, Any] | None:
    try:
        return _resolve_service_row(text=text, session_id=session_id)
    except Exception as exc:
        _log.warning("Service row resolution failed: %s", exc)
        return None


def _safe_bootstrap_investigation_from_row(
    row: dict[str, Any],
    *,
    session_id: str,
) -> tuple[InvestigationState | None, list[str], bool]:
    from aethos_core.world_model.world_model_followup_router import _bootstrap_investigation_from_row

    errors: list[str] = []
    timed_out = False
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_bootstrap_investigation_from_row, row, session_id=session_id)
            state, bootstrap_errors = future.result(timeout=_BOOTSTRAP_TIMEOUT_SECONDS)
        errors.extend(bootstrap_errors)
        return state, errors, timed_out
    except FuturesTimeoutError:
        timed_out = True
        errors.append("evidence collection timed out")
        return None, errors, timed_out
    except Exception as exc:
        errors.append(str(exc))
        return None, errors, timed_out


def _safe_compose_followup_reply(
    state: InvestigationState,
    *,
    intent: WorldModelIntent,
    partial_context: dict[str, Any],
    text: str = "",
) -> tuple[str, str]:
    try:
        from aethos_core.repair_memory.recommendation_guard import (
            compose_did_restart_help_reply,
            compose_restart_again_reply,
            is_did_restart_help_question,
            is_restart_again_question,
        )

        if is_restart_again_question(text):
            blocked = compose_restart_again_reply(state)
            if blocked:
                return blocked, "world_model_restart_safety"
        if is_did_restart_help_question(text):
            help_reply = compose_did_restart_help_reply(state)
            if help_reply:
                return help_reply, "world_model_restart_safety"
        return _compose_followup_reply(state, intent=intent)
    except Exception as exc:
        _log.warning("World-model compose failed: %s", exc)
        partial_context["compose_error"] = str(exc)
        body = compose_world_model_error_fallback(str(exc), partial_context={"state": state, "intent": intent})
        intent_map = {
            "recap": "world_model_investigation_recap",
            "next_step": "world_model_next_action",
            "safety_check": "world_model_restart_safety",
            "evidence_delta": "world_model_what_changed",
            "hypothesis_summary": "world_model_hypothesis_summary",
            "missing_evidence": "world_model_missing_evidence",
            "blocker_summary": "world_model_blocker_summary",
            "investigation_status": "world_model_investigation_status",
        }
        return body, intent_map.get(intent, "world_model_investigation_recap")


def _apply_recovery_prefix(
    body: str,
    *,
    state: InvestigationState,
    load_errors: list[str],
    recovery_notes: list[str],
    recovery_meta: dict[str, Any],
) -> str:
    service = state.service or state.target
    if recovery_meta.get("error_type") == "corrupt_investigation_state":
        prefix = (
            f"I found the **{service}** investigation target, but the saved investigation state was unreadable.\n\n"
            "I rebuilt the context from Railway health and logs.\n\n"
        )
        if not body.startswith(prefix):
            body = prefix + body
    elif load_errors:
        prefix = (
            f"I found the **{service}** investigation state, but one evidence source failed to load. "
            "Here is the reliable context I have:\n\n"
        )
        if not body.startswith(prefix):
            body = prefix + body
    elif "bootstrapped_from_health_report" in recovery_notes:
        intro = f"We're investigating **{state.service or 'the service'}**"
        if state.project:
            intro += f" in **{state.project}**"
        intro += "."
        if not body.startswith(intro):
            body = f"{intro}\n\n{body}"
    return body


def _minimal_state_from_row(
    row: dict[str, Any],
    *,
    session_id: str,
    recovery_meta: dict[str, Any] | None = None,
) -> InvestigationState:
    target = target_label_from_row(row)
    evidence: list[str] = []
    status = str(row.get("status") or row.get("health") or "").lower()
    if status in {"failed", "crashed", "error", "unhealthy"}:
        evidence.append("failed_runtime_status")
    recommendation = "Refresh Railway service events and fetch logs around the latest failed deployment window."
    fallback_ctx = dict((recovery_meta or {}).get("fallback_context") or {})
    if fallback_ctx.get("evidence_summary"):
        from aethos_core.world_model.fallback_context_resolver import _evidence_tags_from_summary

        evidence = sorted(set(evidence) | set(_evidence_tags_from_summary(str(fallback_ctx["evidence_summary"]))))
    if fallback_ctx.get("recommendation"):
        recommendation = str(fallback_ctx["recommendation"])
    elif "wiredtiger" in str(fallback_ctx.get("evidence_summary") or "").lower():
        evidence.append("fresh_wiredtiger_logs")
        evidence.append("stale_service_events")
    return InvestigationState(
        target=target,
        session_id=session_id,
        provider=str(row.get("provider") or "railway"),
        service=str(row.get("service") or ""),
        project=str(row.get("project") or ""),
        environment=str(row.get("environment") or ""),
        active_investigation=True,
        confidence_score=0.42,
        confidence_label="bounded",
        evidence=sorted(set(evidence)),
        missing_evidence=[
            "recent service events / exit code",
            "logs around the actual failure window",
            "storage/volume health",
        ],
        next_best_action=recommendation,
    )


def _fallback_reply(
    *,
    error: str,
    partial_context: dict[str, Any],
    recovery_meta: dict[str, Any],
) -> tuple[str, str, dict[str, str]]:
    intent = partial_context.get("intent") or "recap"
    body = compose_world_model_error_fallback(error, partial_context=partial_context)
    intent_map = {
        "recap": "world_model_investigation_recap",
        "next_step": "world_model_next_action",
        "safety_check": "world_model_restart_safety",
        "evidence_delta": "world_model_what_changed",
        "hypothesis_summary": "world_model_hypothesis_summary",
        "missing_evidence": "world_model_missing_evidence",
        "blocker_summary": "world_model_blocker_summary",
        "investigation_status": "world_model_investigation_status",
    }
    reply_intent = intent_map.get(intent, "world_model_investigation_recap")
    state = partial_context.get("state")
    row = partial_context.get("row") or {}
    meta = {
        "route_id": "world_model_investigation",
        "matched_module": "world_model.safe_world_model_runtime",
        "active_investigation": "true",
        "world_model_degraded": "true",
        "world_model_correlation_id": uuid.uuid4().hex[:8],
        "blocked_routes": "operation_preflight,explicit_mutation,continuity_reconstruction,generic_fix_plan",
    }
    if isinstance(state, InvestigationState):
        meta["world_model_target"] = state.target
        meta["service"] = state.service
        meta["project"] = state.project
        meta["environment"] = state.environment
    elif row:
        meta["service"] = str(row.get("service") or "")
        meta["project"] = str(row.get("project") or "")
        meta["environment"] = str(row.get("environment") or "")
    meta.update(_recovery_meta_to_strings(recovery_meta))
    return body, reply_intent, meta


def _recovery_meta_to_strings(recovery_meta: dict[str, Any]) -> dict[str, str]:
    meta: dict[str, str] = {}
    if recovery_meta.get("recovered"):
        meta["recovered"] = "true"
    if recovery_meta.get("fallback_used"):
        meta["fallback_used"] = str(recovery_meta["fallback_used"])
    if recovery_meta.get("error_type"):
        meta["error_type"] = str(recovery_meta["error_type"])
    return meta
