# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — chat router for SaaS launch readiness assessment."""

from __future__ import annotations

from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_309,
    AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309,
    CUSTOMER_PROVISIONING_AUTHORITY_FIX_309,
    LAUNCH_AUTHORITY_FIX_309,
    MUTATION_PERFORMED_FIX_309,
    SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_309,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_intent import (
    handle_saas_launch_readiness_assessment_intent,
    parse_saas_launch_readiness_assessment_intent,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_renderer import (
    render_saas_launch_readiness_assessment,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": SAAS_LAUNCH_READINESS_ASSESSMENT_ROUTE_ID,
        "matched_module": (
            "mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_309 is False else "true",
        "launch_authority": "false" if LAUNCH_AUTHORITY_FIX_309 is False else "true",
        "automatic_launch_enabled": "false" if AUTOMATIC_LAUNCH_ENABLED_FIX_309 is False else "true",
        "automatic_readiness_promotion_enabled": "false"
        if AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_309 is False else "true",
        "customer_provisioning_authority": "false"
        if CUSTOMER_PROVISIONING_AUTHORITY_FIX_309 is False
        else "true",
        "mutation_scope": "saas_launch_readiness_assessment",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "launch_assessment_not_launch_authority",
        **extra,
    }


def route_saas_launch_readiness_assessment(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_saas_launch_readiness_assessment_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_saas_launch_readiness_assessment_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded launch readiness note ({record.get('kind', 'note')}). "
            "Launch assessment ≠ launch authority."
        )
        return (
            body,
            "mission_control_saas_launch_readiness_assessment_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "launch_readiness_dashboard")
    result = build_saas_launch_readiness_assessment(session_id=sid)
    markdown = render_saas_launch_readiness_assessment(
        result.saas_launch_readiness_assessment,
        focus=focus,
    )
    dashboard = (
        (result.saas_launch_readiness_assessment.get("sections") or {})
        .get("launch_readiness_dashboard", [{}])[0]
    )
    headline = (
        f"Overall launch status **{result.saas_launch_readiness_assessment.get('overall_launch_status', '—')}**. "
        "Evidence-backed assessment — humans decide launch readiness, not AethOS."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_saas_launch_readiness_assessment",
        _meta(sid, stage="view", focus=focus, blocker_count=str(len(dashboard.get("blockers") or []))),
    )
