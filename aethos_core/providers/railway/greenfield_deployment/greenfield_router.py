# SPDX-License-Identifier: Apache-2.0
"""Chat router for Railway greenfield deployment from local workspace."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import run_railway_greenfield_deployment_flow
from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
    greenfield_intent_debug_metadata,
    is_railway_greenfield_deployment_intent,
)
from aethos_core.security.secret_redaction import redact_text

if TYPE_CHECKING:
    from aethos_core.chat.service import ChatTurnResult

_log = logging.getLogger(__name__)


def _build_meta(
    *,
    session_id: str,
    result,
    text: str,
    debug_enabled: bool,
    route_source: str = "greenfield_router",
) -> dict[str, str]:
    meta: dict[str, str] = {
        "route_id": "railway_greenfield_deployment_flow",
        "intent": "railway_greenfield_deployment_flow",
        "route_precedence": "greenfield_before_operational_recall",
        "matched_module": "providers.railway.greenfield_deployment.greenfield_router",
        "route_source": route_source,
        "session_id": session_id,
        "flow": "railway_greenfield_deployment",
        "readonly": "true" if result.blocked else "false",
        "mutation_performed": "true" if result.intent == "railway_greenfield_solo_execution_completed" else "false",
        "execution_started": "true" if "solo_execution" in result.intent else "false",
        "solo_execution_mode": "true" if "solo_execution" in result.intent else "false",
        "preflight_created": "true" if result.preflight_job_id else "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
    }
    meta.update(greenfield_intent_debug_metadata(text, debug_enabled=debug_enabled))
    if result.blocker_code:
        meta["blocker_code"] = result.blocker_code
    if result.preflight_job_id:
        meta["job_id"] = result.preflight_job_id
    if result.safe_next_command:
        meta["safe_next_command"] = result.safe_next_command
    return meta


def route_railway_greenfield_deployment_flow(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Route greenfield deployment — never raises."""
    return safe_route_railway_greenfield_deployment_flow(text, session_id=session_id)


def safe_route_railway_greenfield_deployment_flow(
    text: str,
    *,
    session_id: str = "default",
    route_source: str = "greenfield_router",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.deployment_targets.resolver import (
        is_railway_greenfield_deploy_continuation,
        merge_greenfield_deploy_continuation_text,
    )

    routed_text = text
    continuation = False
    if not is_railway_greenfield_deployment_intent(text):
        if is_railway_greenfield_deploy_continuation(text, session_id=session_id):
            routed_text = merge_greenfield_deploy_continuation_text(text, session_id=session_id)
            continuation = True
        else:
            return None
    elif is_railway_greenfield_deploy_continuation(text, session_id=session_id):
        routed_text = merge_greenfield_deploy_continuation_text(text, session_id=session_id)
        continuation = True

    from aethos_core.chat.route_trace import is_internal_diagnostics_query

    debug_enabled = is_internal_diagnostics_query(routed_text)
    try:
        result = run_railway_greenfield_deployment_flow(routed_text, session_id=session_id)
    except Exception as exc:
        _log.exception("Railway greenfield deployment flow failed safely")
        detail = redact_text(str(exc))
        reply = "\n".join(
            [
                "**Railway greenfield deployment blocked**",
                "",
                "- Blocker: `RAILWAY_GREENFIELD_FLOW_ERROR`",
                f"- Detail: {detail}",
                "",
                "**Required action:** verify Local Workspaces registration and git remote, then retry.",
                "",
                "**Safe next command:** `Open Mission Control → Code workspaces and register the AethOS repo path.`",
                "",
                "No Railway project or service has been created. No mutation has been performed.",
            ]
        )
        meta = {
            "route_id": "railway_greenfield_deployment_flow",
            "intent": "railway_greenfield_deployment_flow",
            "route_precedence": "greenfield_before_operational_recall",
            "matched_module": "providers.railway.greenfield_deployment.greenfield_router",
            "route_source": route_source,
            "session_id": session_id,
            "flow": "railway_greenfield_deployment",
            "mutation_performed": "false",
            "preflight_created": "false",
            "blocker_code": "RAILWAY_GREENFIELD_FLOW_ERROR",
            "presentation_bypass": "true",
            "presentation_mode": "engineering",
            "suppress_governance_footer": "true",
        }
        meta.update(greenfield_intent_debug_metadata(text, debug_enabled=debug_enabled))
        return reply, "railway_greenfield_deployment_blocked", meta

    meta = _build_meta(
        session_id=session_id,
        result=result,
        text=routed_text,
        debug_enabled=debug_enabled,
        route_source=route_source,
    )
    if continuation:
        meta["deploy_continuation"] = "true"
    return result.reply, result.intent, meta


def preemption_chat_turn_result(
    text: str,
    *,
    session_id: str = "default",
    route_source: str = "greenfield_preemption",
) -> ChatTurnResult | None:
    """Return a chat turn for greenfield intent — used before operational recall and crash fallback."""
    from aethos_core.chat.service import ChatTurnResult

    routed = safe_route_railway_greenfield_deployment_flow(
        text,
        session_id=session_id,
        route_source=route_source,
    )
    if routed is None:
        return None
    body, intent, meta = routed
    return ChatTurnResult(
        reply=body,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=meta,
    )
