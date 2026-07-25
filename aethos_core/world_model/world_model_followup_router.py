# SPDX-License-Identifier: Apache-2.0
"""World-model investigation follow-up routing — owns recall before mutation."""

from __future__ import annotations

import re
import uuid
from typing import Any, Literal

from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.world_state_store import get_active_investigation, load_investigation_state

WorldModelIntent = Literal[
    "recap",
    "next_step",
    "safety_check",
    "evidence_delta",
    "hypothesis_summary",
    "missing_evidence",
    "blocker_summary",
    "investigation_status",
]

_WORLD_MODEL_INTENT_RX: dict[WorldModelIntent, re.Pattern[str]] = {
    "recap": re.compile(
        r"\b(?:what do we know(?: so far)?|what have we learned|summarize (?:the )?investigation|recap(?: the)? investigation)\b",
        re.I,
    ),
    "next_step": re.compile(
        r"\b(?:what\s+(?:should\s+we|we\s+should)\s+do\s+next|what(?:'s| is) the next step|next best action)\b",
        re.I,
    ),
    "evidence_delta": re.compile(
        r"\b(?:what changed|what(?:'s| is) new|what did we learn since)\b",
        re.I,
    ),
    "safety_check": re.compile(
        r"\b(?:"
        r"is restart safe|should (?:i|we) restart|safe to restart|can i restart|"
        r"should we restart again|restart again|another restart|repeat (?:the )?restart|"
        r"is redeploy safe|should (?:i|we) redeploy|safe to redeploy|can i redeploy|"
        r"can we safely restart|is it safe to restart|is it safe to redeploy|"
        r"can we safely redeploy|should we safely restart|should we safely redeploy"
        r")\b",
        re.I,
    ),
    "hypothesis_summary": re.compile(
        r"\b(?:what is the current hypothesis|current hypothesis|leading hypothesis)\b",
        re.I,
    ),
    "missing_evidence": re.compile(
        r"\b(?:what evidence are we missing|missing evidence|evidence gaps?)\b",
        re.I,
    ),
    "blocker_summary": re.compile(
        r"\b(?:what is blocking us|what(?:'s| is) blocking|blockers?)\b",
        re.I,
    ),
    "investigation_status": re.compile(
        r"\b(?:investigation status|status of (?:the )?investigation)\b",
        re.I,
    ),
}

_INTENT_PRIORITY: tuple[WorldModelIntent, ...] = (
    "recap",
    "next_step",
    "safety_check",
    "evidence_delta",
    "hypothesis_summary",
    "missing_evidence",
    "blocker_summary",
    "investigation_status",
)


def classify_world_model_followup(text: str, *, session_id: str = "default") -> WorldModelIntent | None:
    raw = (text or "").strip()
    if not raw:
        return None
    # An explicit multi-agent command-center / orchestration ask is a *fresh*
    # request, not a single-service investigation follow-up. Decline so the
    # world-model lane never claims (and then errors on) the turn.
    from aethos_core.agents.runtime.planner import is_command_center_orchestration_request

    if is_command_center_orchestration_request(raw, session_id=session_id):
        return None
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        verification_preemption_blocks_route,
    )

    if verification_preemption_blocks_route(raw, session_id=session_id):
        return None
    from aethos_core.repair_memory.repair_outcome_router import repair_outcome_preemption_blocks_route

    if repair_outcome_preemption_blocks_route(raw, session_id=session_id):
        return None
    for intent in _INTENT_PRIORITY:
        if _WORLD_MODEL_INTENT_RX[intent].search(raw):
            return intent
    return None


def is_world_model_followup(text: str, *, session_id: str = "default") -> bool:
    try:
        if classify_world_model_followup(text) is None:
            return False
        from aethos_core.world_model.safety_question_classifier import is_safety_question

        if is_safety_question(text):
            return True
        from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context

        if resolve_fallback_context(text=text, session_id=session_id) is not None:
            return True
        return _has_investigation_context(text=text, session_id=session_id)
    except Exception:
        from aethos_core.world_model.safety_question_classifier import is_safety_question

        return classify_world_model_followup(text) is not None and is_safety_question(text)


def route_world_model_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.world_model.safe_world_model_runtime import safe_route_world_model_followup

    return safe_route_world_model_followup(text, session_id=session_id)


