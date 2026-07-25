# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — chat router for autonomous business operating system."""

from __future__ import annotations

from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
    AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
    AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID,
    BILLING_AUTHORITY_FIX_290,
    BUSINESS_AUTHORITY_FIX_290,
    CUSTOMER_MUTATION_AUTHORITY_FIX_290,
    GATE_BYPASS_ENABLED_FIX_290,
    MERGE_AUTHORITY_FIX_290,
    MUTATION_PERFORMED_FIX_290,
    PROVIDER_MUTATION_AUTHORITY_FIX_290,
    REPOSITORY_MUTATION_AUTHORITY_FIX_290,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_intent import (
    handle_autonomous_business_operating_system_intent,
    parse_autonomous_business_operating_system_intent,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_renderer import (
    render_autonomous_business_operating_system,
)
from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_service import (
    build_autonomous_business_operating_system,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_ROUTE_ID,
        "matched_module": (
            "mission_control.autonomous_business_operating_system."
            "autonomous_business_operating_system_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_290 is False else "true",
        "business_authority": "false" if BUSINESS_AUTHORITY_FIX_290 is False else "true",
        "automatic_business_execution_enabled": "false"
        if AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290 is False
        else "true",
        "customer_mutation_authority": "false"
        if CUSTOMER_MUTATION_AUTHORITY_FIX_290 is False
        else "true",
        "billing_authority": "false" if BILLING_AUTHORITY_FIX_290 is False else "true",
        "repository_mutation_authority": "false"
        if REPOSITORY_MUTATION_AUTHORITY_FIX_290 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_290 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_290 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_290 is False else "true",
        "mutation_scope": "autonomous_business_operating_system",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "business_operating_not_authority",
        **extra,
    }


def route_autonomous_business_operating_system(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_business_operating_system_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_business_operating_system_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded business operating note ({record.get('kind', 'note')}). "
            "Business operating system understands the business — humans run the business."
        )
        return (
            body,
            "mission_control_autonomous_business_operating_system_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_autonomous_business_operating_system(session_id=sid)
    markdown = render_autonomous_business_operating_system(result.autonomous_business_operating_system)
    dashboard = (
        (result.autonomous_business_operating_system.get("sections") or {})
        .get("business_operating_dashboard", [{}])[0]
    )
    headline = (
        f"Business health **{dashboard.get('overall_health', '—')}**, risk **{dashboard.get('overall_risk', '—')}**. "
        f"Goals **{dashboard.get('goal_count', 0)}**, opportunities **{dashboard.get('open_opportunity_count', 0)}**. "
        "Business operating system ≠ business authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_autonomous_business_operating_system",
        _meta(sid, stage="view"),
    )
