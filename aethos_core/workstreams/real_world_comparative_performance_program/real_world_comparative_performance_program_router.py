# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 / FIX 365 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    AUTHORITY_EXPANSION_FIX_365,
    COMPETITIVE_ACTIONS_FIX_365,
    COMPETITIVE_AUTHORITY_FIX_365,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_365,
    GOVERNANCE_BYPASS_FIX_365,
    GOVERNANCE_MUTATION_FIX_365,
    LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365,
    MUTATION_PERFORMED_FIX_365,
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ROUTE_ID,
    STRATEGY_MUTATION_FIX_365,
    TRUST_MUTATION_AUTHORITY_FIX_365,
    TRUST_PROMOTION_FIX_365,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_intent import (
    handle_comparative_performance_intent,
    parse_comparative_performance_intent,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_renderer import (
    render_real_world_comparative_performance_program,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_service import (
    build_real_world_comparative_performance_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.real_world_comparative_performance_program."
            "real_world_comparative_performance_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_365 is False else "true",
        "competitive_authority": "false" if COMPETITIVE_AUTHORITY_FIX_365 is False else "true",
        "competitive_actions": "false" if COMPETITIVE_ACTIONS_FIX_365 is False else "true",
        "strategy_mutation": "false" if STRATEGY_MUTATION_FIX_365 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_365 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_365 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_365 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_365 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_365 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_365 is False else "true",
        "local_real_world_comparative_performance_executable": (
            "true" if LOCAL_REAL_WORLD_COMPARATIVE_PERFORMANCE_EXECUTABLE_FIX_365 is True else "false"
        ),
        "mutation_scope": "real_world_comparative_performance_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "comparative_performance_not_competitive_authority",
        **extra,
    }


def route_real_world_comparative_performance_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_comparative_performance_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_comparative_performance_intent(intent, session_id=sid)

    if handled.get("action") == "benchmark":
        entry = handled.get("entry") or {}
        body = (
            f"Comparative benchmark **{entry.get('benchmark_id')}** registered "
            f"({entry.get('approach')} / {entry.get('category')}). "
            "Comparative performance ≠ competitive authority."
        )
        return (
            body,
            "phase_real_world_comparative_performance_program_benchmark",
            _meta(sid, stage="benchmark"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Comparative performance note recorded ({record.get('kind', 'note')}). "
            "Evaluation measures outcomes — humans remain responsible for interpretation."
        )
        return (
            body,
            "phase_real_world_comparative_performance_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "comparative_performance_dashboard")
    result = build_real_world_comparative_performance_program(session_id=sid)
    markdown = render_real_world_comparative_performance_program(
        result.real_world_comparative_performance_program,
        focus=focus,
    )
    metrics = result.real_world_comparative_performance_program.get("metrics") or {}
    headline = (
        f"Comparison **{metrics.get('comparison_level')}** · "
        f"Delivery **{metrics.get('delivery_performance_delta')}** · "
        f"Customer **{metrics.get('customer_outcome_delta')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "phase_real_world_comparative_performance_program",
        _meta(sid, stage="view", focus=focus),
    )
