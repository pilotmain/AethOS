# SPDX-License-Identifier: Apache-2.0
"""Investigation state engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.world_model.confidence_tracker import confidence_label, score_from_evidence
from aethos_core.world_model.evidence_memory import evidence_tags_from_payload, merge_evidence_memory
from aethos_core.world_model.hypothesis_graph import evolve_hypotheses
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row
from aethos_core.world_model.investigation_planner import mark_completed_check, plan_next_action_from_state
from aethos_core.world_model.world_state_store import load_investigation_state, save_investigation_state


def classify_world_model_intent(text: str) -> str | None:
    from aethos_core.world_model.world_model_followup_router import classify_world_model_followup

    intent = classify_world_model_followup(text)
    if intent is None:
        return None
    mapping = {
        "recap": "what_do_we_know",
        "next_step": "what_next",
        "evidence_delta": "what_changed",
        "safety_check": "restart_safety",
    }
    return mapping.get(intent, intent)


def update_investigation_from_evidence(
    *,
    session_id: str,
    evidence: dict[str, Any],
    investigation_kind: str,
    operator_intent: str = "diagnose_failure",
) -> InvestigationState:
    row = dict(evidence.get("target") or {})
    target = target_label_from_row(row)
    state = load_investigation_state(session_id=session_id, target=target) or InvestigationState(
        target=target,
        session_id=session_id,
        provider=str(evidence.get("provider") or "railway"),
        service=str(row.get("service") or ""),
        project=str(row.get("project") or ""),
        environment=str(row.get("environment") or ""),
    )

    root = dict(evidence.get("root_cause") or {})
    correlation = dict(evidence.get("evidence_correlation") or {})
    tags = evidence_tags_from_payload(evidence)
    previous_evidence = list(state.evidence)

    state.operator_intent = operator_intent
    state.confidence_score = score_from_evidence(root=root, correlation=correlation, evidence_tags=tags)
    state.confidence_label = confidence_label(state.confidence_score)
    state.conclusion = str(correlation.get("conclusion") or root.get("summary") or state.conclusion)
    state.next_best_action = str(correlation.get("best_next_step") or state.next_best_action)
    state.next_best_action_key = _action_key(state.next_best_action)
    if not state.next_best_action:
        action, key = plan_next_action_from_state(state)
        state.next_best_action = action
        state.next_best_action_key = key

    merge_evidence_memory(state, evidence)
    evolve_hypotheses(
        state,
        root_category=str(root.get("category") or "unknown_runtime_failure"),
        confidence_score=state.confidence_score,
        new_evidence=sorted(set(tags) - set(previous_evidence)),
    )
    mark_completed_check(state, investigation_kind)
    state.timeline.append(
        {
            "at": datetime.now(tz=UTC).isoformat(),
            "kind": investigation_kind,
            "confidence": state.confidence_score,
            "evidence_added": sorted(set(state.evidence) - set(previous_evidence)),
        }
    )
    state.updated_at = datetime.now(tz=UTC).isoformat()
    state.active_investigation = True
    state.meta["previous_evidence"] = previous_evidence
    save_investigation_state(state)
    return state


def get_investigation_for_text(*, text: str, session_id: str) -> InvestigationState | None:
    from aethos_core.failed_service_investigation.global_preemption import detect_failed_service_reference

    ref = detect_failed_service_reference(text, session_id=session_id)
    if ref and ref.rows:
        target = target_label_from_row(ref.rows[0])
        return load_investigation_state(session_id=session_id, target=target)
    from aethos_core.world_model.world_state_store import get_active_investigation

    return get_active_investigation(session_id=session_id)


def try_world_model_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.world_model.world_model_followup_router import route_world_model_followup

    return route_world_model_followup(text, session_id=session_id)


def prepend_story_if_active(
    body: str,
    *,
    session_id: str,
    target: dict[str, Any],
    action: str,
) -> str:
    from aethos_core.world_model.investigation_state import target_label_from_row
    from aethos_core.world_model.world_state_store import load_investigation_state

    state = load_investigation_state(session_id=session_id, target=target_label_from_row(target))
    if state is None or not state.active_investigation:
        return body
    if len(state.timeline) <= 1:
        return body
    from aethos_core.world_model.operational_story import compose_continuation_intro

    intro = compose_continuation_intro(state, action=action)
    if body.startswith(intro):
        return body
    if intro.rstrip(".") in body[:240]:
        return body
    return f"{intro}\n\n{body}"


def _action_key(action: str) -> str:
    low = (action or "").lower()
    if "refresh" in low and "event" in low:
        return "refresh_events_and_fetch_failure_window_logs"
    if "logs" in low:
        return "fetch_failure_window_logs"
    if "env" in low:
        return "prepare_env_fix_plan"
    if "metrics" in low:
        return "check_resource_metrics"
    return "investigate"
