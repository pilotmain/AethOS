# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — chat router for governance insights."""

from __future__ import annotations

from aethos_core.mission_control.governance_insights.governance_insights_contract import (
    AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143,
    GOVERNANCE_INSIGHTS_ROUTE_ID,
    GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143,
    MUTATION_PERFORMED_FIX_143,
    POLICY_AUTO_TUNING_ENABLED_FIX_143,
)
from aethos_core.mission_control.governance_insights.governance_insights_intent import is_governance_insights_intent
from aethos_core.mission_control.governance_insights.governance_insights_renderer import render_governance_insights
from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_INSIGHTS_ROUTE_ID,
        "matched_module": "mission_control.governance_insights.governance_insights_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_143 is False else "true",
        "policy_auto_tuning_enabled": "false" if POLICY_AUTO_TUNING_ENABLED_FIX_143 is False else "true",
        "governance_self_modification_enabled": "false"
        if GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143 is False
        else "true",
        "mutation_scope": "governance_insights_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "meta_governance_not_mutation",
        **extra,
    }


def route_governance_insights(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_governance_insights_intent(text):
        return None

    result = build_governance_insights(session_id=session_id)
    if not result.ok:
        body = f"Governance insights unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_insights_blocked", _meta(session_id, stage="blocked")

    body = render_governance_insights(result.insights)
    health = (result.insights.get("insights") or {}).get("governance_health_metrics") or {}
    return (
        body,
        "mission_control_governance_insights",
        _meta(
            session_id,
            stage="governance_insights",
            insight_count=str(result.insights.get("insight_count", 0)),
            health_score=str(health.get("governance_health_score", "")),
        ),
    )
