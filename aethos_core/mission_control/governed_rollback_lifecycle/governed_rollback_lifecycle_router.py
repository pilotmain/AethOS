# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — chat router for governed rollback lifecycle."""

from __future__ import annotations

from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
    AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
    DATABASE_MUTATION_AUTHORITY_FIX_230,
    DEPLOY_AUTHORITY_FIX_230,
    GATE_BYPASS_ENABLED_FIX_230,
    GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID,
    MERGE_AUTHORITY_FIX_230,
    MONITORING_AUTHORITY_FIX_230,
    MUTATION_PERFORMED_FIX_230,
    PROVIDER_MUTATION_AUTHORITY_FIX_230,
    RAILWAY_AUTHORITY_FIX_230,
    ROLLBACK_AUTHORITY_FIX_230,
    WORKFLOW_EXECUTION_PERFORMED_FIX_230,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_intent import (
    is_governed_rollback_handoff_intent,
    is_governed_rollback_lifecycle_intent,
    parse_governed_rollback_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_renderer import (
    render_governed_rollback_lifecycle,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
    build_governed_rollback_lifecycle,
    prepare_governed_rollback_handoff,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_store import (
    append_governed_rollback_lifecycle_record,
)
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_ROLLBACK_LIFECYCLE_ROUTE_ID,
        "matched_module": (
            "mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_230 is False else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_230 is False else "true",
        "autonomous_rollback_enabled": "false"
        if AUTONOMOUS_ROLLBACK_ENABLED_FIX_230 is False
        else "true",
        "workflow_execution_performed": "false"
        if WORKFLOW_EXECUTION_PERFORMED_FIX_230 is False
        else "true",
        "monitoring_authority": "false" if MONITORING_AUTHORITY_FIX_230 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_230 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_230 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_230 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_230 is False
        else "true",
        "database_mutation_authority": "false"
        if DATABASE_MUTATION_AUTHORITY_FIX_230 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_230 is False else "true",
        "mutation_scope": "governed_rollback_lifecycle",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "rollback_not_autonomous_rollback",
        **extra,
    }


def route_governed_rollback_lifecycle(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_rollback_lifecycle_record_intent(text)
    if record_intent is not None:
        kind, content, metadata = record_intent
        plan = load_issue_plan_for_session(session_id=session_id)
        plan_id = str((plan or {}).get("plan_id") or "") or None
        record, blockers = append_governed_rollback_lifecycle_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=plan_id,
            metadata=metadata,
        )
        if blockers or not record:
            body = f"Rollback lifecycle record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_rollback_lifecycle_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Rollback lifecycle record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "rollback_authority ≠ autonomous_rollback."
        )
        return (
            body,
            "mission_control_governed_rollback_lifecycle_record",
            _meta(session_id, stage="rollback_decision", record_id=str(record.get("record_id") or "")),
        )

    if is_governed_rollback_handoff_intent(text):
        handoff = prepare_governed_rollback_handoff(session_id=session_id)
        if not handoff.ok:
            body = f"Rollback handoff blocked: {', '.join(handoff.blockers)}"
            return (
                body,
                "mission_control_governed_rollback_handoff_blocked",
                _meta(session_id, stage="handoff_blocked"),
            )
        adapter = handoff.rollback_handoff.get("github_actions_rollback_adapter") or {}
        body = (
            f"Rollback execution request prepared (`{handoff.rollback_handoff.get('handoff_id')}`). "
            f"Human command: `{adapter.get('command_template')}`. "
            "AethOS does not execute rollbacks."
        )
        return (
            body,
            "mission_control_governed_rollback_handoff",
            _meta(session_id, stage="rollback_handoff"),
        )

    if not is_governed_rollback_lifecycle_intent(text):
        return None

    result = build_governed_rollback_lifecycle(session_id=session_id)
    body = render_governed_rollback_lifecycle(result.governed_rollback_lifecycle)
    return (
        body,
        "mission_control_governed_rollback_lifecycle",
        _meta(session_id, stage="governed_rollback_lifecycle"),
    )