def compose_world_model_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Capability handler entrypoint — crash-isolated."""
    from aethos_core.world_model.safe_world_model_runtime import safe_route_world_model_followup

    return safe_route_world_model_followup(text, session_id=session_id)


def resolve_investigation_state(
    *,
    text: str,
    session_id: str,
) -> tuple[InvestigationState | None, list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    state = _load_existing_state(text=text, session_id=session_id)
    if state is not None:
        return state, errors, notes

    row = _resolve_service_row(text=text, session_id=session_id)
    if row is None:
        return None, errors, notes

    target = target_label_from_row(row)
    state = load_investigation_state(session_id=session_id, target=target)
    if state is not None:
        return state, errors, notes

    bootstrapped, bootstrap_errors = _bootstrap_investigation_from_row(row, session_id=session_id)
    if bootstrap_errors:
        errors.extend(bootstrap_errors)
    if bootstrapped is not None:
        notes.append("bootstrapped_from_health_report")
        return bootstrapped, errors, notes

    minimal = InvestigationState(
        target=target,
        session_id=session_id,
        provider="railway",
        service=str(row.get("service") or ""),
        project=str(row.get("project") or ""),
        environment=str(row.get("environment") or ""),
        active_investigation=True,
        evidence=["failed_runtime_status"] if str(row.get("status") or "").lower() in {"failed", "crashed"} else [],
    )
    notes.append("partial_bootstrap")
    return minimal, errors, notes


def _load_existing_state(*, text: str, session_id: str) -> InvestigationState | None:
    from aethos_core.world_model.investigation_engine import get_investigation_for_text

    return get_investigation_for_text(text=text, session_id=session_id)


def _has_investigation_context(*, text: str, session_id: str) -> bool:
    if _load_existing_state(text=text, session_id=session_id) is not None:
        return True
    if _resolve_service_row(text=text, session_id=session_id) is not None:
        return True
    return get_active_investigation(session_id=session_id) is not None


def _resolve_service_row(*, text: str, session_id: str) -> dict[str, Any] | None:
    from aethos_core.failed_service_investigation.global_preemption import detect_failed_service_reference

    ref = detect_failed_service_reference(text, session_id=session_id)
    if ref and ref.rows:
        return dict(ref.rows[0])

    active = get_active_investigation(session_id=session_id)
    if active is not None:
        return {
            "service": active.service,
            "project": active.project,
            "environment": active.environment,
            "status": "failed",
        }
    return None


def _bootstrap_investigation_from_row(
    row: dict[str, Any],
    *,
    session_id: str,
) -> tuple[InvestigationState | None, list[str]]:
    errors: list[str] = []
    try:
        from aethos_core.failed_service_investigation.failed_service_diagnosis import collect_failed_service_evidence
        from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService
        from aethos_core.world_model.investigation_engine import update_investigation_from_evidence

        target = ResolvedFailedService(row=row)
        evidence = collect_failed_service_evidence(target)
        state = update_investigation_from_evidence(
            session_id=session_id,
            evidence=evidence,
            investigation_kind="world_model_recall",
            operator_intent="world_model_followup",
        )
        return state, errors
    except Exception as exc:
        errors.append(str(exc))
        return None, errors


def _compose_followup_reply(state: InvestigationState, *, intent: WorldModelIntent) -> tuple[str, str]:
    from aethos_core.world_model.investigation_planner import plan_next_action_from_state
    from aethos_core.world_model.operational_story import (
        compose_blocker_summary,
        compose_hypothesis_summary,
        compose_investigation_recap,
        compose_investigation_status,
        compose_missing_evidence_summary,
        compose_next_step_answer,
        compose_restart_safety_answer,
        compose_what_changed_recap,
    )

    if intent == "recap":
        return compose_investigation_recap(state), "world_model_investigation_recap"
    if intent == "next_step":
        return compose_next_step_answer(state), "world_model_next_action"
    if intent == "evidence_delta":
        previous = list(state.meta.get("previous_evidence") or [])
        return compose_what_changed_recap(state, previous_evidence=previous), "world_model_what_changed"
    if intent == "safety_check":
        return compose_restart_safety_answer(state), "world_model_restart_safety"
    if intent == "hypothesis_summary":
        return compose_hypothesis_summary(state), "world_model_hypothesis_summary"
    if intent == "missing_evidence":
        return compose_missing_evidence_summary(state), "world_model_missing_evidence"
    if intent == "blocker_summary":
        return compose_blocker_summary(state), "world_model_blocker_summary"
    action, _key = plan_next_action_from_state(state)
    if not state.next_best_action:
        state.next_best_action = action
    return compose_investigation_status(state), "world_model_investigation_status"


def _meta_from_state(state: InvestigationState, *, intent: str, degraded: bool) -> dict[str, str]:
    correlation_id = uuid.uuid4().hex[:8]
    meta = {
        "route_id": "world_model_investigation",
        "matched_module": "world_model.world_model_followup_router",
        "world_model_target": state.target,
        "confidence_score": f"{state.confidence_score:.2f}",
        "confidence_label": state.confidence_label,
        "active_investigation": "true",
        "world_model_correlation_id": correlation_id,
        "blocked_routes": "operation_preflight,explicit_mutation,continuity_reconstruction,generic_fix_plan",
    }
    if state.service:
        meta["service"] = state.service
    if state.project:
        meta["project"] = state.project
    if state.environment:
        meta["environment"] = state.environment
    if degraded:
        meta["world_model_degraded"] = "true"
    return meta


def is_mutation_safety_question(text: str) -> bool:
    """True when text asks about mutation safety rather than commanding one."""
    from aethos_core.world_model.safety_question_classifier import is_safety_question

    return is_safety_question(text)
