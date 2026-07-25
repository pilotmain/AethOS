# SPDX-License-Identifier: Apache-2.0
"""PHASE_I2 / FIX 362 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_contract import (
    APPROVAL_BYPASS_FIX_362,
    AUTHORITY_EXPANSION_FIX_362,
    AUTONOMOUS_AUTHORITY_FIX_362,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_362,
    GOVERNANCE_BYPASS_FIX_362,
    GOVERNANCE_MUTATION_FIX_362,
    GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ROUTE_ID,
    LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362,
    MUTATION_PERFORMED_FIX_362,
    TRUST_MUTATION_AUTHORITY_FIX_362,
    TRUST_PROMOTION_FIX_362,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_intent import (
    handle_autonomous_proof_intent,
    parse_autonomous_proof_intent,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_renderer import (
    render_governed_autonomous_execution_proof_program,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_service import (
    build_governed_autonomous_execution_proof_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_AUTONOMOUS_EXECUTION_PROOF_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.governed_autonomous_execution_proof_program."
            "governed_autonomous_execution_proof_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_362 is False else "true",
        "autonomous_authority": "false" if AUTONOMOUS_AUTHORITY_FIX_362 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_362 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_362 is False else "true",
        "governance_bypass": "false" if GOVERNANCE_BYPASS_FIX_362 is False else "true",
        "trust_promotion": "false" if TRUST_PROMOTION_FIX_362 is False else "true",
        "approval_bypass": "false" if APPROVAL_BYPASS_FIX_362 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_362 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_362 is False else "true",
        "local_governed_autonomous_execution_proof_executable": (
            "true" if LOCAL_GOVERNED_AUTONOMOUS_EXECUTION_PROOF_EXECUTABLE_FIX_362 is True else "false"
        ),
        "mutation_scope": "governed_autonomous_execution_proof_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "autonomous_execution_proof_not_autonomous_authority",
        **extra,
    }


def route_governed_autonomous_execution_proof_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_proof_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_proof_intent(intent, session_id=sid)

    if handled.get("action") == "run":
        entry = handled.get("entry") or {}
        body = (
            f"Autonomous proof run **{entry.get('run_id')}** registered "
            f"({entry.get('category')} / {entry.get('outcome')} / {entry.get('verification_state')}). "
            "Autonomous execution proof ≠ autonomous authority."
        )
        return (
            body,
            "phase_governed_autonomous_execution_proof_program_run",
            _meta(sid, stage="run"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Autonomous proof note recorded ({record.get('kind', 'note')}). "
            "Proof measures demonstrated capability — humans remain final authority."
        )
        return (
            body,
            "phase_governed_autonomous_execution_proof_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "autonomous_execution_proof_dashboard")
    result = build_governed_autonomous_execution_proof_program(session_id=sid)
    markdown = render_governed_autonomous_execution_proof_program(
        result.governed_autonomous_execution_proof_program,
        focus=focus,
    )
    metrics = result.governed_autonomous_execution_proof_program.get("metrics") or {}
    headline = (
        f"Proof **{metrics.get('autonomous_proof_level')}** · "
        f"Score **{metrics.get('autonomous_execution_proof_score')}** · "
        f"Success evidence **{metrics.get('success_evidence_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "phase_governed_autonomous_execution_proof_program",
        _meta(sid, stage="view", focus=focus),
    )
