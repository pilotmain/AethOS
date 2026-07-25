# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — chat router for pilot validation trust board."""

from __future__ import annotations

from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_contract import (
    AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183,
    DIRECT_EXECUTION_PERFORMED_FIX_183,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183,
    EXECUTION_PERFORMED_FIX_183,
    GATE_BYPASS_ENABLED_FIX_183,
    MUTATION_PERFORMED_FIX_183,
    PILOT_REEXECUTION_PERFORMED_FIX_183,
    PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_intent import (
    is_pilot_validation_trust_board_intent,
    parse_pilot_validation_trust_board_record_intent,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_renderer import (
    render_pilot_validation_trust_board,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
    build_pilot_validation_trust_board,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_store import (
    append_pilot_validation_trust_board_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID,
        "matched_module": "mission_control.pilot_validation_trust_board.pilot_validation_trust_board_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_183 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_183 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_183 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183 is False
        else "true",
        "pilot_reexecution_performed": "false" if PILOT_REEXECUTION_PERFORMED_FIX_183 is False else "true",
        "autonomous_validation_execution_enabled": "false"
        if AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_183 is False else "true",
        "mutation_scope": "pilot_validation_trust_board_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "validation_board_not_pilot_reexecution",
        **extra,
    }


def route_pilot_validation_trust_board(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_pilot_validation_trust_board_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        harness = build_end_to_end_repo_development_pilot_harness(session_id=session_id)
        ctx = harness.end_to_end_repo_development_pilot_harness if harness.ok else {}
        record, blockers = append_pilot_validation_trust_board_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Validation board record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_pilot_validation_trust_board_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Validation board record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show pilot validation` to review trust metrics."
        )
        return (
            body,
            "mission_control_pilot_validation_trust_board_record",
            _meta(
                session_id,
                stage="pilot_validation_trust_board_record",
                record_id=str(record.get("record_id") or ""),
                pilot_validation_trust_board_memory_only="true",
            ),
        )

    if not is_pilot_validation_trust_board_intent(text):
        return None

    result = build_pilot_validation_trust_board(session_id=session_id)
    if not result.ok:
        body = f"Pilot validation trust board unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_pilot_validation_trust_board_blocked",
            _meta(session_id, stage="blocked"),
        )

    board = result.pilot_validation_trust_board
    body = render_pilot_validation_trust_board(board)
    return (
        body,
        "mission_control_pilot_validation_trust_board",
        _meta(
            session_id,
            stage="pilot_validation_trust_board",
            trust_recommendation=str(board.get("trust_recommendation") or "none"),
            pilot_audit_count=str(board.get("pilot_audit_count", 0)),
        ),
    )
