# SPDX-License-Identifier: Apache-2.0
"""FIX 195 — chat router for Nexora pilot arc orchestrator."""

from __future__ import annotations

from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    CROSS_REPO_AUTHORITY_FIX_195,
    DEPLOY_AUTHORITY_FIX_195,
    GATE_BYPASS_ENABLED_FIX_195,
    MERGE_AUTHORITY_FIX_195,
    MUTATION_PERFORMED_FIX_195,
    NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    PROVIDER_AUTHORITY_FIX_195,
    RAILWAY_MUTATION_ENABLED_FIX_195,
    ROLLBACK_AUTHORITY_FIX_195,
    TRUST_GRANTING_AUTHORITY_FIX_195,
    TRUST_INHERITANCE_ENABLED_FIX_195,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_intent import (
    is_nexora_pilot_arc_orchestrator_intent,
    parse_nexora_pilot_arc_orchestrator_record_intent,
    parse_run_nexora_pilot_intent,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_renderer import (
    render_nexora_pilot_arc_orchestrator,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_service import (
    build_nexora_pilot_arc_orchestrator,
    run_nexora_pilot_arc_pilot,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
    append_nexora_pilot_arc_orchestrator_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
        "matched_module": (
            "mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_195 is False else "true",
        "trust_granting_authority": "false" if TRUST_GRANTING_AUTHORITY_FIX_195 is False else "true",
        "trust_inheritance_enabled": "false"
        if TRUST_INHERITANCE_ENABLED_FIX_195 is False
        else "true",
        "cross_repo_authority": "false" if CROSS_REPO_AUTHORITY_FIX_195 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_195 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_195 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_195 is False else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_195 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_195 is False else "true",
        "railway_mutation_enabled": "false" if RAILWAY_MUTATION_ENABLED_FIX_195 is False else "true",
        "mutation_scope": "nexora_pilot_arc_orchestrator",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "pilot_arc_orchestration_not_trust_granting",
        **extra,
    }


def route_nexora_pilot_arc_orchestrator(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    pilot_num = parse_run_nexora_pilot_intent(text)
    if pilot_num is not None:
        outcome = run_nexora_pilot_arc_pilot(pilot_number=pilot_num)
        body = (
            f"Nexora pilot {pilot_num} routed through FIX 181. "
            f"Session `{outcome.session_id}`. Audit `{outcome.audit_id or 'none'}`. "
            f"Stages: {', '.join(outcome.stages_completed) or 'none'}."
        )
        if not outcome.ok:
            body = f"Nexora pilot partial/blocked: {', '.join(outcome.blockers)}. {body}"
        return (
            body,
            "mission_control_nexora_pilot_arc_orchestrator_run",
            _meta(
                session_id,
                stage="pilot_arc_run",
                pilot_number=str(pilot_num),
                audit_id=outcome.audit_id or "",
                execution_routed_through_fix_181="true",
            ),
        )

    record_intent = parse_nexora_pilot_arc_orchestrator_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        record, blockers = append_nexora_pilot_arc_orchestrator_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"Nexora pilot arc record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_nexora_pilot_arc_orchestrator_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Nexora pilot arc record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show nexora pilot arc` to review state."
        )
        return (
            body,
            "mission_control_nexora_pilot_arc_orchestrator_record",
            _meta(session_id, stage="pilot_arc_record", record_id=str(record.get("record_id") or "")),
        )

    if not is_nexora_pilot_arc_orchestrator_intent(text):
        return None

    result = build_nexora_pilot_arc_orchestrator(session_id=session_id)
    body = render_nexora_pilot_arc_orchestrator(result.nexora_pilot_arc_orchestrator)
    return (
        body,
        "mission_control_nexora_pilot_arc_orchestrator",
        _meta(
            session_id,
            stage="nexora_pilot_arc_orchestrator",
            arc_state=str(result.nexora_pilot_arc_orchestrator.get("arc_state") or ""),
        ),
    )
