# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G4 / FIX 357 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_contract import (
    AUTHORITY_EXPANSION_FIX_357,
    BUSINESS_AUTOMATION_FIX_357,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_357,
    GOVERNANCE_MUTATION_FIX_357,
    LAUNCH_AUTHORITY_FIX_357,
    LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357,
    MUTATION_PERFORMED_FIX_357,
    ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_357,
    TRUST_PROMOTION_FIX_357,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_intent import (
    handle_platform_maturity_intent,
    parse_platform_maturity_intent,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_renderer import (
    render_enterprise_platform_maturity_readiness_audit_program,
)
from aethos_core.workstreams.enterprise_platform_maturity_readiness_audit_program.enterprise_platform_maturity_readiness_audit_program_service import (
    build_enterprise_platform_maturity_readiness_audit_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": ENTERPRISE_PLATFORM_MATURITY_READINESS_AUDIT_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.enterprise_platform_maturity_readiness_audit_program."
            "enterprise_platform_maturity_readiness_audit_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_357 is False else "true",
        "launch_authority": "false" if LAUNCH_AUTHORITY_FIX_357 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_357 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_357 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_357 is False else "true",
        "business_automation": "false" if BUSINESS_AUTOMATION_FIX_357 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_357 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_357 is False else "true",
        "local_platform_maturity_executable": "true" if LOCAL_PLATFORM_MATURITY_EXECUTABLE_FIX_357 is True else "false",
        "mutation_scope": "enterprise_platform_maturity_readiness_audit_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "platform_maturity_audit_not_launch_authority",
        **extra,
    }


def route_enterprise_platform_maturity_readiness_audit_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_platform_maturity_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_platform_maturity_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Platform maturity note recorded ({record.get('kind', 'note')}). "
            "Audit evaluates readiness — no launch authority or trust promotion."
        )
        return (
            body,
            "workstream_enterprise_platform_maturity_readiness_audit_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "enterprise_platform_maturity_dashboard")
    result = build_enterprise_platform_maturity_readiness_audit_program(session_id=sid)
    markdown = render_enterprise_platform_maturity_readiness_audit_program(
        result.enterprise_platform_maturity_readiness_audit_program,
        focus=focus,
    )
    metrics = result.enterprise_platform_maturity_readiness_audit_program.get("metrics") or {}
    headline = (
        f"Maturity **{metrics.get('overall_platform_maturity_score')}** · "
        f"Level **{metrics.get('platform_maturity_level')}** · "
        f"Architecture **{metrics.get('architecture_maturity_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_enterprise_platform_maturity_readiness_audit_program",
        _meta(sid, stage="view", focus=focus),
    )
