# SPDX-License-Identifier: Apache-2.0
"""PHASE_J1 / FIX 364 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_contract import (
    APPROVAL_BYPASS_FIX_364,
    AUTHORITY_EXPANSION_FIX_364,
    AUTONOMOUS_PRODUCTION_CONTROL_FIX_364,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_364,
    GOVERNANCE_BYPASS_FIX_364,
    GOVERNANCE_MUTATION_FIX_364,
    LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364,
    MUTATION_PERFORMED_FIX_364,
    OPERATIONAL_AUTHORITY_FIX_364,
    OPERATIONAL_AUTOMATION_CHANGES_FIX_364,
    PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_364,
    TRUST_PROMOTION_FIX_364,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_intent import (
    handle_production_reality_intent,
    parse_production_reality_intent,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_renderer import (
    render_production_reality_longitudinal_operations_program,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_service import (
    build_production_reality_longitudinal_operations_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.production_reality_longitudinal_operations_program."
            "production_reality_longitudinal_operations_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_364 is False else "true",
        "operational_authority": "false" if OPERATIONAL_AUTHORITY_FIX_364 is False else "true",
        "autonomous_production_control": "false" if AUTONOMOUS_PRODUCTION_CONTROL_FIX_364 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_364 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_364 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_364 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_364 is False else "true",
        "approval_bypass": "false" if APPROVAL_BYPASS_FIX_364 is False else "true",
        "operational_automation_changes": "false" if OPERATIONAL_AUTOMATION_CHANGES_FIX_364 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_364 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_364 is False else "true",
        "local_production_reality_longitudinal_operations_executable": (
            "true" if LOCAL_PRODUCTION_REALITY_LONGITUDINAL_OPERATIONS_EXECUTABLE_FIX_364 is True else "false"
        ),
        "mutation_scope": "production_reality_longitudinal_operations_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "production_reality_measurement_not_operational_authority",
        **extra,
    }


def route_production_reality_longitudinal_operations_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_production_reality_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_production_reality_intent(intent, session_id=sid)

    if handled.get("action") == "observation":
        entry = handled.get("entry") or {}
        body = (
            f"Production reality observation **{entry.get('operation_id')}** registered "
            f"({entry.get('category')} / {entry.get('outcome')}). "
            "Production reality measurement ≠ operational authority."
        )
        return (
            body,
            "phase_production_reality_longitudinal_operations_program_observation",
            _meta(sid, stage="observation"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Production reality note recorded ({record.get('kind', 'note')}). "
            "Measurement tracks durability — humans remain final authority."
        )
        return (
            body,
            "phase_production_reality_longitudinal_operations_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "production_reality_dashboard")
    result = build_production_reality_longitudinal_operations_program(session_id=sid)
    markdown = render_production_reality_longitudinal_operations_program(
        result.production_reality_longitudinal_operations_program,
        focus=focus,
    )
    metrics = result.production_reality_longitudinal_operations_program.get("metrics") or {}
    headline = (
        f"Durability **{metrics.get('durability_level')}** · "
        f"Score **{metrics.get('operational_durability_score')}** · "
        f"Deployment **{metrics.get('deployment_durability_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "phase_production_reality_longitudinal_operations_program",
        _meta(sid, stage="view", focus=focus),
    )
