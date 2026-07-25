# SPDX-License-Identifier: Apache-2.0
"""Investigation strategy routing — owns strategic next-step questions."""

from __future__ import annotations

import re

from aethos_core.chat.service import ChatTurnResult
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome
from aethos_core.repair_memory.repair_outcome_router import find_latest_repair_outcome_for_context
from aethos_core.world_model.investigation_state import InvestigationState, target_label_from_row

_STRATEGY_RX = re.compile(
    r"\b("
    r"what\s+(?:should\s+we|we\s+should)\s+do\s+next"
    r"|what\s+next"
    r"|what(?:'s| is)\s+(?:the\s+)?next\s+step"
    r"|^next\s+step\b"
    r"|what\s+do\s+you\s+recommend(?:\s+now)?"
    r"|how\s+should\s+we\s+continue"
    r"|how\s+should\s+we\s+debug\s+this"
    r"|where\s+should\s+we\s+investigate"
    r"|what\s+is\s+the\s+best\s+next\s+action"
    r"|next\s+best\s+action"
    r"|how\s+do\s+we\s+move\s+forward"
    r")\b",
    re.I,
)

_STRATEGY_STEPS = (
    "Fetch full logs around the latest failed deployment window",
    "Inspect Railway service events and exit reasons",
    "Check storage/volume state and disk availability",
)


def is_investigation_strategy_question(text: str) -> bool:
    return bool(_STRATEGY_RX.search(text or ""))


def investigation_strategy_preemption_blocks_route(text: str, *, session_id: str = "default") -> bool:
    """Strategic follow-ups must not fall through to generic assistant/help routing."""
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        workflow_discovery_preemption_blocks_route,
    )

    if workflow_discovery_preemption_blocks_route(text, session_id=session_id):
        return False
    return is_investigation_strategy_question(text)


def has_investigation_continuity(*, text: str, session_id: str = "default") -> bool:
    if _resolve_investigation_state(text=text, session_id=session_id) is not None:
        return True
    if find_latest_repair_outcome_for_context(text, session_id=session_id) is not None:
        return True
    try:
        from aethos_core.post_mutation_verification.verification_context_discovery import discover_verification_lifecycle

        if discover_verification_lifecycle("", session_id=session_id) is not None:
            return True
    except Exception:
        pass
    try:
        from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context

        if resolve_fallback_context(text=text, session_id=session_id) is not None:
            return True
    except Exception:
        pass
    try:
        from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

        thread = get_active_operational_thread(session_id)
        if thread is not None and thread.status not in {"completed", "cancelled", "superseded"}:
            return True
    except Exception:
        pass
    return False


