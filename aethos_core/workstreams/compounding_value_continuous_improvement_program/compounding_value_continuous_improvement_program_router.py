# SPDX-License-Identifier: Apache-2.0
"""PHASE_J3 / FIX 366 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_contract import (
    AUTHORITY_EXPANSION_FIX_366,
    AUTOMATIC_POLICY_CHANGES_FIX_366,
    AUTONOMOUS_SELF_MODIFICATION_FIX_366,
    AUTONOMOUS_STRATEGIC_CONTROL_FIX_366,
    COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_366,
    GOVERNANCE_BYPASS_FIX_366,
    GOVERNANCE_MUTATION_FIX_366,
    LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366,
    MUTATION_PERFORMED_FIX_366,
    TRUST_MUTATION_AUTHORITY_FIX_366,
    TRUST_PROMOTION_FIX_366,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_intent import (
    handle_continuous_improvement_intent,
    parse_continuous_improvement_intent,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_renderer import (
    render_compounding_value_continuous_improvement_program,
)
from aethos_core.workstreams.compounding_value_continuous_improvement_program.compounding_value_continuous_improvement_program_service import (
    build_compounding_value_continuous_improvement_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.compounding_value_continuous_improvement_program."
            "compounding_value_continuous_improvement_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_366 is False else "true",
        "autonomous_self_modification": "false" if AUTONOMOUS_SELF_MODIFICATION_FIX_366 is False else "true",
        "automatic_policy_changes": "false" if AUTOMATIC_POLICY_CHANGES_FIX_366 is False else "true",
        "autonomous_strategic_control": "false" if AUTONOMOUS_STRATEGIC_CONTROL_FIX_366 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_366 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_366 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_366 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_366 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_366 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_366 is False else "true",
        "local_compounding_value_continuous_improvement_executable": (
            "true" if LOCAL_COMPOUNDING_VALUE_CONTINUOUS_IMPROVEMENT_EXECUTABLE_FIX_366 is True else "false"
        ),
        "mutation_scope": "compounding_value_continuous_improvement_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "continuous_improvement_measurement_not_self_modification",
        **extra,
    }


def route_compounding_value_continuous_improvement_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_continuous_improvement_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_continuous_improvement_intent(intent, session_id=sid)

    if handled.get("action") == "baseline":
        entry = handled.get("entry") or {}
        body = (
            f"Improvement baseline **{entry.get('baseline_id')}** registered "
            f"({entry.get('category')} / {entry.get('initial_outcome')} → {entry.get('current_outcome')}). "
            "Continuous improvement measurement ≠ autonomous self-modification."
        )
        return (
            body,
            "phase_compounding_value_continuous_improvement_program_baseline",
            _meta(sid, stage="baseline"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Continuous improvement note recorded ({record.get('kind', 'note')}). "
            "Measurement tracks improvement — humans remain responsible for changes."
        )
        return (
            body,
            "phase_compounding_value_continuous_improvement_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "compounding_value_dashboard")
    result = build_compounding_value_continuous_improvement_program(session_id=sid)
    markdown = render_compounding_value_continuous_improvement_program(
        result.compounding_value_continuous_improvement_program,
        focus=focus,
    )
    metrics = result.compounding_value_continuous_improvement_program.get("metrics") or {}
    headline = (
        f"Improvement **{metrics.get('improvement_level')}** · "
        f"Compounding **{metrics.get('compounding_value_score')}** · "
        f"Velocity **{metrics.get('improvement_velocity')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "phase_compounding_value_continuous_improvement_program",
        _meta(sid, stage="view", focus=focus),
    )
