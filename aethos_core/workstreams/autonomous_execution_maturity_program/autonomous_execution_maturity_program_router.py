# SPDX-License-Identifier: Apache-2.0
"""PHASE_I1 / FIX 361 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_361,
    AUTONOMOUS_AUTHORITY_FIX_361,
    AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361,
    AUTONOMOUS_STRATEGIC_CONTROL_FIX_361,
    AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_361,
    GOVERNANCE_BYPASS_FIX_361,
    GOVERNANCE_MUTATION_FIX_361,
    LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361,
    MUTATION_PERFORMED_FIX_361,
    TRUST_MUTATION_AUTHORITY_FIX_361,
    TRUST_PROMOTION_FIX_361,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_intent import (
    handle_autonomous_execution_intent,
    parse_autonomous_execution_intent,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_renderer import (
    render_autonomous_execution_maturity_program,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_service import (
    build_autonomous_execution_maturity_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": AUTONOMOUS_EXECUTION_MATURITY_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.autonomous_execution_maturity_program."
            "autonomous_execution_maturity_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_361 is False else "true",
        "autonomous_authority": "false" if AUTONOMOUS_AUTHORITY_FIX_361 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_361 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_361 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_361 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_361 is False else "true",
        "autonomous_organizational_control": "false" if AUTONOMOUS_ORGANIZATIONAL_CONTROL_FIX_361 is False else "true",
        "autonomous_strategic_control": "false" if AUTONOMOUS_STRATEGIC_CONTROL_FIX_361 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_361 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_361 is False else "true",
        "local_autonomous_execution_maturity_executable": "true" if LOCAL_AUTONOMOUS_EXECUTION_MATURITY_EXECUTABLE_FIX_361 is True else "false",
        "mutation_scope": "autonomous_execution_maturity_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "autonomous_execution_maturity_not_autonomous_authority",
        **extra,
    }


def route_autonomous_execution_maturity_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_execution_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_execution_intent(intent, session_id=sid)

    if handled.get("action") == "request":
        entry = handled.get("entry") or {}
        body = (
            f"Autonomous execution request **{entry.get('request_id')}** registered "
            f"({entry.get('category')} / {entry.get('outcome')}). "
            "Autonomous execution maturity ≠ autonomous authority."
        )
        return (
            body,
            "phase_autonomous_execution_maturity_program_request",
            _meta(sid, stage="request"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Autonomous execution note recorded ({record.get('kind', 'note')}). "
            "Maturity measures capability — humans remain final authority."
        )
        return (
            body,
            "phase_autonomous_execution_maturity_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "autonomous_execution_dashboard")
    result = build_autonomous_execution_maturity_program(session_id=sid)
    markdown = render_autonomous_execution_maturity_program(
        result.autonomous_execution_maturity_program,
        focus=focus,
    )
    metrics = result.autonomous_execution_maturity_program.get("metrics") or {}
    headline = (
        f"Maturity **{metrics.get('autonomous_maturity_level')}** · "
        f"Score **{metrics.get('autonomous_execution_maturity_score')}** · "
        f"Success **{metrics.get('execution_success_rate')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "phase_autonomous_execution_maturity_program",
        _meta(sid, stage="view", focus=focus),
    )
