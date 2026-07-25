# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H1 / FIX 358 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_contract import (
    AUTHORITY_EXPANSION_FIX_358,
    AUTOMATIC_PRIORITIZATION_FIX_358,
    BUDGET_ALLOCATION_FIX_358,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_358,
    LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358,
    MUTATION_PERFORMED_FIX_358,
    PLAN_EXECUTION_FIX_358,
    PROJECT_CREATION_FIX_358,
    RESOURCE_COMMITMENT_FIX_358,
    ROADMAP_MUTATION_FIX_358,
    STRATEGIC_AUTHORITY_FIX_358,
    STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_358,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_intent import (
    handle_strategic_direction_intent,
    parse_strategic_direction_intent,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_renderer import (
    render_strategic_direction_next_growth_decision_program,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_service import (
    build_strategic_direction_next_growth_decision_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": STRATEGIC_DIRECTION_NEXT_GROWTH_DECISION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.strategic_direction_next_growth_decision_program."
            "strategic_direction_next_growth_decision_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_358 is False else "true",
        "strategic_authority": "false" if STRATEGIC_AUTHORITY_FIX_358 is False else "true",
        "budget_allocation": "false" if BUDGET_ALLOCATION_FIX_358 is False else "true",
        "project_creation": "false" if PROJECT_CREATION_FIX_358 is False else "true",
        "resource_commitment": "false" if RESOURCE_COMMITMENT_FIX_358 is False else "true",
        "plan_execution": "false" if PLAN_EXECUTION_FIX_358 is False else "true",
        "roadmap_mutation": "false" if ROADMAP_MUTATION_FIX_358 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_358 is False else "true",
        "automatic_prioritization": "false" if AUTOMATIC_PRIORITIZATION_FIX_358 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_358 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_358 is False else "true",
        "local_strategic_direction_executable": "true" if LOCAL_STRATEGIC_DIRECTION_EXECUTABLE_FIX_358 is True else "false",
        "mutation_scope": "strategic_direction_next_growth_decision_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "strategic_direction_not_strategic_authority",
        **extra,
    }


def route_strategic_direction_next_growth_decision_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_strategic_direction_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_strategic_direction_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Strategic direction note recorded ({record.get('kind', 'note')}). "
            "Intelligence evaluates options — no strategy execution or budget allocation."
        )
        return (
            body,
            "workstream_strategic_direction_next_growth_decision_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "strategic_direction_dashboard")
    result = build_strategic_direction_next_growth_decision_program(session_id=sid)
    markdown = render_strategic_direction_next_growth_decision_program(
        result.strategic_direction_next_growth_decision_program,
        focus=focus,
    )
    metrics = result.strategic_direction_next_growth_decision_program.get("metrics") or {}
    headline = (
        f"Growth potential **{metrics.get('growth_potential_score')}** · "
        f"Leverage **{metrics.get('strategic_leverage_score')}** · "
        f"Leading outcome **{metrics.get('leading_outcome_category')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_strategic_direction_next_growth_decision_program",
        _meta(sid, stage="view", focus=focus),
    )
