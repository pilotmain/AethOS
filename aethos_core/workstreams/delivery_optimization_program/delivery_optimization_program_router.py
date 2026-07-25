# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C2 / FIX 340 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    AUTONOMOUS_MUTATION_ENABLED_FIX_340,
    AUTHORITY_EXPANSION_FIX_340,
    DELIVERY_AUTHORITY_FIX_340,
    DELIVERY_OPTIMIZATION_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_340,
    LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340,
    MUTATION_PERFORMED_FIX_340,
    TRUST_MUTATION_AUTHORITY_FIX_340,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_intent import (
    handle_delivery_optimization_intent,
    parse_delivery_optimization_intent,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_renderer import (
    render_delivery_optimization_program,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_service import (
    build_delivery_optimization_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": DELIVERY_OPTIMIZATION_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.delivery_optimization_program.delivery_optimization_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_340 is False else "true",
        "autonomous_mutation_enabled": "false" if AUTONOMOUS_MUTATION_ENABLED_FIX_340 is False else "true",
        "delivery_authority": "false" if DELIVERY_AUTHORITY_FIX_340 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_340 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_340 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_340 is False else "true",
        "local_optimization_analysis_executable": "true"
        if LOCAL_OPTIMIZATION_ANALYSIS_EXECUTABLE_FIX_340 is True
        else "false",
        "mutation_scope": "delivery_optimization_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "delivery_optimization_not_autonomous_mutation",
        **extra,
    }


def route_delivery_optimization_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_delivery_optimization_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_delivery_optimization_intent(intent, session_id=sid)

    if handled.get("action") == "analyze":
        analysis = handled.get("analysis") or {}
        opps = analysis.get("improvement_opportunities") or {}
        body = (
            f"Delivery optimization analysis complete — **{opps.get('opportunity_count', 0)}** opportunities identified. "
            "Delivery optimization ≠ autonomous mutation."
        )
        return (
            body,
            "workstream_delivery_optimization_program_analyze",
            _meta(sid, stage="analyze"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded delivery optimization note ({record.get('kind', 'note')}). "
            "Recommendations require human review — no autonomous mutation."
        )
        return (
            body,
            "workstream_delivery_optimization_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "delivery_optimization_dashboard")
    result = build_delivery_optimization_program(session_id=sid)
    markdown = render_delivery_optimization_program(result.delivery_optimization_program, focus=focus)
    trends = result.delivery_optimization_program.get("trends") or {}
    headline = (
        f"Success trend **{trends.get('deployment_success_trend', 0.0)}** · "
        f"Intervention reduction **{trends.get('intervention_reduction_trend', 0.0)}**. "
        "Optimization recommends — humans decide adoption."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_delivery_optimization_program",
        _meta(sid, stage="view", focus=focus),
    )