def compose_investigation_strategy_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, dict[str, str]]:
    if not has_investigation_continuity(text=text, session_id=session_id):
        return (
            (
                "I can recommend the next investigation step once I know which service failure we are pursuing.\n\n"
                "Tell me which service is failing, or ask me to **verify health** after the latest mutation."
            ),
            {},
        )

    outcome = find_latest_repair_outcome_for_context(text, session_id=session_id)
    state = _resolve_investigation_state(text=text, session_id=session_id)
    guided_meta: dict[str, str] = {}

    if outcome is not None and not outcome.helped:
        reply = _compose_regressed_strategy_reply(outcome, state=state)
        service = outcome.service or outcome.target.split("/")[-1].strip() or "the service"
        opener = [
            f"The **{service}** restart did not resolve the failure, so I would avoid another restart right now."
        ]
        enriched, guided_meta = _try_guided_evidence(
            reply, session_id=session_id, state=state, outcome=outcome, opener_lines=opener
        )
        return enriched, guided_meta

    if state is not None:
        from aethos_core.repair_memory.recommendation_guard import compose_next_step_with_repair_guard
        from aethos_core.world_model.investigation_planner import plan_next_action_from_state
        from aethos_core.world_model.operational_story import compose_next_step_answer

        base = compose_next_step_answer(state)
        guarded = compose_next_step_with_repair_guard(state, base)
        if guarded != base:
            reply = guarded
        else:
            action, _key = state.next_best_action, state.next_best_action_key
            if not action:
                action, _key = plan_next_action_from_state(state)
            service = state.service or state.target.split("/")[-1].strip() or "the service"
            lines = [
                f"Best next action for **{service}**:",
                action,
            ]
            reasons: list[str] = []
            if "fresh_wiredtiger_logs" in state.evidence or "fresh_runtime_logs" in state.evidence:
                reasons.append("current logs are fresh but low-signal")
            if "stale_service_events" in state.evidence:
                reasons.append("service events are stale")
            if "high_signal_logs" not in state.evidence:
                reasons.append("no fatal error or exit reason has been confirmed yet")
            if reasons:
                lines.extend(["", "Reason:", f"{' and '.join(reasons).capitalize()}."])
            reply = "\n".join(lines)
        enriched, guided_meta = _try_guided_evidence(reply, session_id=session_id, state=state, outcome=outcome)
        return enriched, guided_meta

    if outcome is not None and outcome.helped:
        service = outcome.service or outcome.target.split("/")[-1].strip() or "the service"
        return (
            (
                f"The latest **{outcome.operation.replace('_', ' ')}** on **{service}** appears to have helped.\n\n"
                "Best next action:\n"
                "Continue monitoring recovery and confirm with fresh logs and service events."
            ),
            {},
        )

    service = _service_label_from_outcome_or_default(outcome)
    reply = _compose_default_strategy_reply(service)
    enriched, guided_meta = _try_guided_evidence(reply, session_id=session_id, state=state, outcome=outcome)
    return enriched, guided_meta


def compose_investigation_strategy_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        workflow_discovery_preemption_blocks_route,
    )

    if workflow_discovery_preemption_blocks_route(text, session_id=session_id):
        return None
    if not is_investigation_strategy_question(text):
        return None
    reply, guided_meta = compose_investigation_strategy_reply(text, session_id=session_id)
    meta: dict[str, str] = {
        "route_id": "investigation_strategy",
        "matched_module": "world_model.investigation_strategy_router",
        "investigation_strategy": "true",
        "investigation_continuity": "true" if has_investigation_continuity(text=text, session_id=session_id) else "false",
    }
    outcome = find_latest_repair_outcome_for_context(text, session_id=session_id)
    if outcome is not None:
        meta["repair_result"] = outcome.result
        meta["repair_helped"] = "true" if outcome.helped else "false"
        if outcome.service:
            meta["service"] = outcome.service
        if outcome.target:
            meta["matched_target"] = outcome.target
    state = _resolve_investigation_state(text=text, session_id=session_id)
    if state is not None and state.service:
        meta.setdefault("service", state.service)
    meta.update(guided_meta)
    if meta.get("guided_evidence_executed") != "true" and has_investigation_continuity(text=text, session_id=session_id):
        meta.update(_guided_evidence_skip_meta(state=state, outcome=outcome))
    intent = (
        "investigation_strategy_regressed"
        if outcome is not None and not outcome.helped
        else "investigation_strategy_next_step"
    )
    if meta.get("investigation_continuity") == "false":
        intent = "investigation_strategy_clarification"
    return reply, intent, meta


def route_investigation_strategy_question(
    text: str,
    *,
    session_id: str = "default",
) -> ChatTurnResult | None:
    routed = compose_investigation_strategy_route_reply(text, session_id=session_id)
    if routed is None:
        return None
    reply, intent, meta = routed
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )


def _compose_regressed_strategy_reply(
    outcome: RepairAttemptOutcome,
    *,
    state: InvestigationState | None,
) -> str:
    service = outcome.service or outcome.target.split("/")[-1].strip() or "the service"
    lines = [
        f"The **{service}** restart did not resolve the failure, so I would avoid another restart right now.",
        "",
        "Best next action:",
    ]
    for idx, step in enumerate(_strategy_steps_for_service(service), start=1):
        lines.append(f"{idx}. {step}")
    reason_parts = ["Current evidence is still low-signal"]
    if outcome.result in {"regressed", "failed_after_mutation"}:
        reason_parts.append(f"the restart **{outcome.result.replace('_', ' ')}** without improving health")
    elif state and "stale_service_events" in state.evidence:
        reason_parts.append("service events are stale")
    lines.extend(["", "Reason:", f"{' and '.join(reason_parts).capitalize()}."])
    lines.extend(
        [
            "",
            "I would not recommend another restart or redeploy until deeper failure evidence is collected.",
        ]
    )
    return "\n".join(lines)


