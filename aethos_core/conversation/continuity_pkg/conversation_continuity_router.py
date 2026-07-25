# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — conversation continuity runtime router."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_contract import CONVERSATION_CONTINUITY_ROUTE_ID
from aethos_core.conversation.continuity_pkg.conversation_continuity_evaluator import (
    build_conversation_recovery_report,
    detect_topic_drift,
    sanitize_memory_truth,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_follow_up import (
    resolve_follow_up_intent,
    should_persist_human_support_mode,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_intent import (
    handle_conversation_continuity_intent,
    parse_conversation_continuity_intent,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_renderer import render_conversation_continuity_markdown
from aethos_core.conversation.continuity_pkg.conversation_continuity_responses import (
    compose_conversation_recovery_prefix,
    compose_human_support_follow_up_response,
    compose_topic_continuity_intro,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_service import build_conversation_continuity
from aethos_core.conversation.continuity_pkg.conversation_continuity_store import update_session_state
from aethos_core.conversation.continuity_pkg.conversation_continuity_topic_classifier import detect_topic_from_text
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_classifier import classify_runtime_prompt


def _meta(*, session_id: str, intent: str) -> dict[str, str]:
    return {
        "route_id": CONVERSATION_CONTINUITY_ROUTE_ID,
        "matched_module": "conversation_continuity.conversation_continuity_router",
        "session_id": session_id,
        "intent": intent,
        "suppress_governance_footer": "true",
        "show_governance_footer": "false",
        "presentation_mode": "casual",
        "lane": "conversation_continuity",
        "conversation_continuity_layer": "true",
    }


def route_conversation_continuity_commands(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    parsed = parse_conversation_continuity_intent(text)
    if parsed is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"

    if parsed.get("action") == "record":
        handle_conversation_continuity_intent(parsed, session_id=sid)
        return (
            "Continuity review recorded. This command is record-only and does not mutate session topics.",
            "continuity_review_record",
            _meta(session_id=sid, intent="continuity_review_record"),
        )

    if parsed.get("action") == "view":
        payload = build_conversation_continuity(session_id=sid).conversation_continuity
        body = render_conversation_continuity_markdown(payload=payload, focus="continuity_dashboard")
        return body, "continuity_dashboard", _meta(session_id=sid, intent="continuity_dashboard")

    return None


def resolve_continuity_classification(*, text: str, session_id: str) -> str | None:
    follow_up = resolve_follow_up_intent(text=text, session_id=session_id)
    if follow_up.get("resolved") and follow_up.get("classification"):
        if follow_up.get("continue_operational_lane"):
            return "operational_action"
        return str(follow_up["classification"])

    if should_persist_human_support_mode(text=text, session_id=session_id):
        return "human_support_response"

    return classify_runtime_prompt(text)


def record_conversation_turn(
    *,
    text: str,
    session_id: str,
    classification: str | None,
    intent: str,
) -> dict[str, Any]:
    topic_info = detect_topic_from_text(text, classification=classification)
    state = update_session_state(
        session_id=session_id,
        active_topic=str(topic_info.get("topic")) if topic_info.get("topic") else None,
        parent_topic=str(topic_info.get("parent_topic")) if topic_info.get("parent_topic") else None,
        confidence=float(topic_info.get("confidence") or 0.5),
        active_mode=str(topic_info.get("mode") or "general"),
        last_classification=classification,
        last_intent=intent,
        increment_turn=True,
    )
    return state


def apply_conversation_continuity(
    *,
    text: str,
    session_id: str,
    body: str,
    classification: str | None,
    intent: str,
    meta: dict[str, str],
) -> tuple[str, dict[str, str]]:
    drift = detect_topic_drift(
        session_id=session_id,
        classification=classification,
        response_kind=intent,
    )
    recovery = build_conversation_recovery_report(session_id=session_id, drift_report=drift)
    updated_body = body
    if recovery.get("recovery_required"):
        updated_body = compose_conversation_recovery_prefix(session_id=session_id, drift_report=drift) + updated_body

    if intent.endswith("_follow_up_response") or intent in {
        "creator_attribution_response",
        "platform_identity_response",
        "ownership_attribution_response",
    }:
        updated_body = compose_topic_continuity_intro(session_id=session_id, body=updated_body)

    updated_body, memory_report = sanitize_memory_truth(answer_text=updated_body, session_id=session_id)

    state = record_conversation_turn(
        text=text,
        session_id=session_id,
        classification=classification,
        intent=intent,
    )

    enriched = dict(meta)
    enriched["conversation_continuity_layer"] = "true"
    enriched["active_topic"] = str(state.get("active_topic") or "")
    enriched["active_mode"] = str(state.get("active_mode") or "general")
    enriched["topic_drift_detected"] = "true" if drift.get("drift_detected") else "false"
    enriched["memory_truth_valid"] = "true" if memory_report.get("valid") else "false"
    return updated_body, enriched


def compose_continuity_routed_body(
    *,
    text: str,
    session_id: str,
    classification: str,
) -> tuple[str, str] | None:
    if classification == "human_support_follow_up_response":
        return (
            compose_human_support_follow_up_response(session_id=session_id),
            "human_support_follow_up_response",
        )

    follow_up = resolve_follow_up_intent(text=text, session_id=session_id)
    if follow_up.get("resolved") and follow_up.get("resolution_kind") == "human_support_follow_up":
        return (
            compose_human_support_follow_up_response(
                session_id=session_id,
                topic=str(follow_up.get("active_topic") or "human_support"),
            ),
            "human_support_follow_up_response",
        )

    return None
