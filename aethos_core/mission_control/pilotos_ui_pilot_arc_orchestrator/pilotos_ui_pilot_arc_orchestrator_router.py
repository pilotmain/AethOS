# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — chat router for PilotOS UI pilot arc orchestrator."""

from __future__ import annotations

from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
    DEPLOY_ENABLED_FIX_188,
    GATE_BYPASS_ENABLED_FIX_188,
    MERGE_ENABLED_FIX_188,
    MUTATION_PERFORMED_FIX_188,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    RAILWAY_MUTATION_ENABLED_FIX_188,
    TRUST_TRANSFER_ENABLED_FIX_188,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_intent import (
    is_pilotos_ui_pilot_arc_orchestrator_intent,
    parse_pilotos_ui_pilot_arc_orchestrator_record_intent,
    parse_run_pilotos_pilot_intent,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_renderer import (
    render_pilotos_ui_pilot_arc_orchestrator,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_service import (
    build_pilotos_ui_pilot_arc_orchestrator,
    run_pilotos_ui_pilot_arc_pilot,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
    append_pilotos_ui_pilot_arc_orchestrator_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
        "matched_module": "mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_188 is False else "true",
        "automatic_trust_granting_enabled": "false"
        if AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188 is False
        else "true",
        "trust_transfer_enabled": "false" if TRUST_TRANSFER_ENABLED_FIX_188 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_188 is False else "true",
        "merge_enabled": "false" if MERGE_ENABLED_FIX_188 is False else "true",
        "deploy_enabled": "false" if DEPLOY_ENABLED_FIX_188 is False else "true",
        "railway_mutation_enabled": "false" if RAILWAY_MUTATION_ENABLED_FIX_188 is False else "true",
        "mutation_scope": "pilotos_ui_pilot_arc_orchestrator",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "pilot_arc_orchestration_not_trust_granting",
        **extra,
    }


def route_pilotos_ui_pilot_arc_orchestrator(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    pilot_num = parse_run_pilotos_pilot_intent(text)
    if pilot_num is not None:
        outcome = run_pilotos_ui_pilot_arc_pilot(pilot_number=pilot_num)
        body = (
            f"PilotOS UI pilot {pilot_num} routed through FIX 181. "
            f"Session `{outcome.session_id}`. Audit `{outcome.audit_id or 'none'}`. "
            f"Stages: {', '.join(outcome.stages_completed) or 'none'}."
        )
        if not outcome.ok:
            body = f"Pilot partial/blocked: {', '.join(outcome.blockers)}. {body}"
        return (
            body,
            "mission_control_pilotos_ui_pilot_arc_orchestrator_run",
            _meta(
                session_id,
                stage="pilot_arc_run",
                pilot_number=str(pilot_num),
                audit_id=outcome.audit_id or "",
                execution_routed_through_fix_181="true",
            ),
        )

    record_intent = parse_pilotos_ui_pilot_arc_orchestrator_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        if kind == "pilot_arc_trust_decision":
            arc = build_pilotos_ui_pilot_arc_orchestrator(session_id=session_id)
            arc_state = str(arc.pilotos_ui_pilot_arc_orchestrator.get("arc_state") or "")
            if arc_state != "TRUST_REVIEW_PENDING":
                body = (
                    f"Pilot arc trust decision blocked: requires TRUST_REVIEW_PENDING "
                    f"(current: {arc_state}). Pilot completion does not auto-grant trust."
                )
                return (
                    body,
                    "mission_control_pilotos_ui_pilot_arc_orchestrator_trust_blocked",
                    _meta(session_id, stage="trust_decision_blocked", arc_state=arc_state),
                )
        record, blockers = append_pilotos_ui_pilot_arc_orchestrator_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"Pilot arc record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_pilotos_ui_pilot_arc_orchestrator_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Pilot arc record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show pilotos pilot arc` to review state."
        )
        return (
            body,
            "mission_control_pilotos_ui_pilot_arc_orchestrator_record",
            _meta(session_id, stage="pilot_arc_record", record_id=str(record.get("record_id") or "")),
        )

    if not is_pilotos_ui_pilot_arc_orchestrator_intent(text):
        return None

    result = build_pilotos_ui_pilot_arc_orchestrator(session_id=session_id)
    body = render_pilotos_ui_pilot_arc_orchestrator(result.pilotos_ui_pilot_arc_orchestrator)
    return (
        body,
        "mission_control_pilotos_ui_pilot_arc_orchestrator",
        _meta(
            session_id,
            stage="pilotos_ui_pilot_arc_orchestrator",
            arc_state=str(result.pilotos_ui_pilot_arc_orchestrator.get("arc_state") or ""),
        ),
    )
