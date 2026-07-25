# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H2 / FIX 359 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    AUTHORITY_EXPANSION_FIX_359,
    AUTOMATIC_PRIORITIZATION_FIX_359,
    BUDGET_ALLOCATION_FIX_359,
    EXECUTION_AUTHORITY_FIX_359,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_359,
    GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ROUTE_ID,
    INITIATIVE_LAUNCH_FIX_359,
    LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359,
    MUTATION_PERFORMED_FIX_359,
    PROJECT_CREATION_FIX_359,
    RESOURCE_COMMITMENT_FIX_359,
    ROADMAP_MUTATION_FIX_359,
    STRATEGIC_EXECUTION_AUTHORITY_FIX_359,
    TRUST_MUTATION_AUTHORITY_FIX_359,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_intent import (
    handle_strategic_execution_intent,
    parse_strategic_execution_intent,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_renderer import (
    render_governed_strategic_execution_program,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_service import (
    build_governed_strategic_execution_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_STRATEGIC_EXECUTION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.governed_strategic_execution_program."
            "governed_strategic_execution_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_359 is False else "true",
        "strategic_execution_authority": "false" if STRATEGIC_EXECUTION_AUTHORITY_FIX_359 is False else "true",
        "execution_authority": "false" if EXECUTION_AUTHORITY_FIX_359 is False else "true",
        "budget_allocation": "false" if BUDGET_ALLOCATION_FIX_359 is False else "true",
        "project_creation": "false" if PROJECT_CREATION_FIX_359 is False else "true",
        "resource_commitment": "false" if RESOURCE_COMMITMENT_FIX_359 is False else "true",
        "initiative_launch": "false" if INITIATIVE_LAUNCH_FIX_359 is False else "true",
        "roadmap_mutation": "false" if ROADMAP_MUTATION_FIX_359 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_359 is False else "true",
        "automatic_prioritization": "false" if AUTOMATIC_PRIORITIZATION_FIX_359 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_359 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_359 is False else "true",
        "local_strategic_execution_executable": "true" if LOCAL_STRATEGIC_EXECUTION_EXECUTABLE_FIX_359 is True else "false",
        "mutation_scope": "governed_strategic_execution_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "strategic_execution_planning_not_execution_authority",
        **extra,
    }


def route_governed_strategic_execution_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_strategic_execution_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_strategic_execution_intent(intent, session_id=sid)

    if handled.get("action") == "initiative":
        entry = handled.get("entry") or {}
        body = (
            f"Strategic initiative **{entry.get('initiative_id')}** registered "
            f"({entry.get('growth_path')}). "
            "Strategic execution planning ≠ strategic execution authority."
        )
        return (
            body,
            "workstream_governed_strategic_execution_program_initiative",
            _meta(sid, stage="initiative"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Strategic execution note recorded ({record.get('kind', 'note')}). "
            "Planning prepares execution — no budget allocation or initiative launch."
        )
        return (
            body,
            "workstream_governed_strategic_execution_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "strategic_execution_dashboard")
    result = build_governed_strategic_execution_program(session_id=sid)
    markdown = render_governed_strategic_execution_program(
        result.governed_strategic_execution_program,
        focus=focus,
    )
    metrics = result.governed_strategic_execution_program.get("metrics") or {}
    headline = (
        f"Readiness **{metrics.get('execution_readiness_score')}** · "
        f"Level **{metrics.get('execution_readiness_level')}** · "
        f"Governance **{metrics.get('governance_readiness_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_governed_strategic_execution_program",
        _meta(sid, stage="view", focus=focus),
    )
