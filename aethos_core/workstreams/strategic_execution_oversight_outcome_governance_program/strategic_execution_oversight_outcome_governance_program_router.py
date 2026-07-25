# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H3 / FIX 360 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_contract import (
    AUTHORITY_EXPANSION_FIX_360,
    AUTOMATIC_INITIATIVE_CHANGES_FIX_360,
    BUDGET_ALLOCATION_FIX_360,
    EXECUTION_AUTHORITY_FIX_360,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_360,
    GOVERNANCE_BYPASS_FIX_360,
    LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360,
    MUTATION_PERFORMED_FIX_360,
    RESOURCE_COMMITMENT_FIX_360,
    STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ROUTE_ID,
    STRATEGY_MUTATION_FIX_360,
    TRUST_MUTATION_AUTHORITY_FIX_360,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_intent import (
    handle_strategic_oversight_intent,
    parse_strategic_oversight_intent,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_renderer import (
    render_strategic_execution_oversight_outcome_governance_program,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_service import (
    build_strategic_execution_oversight_outcome_governance_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": STRATEGIC_EXECUTION_OVERSIGHT_OUTCOME_GOVERNANCE_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.strategic_execution_oversight_outcome_governance_program."
            "strategic_execution_oversight_outcome_governance_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_360 is False else "true",
        "execution_authority": "false" if EXECUTION_AUTHORITY_FIX_360 is False else "true",
        "strategy_mutation": "false" if STRATEGY_MUTATION_FIX_360 is False else "true",
        "budget_allocation": "false" if BUDGET_ALLOCATION_FIX_360 is False else "true",
        "resource_commitment": "false" if RESOURCE_COMMITMENT_FIX_360 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_360 is False else "true",
        "automatic_initiative_changes": "false" if AUTOMATIC_INITIATIVE_CHANGES_FIX_360 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_360 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_360 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_360 is False else "true",
        "local_strategic_oversight_executable": "true" if LOCAL_STRATEGIC_OVERSIGHT_EXECUTABLE_FIX_360 is True else "false",
        "mutation_scope": "strategic_execution_oversight_outcome_governance_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "strategic_oversight_not_execution_authority",
        **extra,
    }


def route_strategic_execution_oversight_outcome_governance_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_strategic_oversight_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_strategic_oversight_intent(intent, session_id=sid)

    if handled.get("action") == "milestone":
        entry = handled.get("entry") or {}
        body = (
            f"Oversight milestone **{entry.get('milestone')}** recorded for "
            f"**{entry.get('initiative_id')}** ({entry.get('status')}). "
            "Strategic oversight ≠ execution authority."
        )
        return (
            body,
            "workstream_strategic_execution_oversight_outcome_governance_program_milestone",
            _meta(sid, stage="milestone"),
        )

    if handled.get("action") == "status":
        entry = handled.get("entry") or {}
        body = (
            f"Initiative **{entry.get('initiative_id')}** status set to **{entry.get('status')}**. "
            "Monitoring only — no execution performed."
        )
        return (
            body,
            "workstream_strategic_execution_oversight_outcome_governance_program_status",
            _meta(sid, stage="status"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Strategic oversight note recorded ({record.get('kind', 'note')}). "
            "Outcome governance evaluates — no strategy mutation or execution."
        )
        return (
            body,
            "workstream_strategic_execution_oversight_outcome_governance_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "strategic_oversight_dashboard")
    result = build_strategic_execution_oversight_outcome_governance_program(session_id=sid)
    markdown = render_strategic_execution_oversight_outcome_governance_program(
        result.strategic_execution_oversight_outcome_governance_program,
        focus=focus,
    )
    metrics = result.strategic_execution_oversight_outcome_governance_program.get("metrics") or {}
    headline = (
        f"Maturity **{metrics.get('oversight_maturity_level')}** · "
        f"Success **{metrics.get('initiative_success_rate')}** · "
        f"Learning **{metrics.get('strategic_learning_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_strategic_execution_oversight_outcome_governance_program",
        _meta(sid, stage="view", focus=focus),
    )
