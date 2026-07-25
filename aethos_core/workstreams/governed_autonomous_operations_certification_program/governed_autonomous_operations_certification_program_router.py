# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 / FIX 363 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    APPROVAL_BYPASS_FIX_363,
    AUTHORITY_EXPANSION_FIX_363,
    AUTONOMOUS_AUTHORITY_FIX_363,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_363,
    GOVERNANCE_BYPASS_FIX_363,
    GOVERNANCE_MUTATION_FIX_363,
    GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ROUTE_ID,
    LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363,
    MUTATION_PERFORMED_FIX_363,
    TRUST_MUTATION_AUTHORITY_FIX_363,
    TRUST_PROMOTION_FIX_363,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_intent import (
    handle_autonomous_certification_intent,
    parse_autonomous_certification_intent,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_renderer import (
    render_governed_autonomous_operations_certification_program,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_service import (
    build_governed_autonomous_operations_certification_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.governed_autonomous_operations_certification_program."
            "governed_autonomous_operations_certification_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_363 is False else "true",
        "autonomous_authority": "false" if AUTONOMOUS_AUTHORITY_FIX_363 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_363 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_363 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_363 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_363 is False else "true",
        "approval_bypass": "false" if APPROVAL_BYPASS_FIX_363 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_363 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_363 is False else "true",
        "local_governed_autonomous_operations_certification_executable": (
            "true" if LOCAL_GOVERNED_AUTONOMOUS_OPERATIONS_CERTIFICATION_EXECUTABLE_FIX_363 is True else "false"
        ),
        "mutation_scope": "governed_autonomous_operations_certification_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "autonomous_operations_certification_not_autonomous_authority",
        **extra,
    }


def route_governed_autonomous_operations_certification_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_certification_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_certification_intent(intent, session_id=sid)

    if handled.get("action") == "candidate":
        entry = handled.get("entry") or {}
        body = (
            f"Autonomous certification candidate **{entry.get('candidate_id')}** registered "
            f"({entry.get('workload_category')} / {entry.get('provider_category')}). "
            "Autonomous operations certification ≠ autonomous authority."
        )
        return (
            body,
            "phase_governed_autonomous_operations_certification_program_candidate",
            _meta(sid, stage="candidate"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Autonomous certification note recorded ({record.get('kind', 'note')}). "
            "Certification measures demonstrated capability — humans remain final authority."
        )
        return (
            body,
            "phase_governed_autonomous_operations_certification_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "autonomous_operations_certification_dashboard")
    result = build_governed_autonomous_operations_certification_program(session_id=sid)
    markdown = render_governed_autonomous_operations_certification_program(
        result.governed_autonomous_operations_certification_program,
        focus=focus,
    )
    metrics = result.governed_autonomous_operations_certification_program.get("metrics") or {}
    headline = (
        f"Certification **{metrics.get('autonomous_operations_certification_level')}** · "
        f"Score **{metrics.get('autonomous_operations_certification_score')}** · "
        f"Execution reliability **{metrics.get('execution_reliability_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "phase_governed_autonomous_operations_certification_program",
        _meta(sid, stage="view", focus=focus),
    )
