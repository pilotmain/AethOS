# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — chat router for autonomous application lifecycle management."""

from __future__ import annotations

from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
    AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID,
    DEPLOYMENT_AUTHORITY_FIX_280,
    GATE_BYPASS_ENABLED_FIX_280,
    LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
    MERGE_AUTHORITY_FIX_280,
    MUTATION_PERFORMED_FIX_280,
    PROVIDER_MUTATION_AUTHORITY_FIX_280,
    REPOSITORY_MUTATION_AUTHORITY_FIX_280,
    ROLLBACK_AUTHORITY_FIX_280,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_intent import (
    handle_autonomous_application_lifecycle_management_intent,
    parse_autonomous_application_lifecycle_management_intent,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_renderer import (
    render_autonomous_application_lifecycle_management,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_service import (
    build_autonomous_application_lifecycle_management,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_ROUTE_ID,
        "matched_module": (
            "mission_control.autonomous_application_lifecycle_management."
            "autonomous_application_lifecycle_management_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_280 is False else "true",
        "lifecycle_management_authority": "false"
        if LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280 is False
        else "true",
        "automatic_lifecycle_execution_enabled": "false"
        if AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280 is False
        else "true",
        "repository_mutation_authority": "false"
        if REPOSITORY_MUTATION_AUTHORITY_FIX_280 is False
        else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_280 is False else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_280 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_280 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_280 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_280 is False else "true",
        "mutation_scope": "autonomous_application_lifecycle_management",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "lifecycle_management_not_execution",
        **extra,
    }


def route_autonomous_application_lifecycle_management(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_application_lifecycle_management_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_application_lifecycle_management_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded application lifecycle note ({record.get('kind', 'note')}). "
            "Lifecycle management tracks state — humans approve transitions."
        )
        return (
            body,
            "mission_control_autonomous_application_lifecycle_management_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_autonomous_application_lifecycle_management(session_id=sid)
    markdown = render_autonomous_application_lifecycle_management(
        result.autonomous_application_lifecycle_management
    )
    dashboard = (
        (result.autonomous_application_lifecycle_management.get("sections") or {})
        .get("lifecycle_management_dashboard", [{}])[0]
    )
    headline = (
        f"Application lifecycle stage **{result.autonomous_application_lifecycle_management.get('current_lifecycle_stage', 'unknown')}**. "
        f"Health **{dashboard.get('overall_health', '—')}**, risk **{dashboard.get('overall_risk', '—')}**. "
        "Lifecycle management ≠ execution authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_autonomous_application_lifecycle_management",
        _meta(sid, stage="view"),
    )
