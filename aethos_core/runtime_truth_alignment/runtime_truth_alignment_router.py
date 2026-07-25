# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — runtime truth alignment router."""

from __future__ import annotations

from aethos_core.conversation.continuity_pkg.conversation_continuity_router import (
    apply_conversation_continuity,
    compose_continuity_routed_body,
    resolve_continuity_classification,
    route_conversation_continuity_commands,
)
from aethos_core.identity_truth_lock.identity_truth_lock_responses import (
    compose_model_creator_attribution_response,
    compose_ownership_attribution_response,
    compose_provider_attribution_response,
)
from aethos_core.identity_truth_lock.identity_truth_lock_router import route_identity_truth_lock
from aethos_core.identity_truth_lock.runtime_identity_lock import runtime_identity_lock_meta
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_composer import (
    compose_capability_response,
    compose_creator_attribution_response,
    compose_human_support_response,
    compose_platform_identity_response,
)
from aethos_core.runtime_truth_alignment.runtime_truth_alignment_contract import (
    RUNTIME_TRUTH_ALIGNMENT_ROUTE_ID,
)
from aethos_core.truth_consistency.truth_consistency_responses import (
    compose_launch_readiness_response,
    compose_provider_support_response,
)
from aethos_core.truth_consistency.truth_consistency_router import (
    attach_truth_validation_meta,
    route_truth_consistency,
)

_TRUTH_VALIDATED_INTENTS = frozenset({
    "platform_identity_response",
    "creator_attribution_response",
    "ownership_attribution_response",
    "provider_attribution_response",
    "provider_support_response",
    "launch_readiness_response",
    "capability_response",
    "model_creator_attribution_response",
    "human_support_follow_up_response",
})


def _meta(*, session_id: str, classification: str, suppress_footer: bool = True) -> dict[str, str]:
    base = {
        "route_id": RUNTIME_TRUTH_ALIGNMENT_ROUTE_ID,
        "matched_module": "runtime_truth_alignment.runtime_truth_alignment_router",
        "session_id": session_id,
        "runtime_classification": classification,
        "suppress_governance_footer": "true" if suppress_footer else "false",
        "show_governance_footer": "false" if suppress_footer else "true",
        "presentation_mode": "casual",
        "lane": "runtime_truth_alignment",
    }
    if classification in {
        "platform_identity_response",
        "creator_attribution_response",
        "ownership_attribution_response",
        "provider_attribution_response",
        "model_creator_attribution_response",
        "human_support_follow_up_response",
    } or classification.startswith("model_creator_attribution_response:"):
        base.update(runtime_identity_lock_meta(classification=classification))
    return base


def _finalize_route(
    *,
    text: str,
    session_id: str,
    body: str,
    intent: str,
    classification: str,
) -> tuple[str, str, dict[str, str]]:
    body, meta = apply_conversation_continuity(
        text=text,
        session_id=session_id,
        body=body,
        classification=classification,
        intent=intent,
        meta=_meta(session_id=session_id, classification=classification),
    )
    if intent in _TRUTH_VALIDATED_INTENTS or intent.startswith("model_creator"):
        meta = attach_truth_validation_meta(
            question=text,
            answer=body,
            session_id=session_id,
            response_kind=intent,
            meta=meta,
        )
    return body, intent, meta


def route_runtime_truth_alignment(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    continuity_cmd = route_conversation_continuity_commands(text, session_id=session_id)
    if continuity_cmd is not None:
        return continuity_cmd

    truth_route = route_truth_consistency(text, session_id=session_id)
    if truth_route is not None:
        return truth_route

    dashboard_route = route_identity_truth_lock(text, session_id=session_id)
    if dashboard_route is not None:
        return dashboard_route

    classification = resolve_continuity_classification(text=text, session_id=session_id)
    if classification is None or classification == "operational_action":
        return None

    sid = (session_id or "default").strip()[:64] or "default"

    continuity_body = compose_continuity_routed_body(
        text=text,
        session_id=sid,
        classification=classification,
    )
    if continuity_body is not None:
        body, intent = continuity_body
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent=intent,
            classification=classification,
        )

    if classification == "ownership_attribution_response":
        body = compose_ownership_attribution_response()
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="ownership_attribution_response",
            classification=classification,
        )

    if classification == "creator_attribution_response":
        body = compose_creator_attribution_response()
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="creator_attribution_response",
            classification=classification,
        )

    if classification == "provider_attribution_response":
        body = compose_provider_attribution_response()
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="provider_attribution_response",
            classification=classification,
        )

    if classification == "provider_support_response":
        body = compose_provider_support_response(session_id=sid)
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="provider_support_response",
            classification=classification,
        )

    if classification == "launch_readiness_response":
        body = compose_launch_readiness_response(session_id=sid)
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="launch_readiness_response",
            classification=classification,
        )

    if classification.startswith("model_creator_attribution_response:"):
        model_name = classification.split(":", 1)[1]
        body = compose_model_creator_attribution_response(model_name=model_name)
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="model_creator_attribution_response",
            classification=classification,
        )

    if classification == "platform_identity_response":
        body = compose_platform_identity_response(session_id=sid)
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="platform_identity_response",
            classification=classification,
        )

    if classification == "capability_response":
        body = compose_capability_response(session_id=sid)
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="capability_response",
            classification=classification,
        )

    if classification == "human_support_response":
        body = compose_human_support_response()
        return _finalize_route(
            text=text,
            session_id=sid,
            body=body,
            intent="human_support_response",
            classification=classification,
        )

    if classification == "general_assistant_response":
        return None

    return None