def _compose_default_strategy_reply(service: str) -> str:
    lines = [
        f"Best next action for **{service}**:",
    ]
    for idx, step in enumerate(_strategy_steps_for_service(service), start=1):
        lines.append(f"{idx}. {step}")
    lines.extend(
        [
            "",
            "Reason:",
            "The active investigation still needs higher-signal failure evidence before another mutation.",
        ]
    )
    return "\n".join(lines)


def _strategy_steps_for_service(service: str) -> list[str]:
    service_label = service or "the service"
    steps = list(_STRATEGY_STEPS)
    steps.append(f"Look for fatal **{service_label}** startup errors beyond low-signal runtime activity")
    return steps


def _service_label_from_outcome_or_default(outcome: RepairAttemptOutcome | None) -> str:
    if outcome is not None:
        return outcome.service or outcome.target.split("/")[-1].strip() or "the service"
    return "the service"


def _try_guided_evidence(
    reply: str,
    *,
    session_id: str,
    state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
    opener_lines: list[str] | None = None,
) -> tuple[str, dict[str, str]]:
    from aethos_core.world_model.guided_evidence_orchestrator import try_enrich_strategy_with_guided_evidence

    return try_enrich_strategy_with_guided_evidence(
        reply,
        session_id=session_id,
        state=state,
        outcome=outcome,
        opener_lines=opener_lines,
    )


def _guided_evidence_skip_meta(
    *,
    state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
) -> dict[str, str]:
    from aethos_core.world_model.guided_evidence_orchestrator import (
        can_execute_readonly_guided_evidence,
        should_execute_guided_evidence,
    )

    if not should_execute_guided_evidence(state=state, outcome=outcome):
        return {"guided_evidence_executed": "false", "guided_evidence_eligible": "false"}
    can_run, _err = can_execute_readonly_guided_evidence()
    if not can_run:
        return {"guided_evidence_executed": "false", "guided_evidence_eligible": "true", "guided_evidence_skipped": "credentials"}
    return {"guided_evidence_eligible": "true", "guided_evidence_executed": "false"}


def _resolve_investigation_state(*, text: str, session_id: str) -> InvestigationState | None:
    try:
        from aethos_core.world_model.investigation_engine import get_investigation_for_text
        from aethos_core.world_model.world_state_store import get_active_investigation, load_investigation_state

        state = get_investigation_for_text(text=text, session_id=session_id)
        if state is not None:
            return state
        active = get_active_investigation(session_id=session_id)
        if active is not None:
            return active
    except Exception:
        pass

    try:
        from aethos_core.world_model.fallback_context_resolver import (
            investigation_state_from_fallback,
            resolve_fallback_context,
        )

        ctx = resolve_fallback_context(text=text, session_id=session_id)
        if ctx is not None:
            return investigation_state_from_fallback(ctx, session_id=session_id)
    except Exception:
        pass

    outcome = find_latest_repair_outcome_for_context(text, session_id=session_id)
    if outcome is not None and outcome.target:
        try:
            from aethos_core.world_model.world_state_store import load_investigation_state

            state = load_investigation_state(session_id=session_id, target=outcome.target)
            if state is not None:
                return state
        except Exception:
            pass
        row = {
            "service": outcome.service,
            "project": outcome.project,
            "environment": outcome.environment,
            "status": "failed",
        }
        return InvestigationState(
            target=outcome.target or target_label_from_row(row),
            session_id=session_id,
            provider=outcome.provider or "railway",
            service=outcome.service or "",
            project=outcome.project or "",
            environment=outcome.environment or "",
            active_investigation=True,
            evidence=["failed_restart_attempt", "restart_did_not_resolve"] if not outcome.helped else [],
        )
    return None
