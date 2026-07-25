# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — chat router for governed monitoring lifecycle."""

from __future__ import annotations

from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
    AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
    DEPLOY_AUTHORITY_FIX_220,
    GATE_BYPASS_ENABLED_FIX_220,
    GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID,
    INCIDENT_RESPONSE_AUTHORITY_FIX_220,
    MERGE_AUTHORITY_FIX_220,
    MONITORING_AUTHORITY_FIX_220,
    MUTATION_PERFORMED_FIX_220,
    PROVIDER_MUTATION_AUTHORITY_FIX_220,
    RAILWAY_AUTHORITY_FIX_220,
    ROLLBACK_AUTHORITY_FIX_220,
    WORKFLOW_EXECUTION_AUTHORITY_FIX_220,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_intent import (
    is_governed_monitoring_escalation_intent,
    is_governed_monitoring_lifecycle_intent,
    parse_governed_monitoring_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_renderer import (
    render_governed_monitoring_lifecycle,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
    build_governed_monitoring_lifecycle,
    prepare_governed_monitoring_escalation,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
    append_governed_monitoring_lifecycle_record,
)
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_MONITORING_LIFECYCLE_ROUTE_ID,
        "matched_module": (
            "mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_220 is False else "true",
        "monitoring_authority": "false" if MONITORING_AUTHORITY_FIX_220 is False else "true",
        "incident_response_authority": "false"
        if INCIDENT_RESPONSE_AUTHORITY_FIX_220 is False
        else "true",
        "autonomous_remediation_enabled": "false"
        if AUTONOMOUS_REMEDIATION_ENABLED_FIX_220 is False
        else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_220 is False else "true",
        "workflow_execution_authority": "false"
        if WORKFLOW_EXECUTION_AUTHORITY_FIX_220 is False
        else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_220 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_220 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_220 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_220 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_220 is False else "true",
        "mutation_scope": "governed_monitoring_lifecycle",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "monitoring_not_operational_authority",
        **extra,
    }


def route_governed_monitoring_lifecycle(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_monitoring_lifecycle_record_intent(text)
    if record_intent is not None:
        kind, content, metadata = record_intent
        plan = load_issue_plan_for_session(session_id=session_id)
        plan_id = str((plan or {}).get("plan_id") or "") or None
        record, blockers = append_governed_monitoring_lifecycle_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=plan_id,
            metadata=metadata,
        )
        if blockers or not record:
            body = f"Monitoring lifecycle record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_monitoring_lifecycle_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Monitoring lifecycle record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "monitoring_authority ≠ operational_authority."
        )
        return (
            body,
            "mission_control_governed_monitoring_lifecycle_record",
            _meta(session_id, stage="operational_decision", record_id=str(record.get("record_id") or "")),
        )

    if is_governed_monitoring_escalation_intent(text):
        escalation = prepare_governed_monitoring_escalation(session_id=session_id)
        if not escalation.ok:
            body = f"Incident escalation blocked: {', '.join(escalation.blockers)}"
            return (
                body,
                "mission_control_governed_monitoring_escalation_blocked",
                _meta(session_id, stage="escalation_blocked"),
            )
        body = (
            f"Incident escalation artifact prepared (`{escalation.incident_escalation.get('escalation_id')}`). "
            "Human review required — AethOS does not perform remediation."
        )
        return (
            body,
            "mission_control_governed_monitoring_escalation",
            _meta(session_id, stage="incident_escalation"),
        )

    if not is_governed_monitoring_lifecycle_intent(text):
        return None

    result = build_governed_monitoring_lifecycle(session_id=session_id)
    body = render_governed_monitoring_lifecycle(result.governed_monitoring_lifecycle)
    return (
        body,
        "mission_control_governed_monitoring_lifecycle",
        _meta(session_id, stage="governed_monitoring_lifecycle"),
    )
