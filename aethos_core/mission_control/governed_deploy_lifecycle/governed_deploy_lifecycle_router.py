# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — chat router for governed deploy lifecycle."""

from __future__ import annotations

from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
    APPROVAL_BYPASS_ENABLED_FIX_210,
    AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
    AWS_AUTHORITY_FIX_210,
    DEPLOY_AUTHORITY_FIX_210,
    GATE_BYPASS_ENABLED_FIX_210,
    GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID,
    KUBERNETES_AUTHORITY_FIX_210,
    MERGE_AUTHORITY_FIX_210,
    MUTATION_PERFORMED_FIX_210,
    RAILWAY_AUTHORITY_FIX_210,
    VERCEL_AUTHORITY_FIX_210,
    WORKFLOW_EXECUTION_PERFORMED_FIX_210,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_intent import (
    is_governed_deploy_handoff_intent,
    is_governed_deploy_lifecycle_intent,
    parse_governed_deploy_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_renderer import (
    render_governed_deploy_lifecycle,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
    build_governed_deploy_lifecycle,
    prepare_governed_deploy_handoff,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    append_governed_deploy_lifecycle_record,
)
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_DEPLOY_LIFECYCLE_ROUTE_ID,
        "matched_module": "mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_210 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_210 is False else "true",
        "autonomous_deploy_enabled": "false"
        if AUTONOMOUS_DEPLOY_ENABLED_FIX_210 is False
        else "true",
        "workflow_execution_performed": "false"
        if WORKFLOW_EXECUTION_PERFORMED_FIX_210 is False
        else "true",
        "approval_bypass_enabled": "false"
        if APPROVAL_BYPASS_ENABLED_FIX_210 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_210 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_210 is False else "true",
        "vercel_authority": "false" if VERCEL_AUTHORITY_FIX_210 is False else "true",
        "aws_authority": "false" if AWS_AUTHORITY_FIX_210 is False else "true",
        "kubernetes_authority": "false" if KUBERNETES_AUTHORITY_FIX_210 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_210 is False else "true",
        "mutation_scope": "governed_deploy_lifecycle",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "deploy_lifecycle_not_autonomous_deploy",
        **extra,
    }


def route_governed_deploy_lifecycle(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_deploy_lifecycle_record_intent(text)
    if record_intent is not None:
        kind, content, metadata = record_intent
        plan = load_issue_plan_for_session(session_id=session_id)
        plan_id = str((plan or {}).get("plan_id") or "") or None
        record, blockers = append_governed_deploy_lifecycle_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=plan_id,
            metadata=metadata,
        )
        if blockers or not record:
            body = f"Deploy lifecycle record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_deploy_lifecycle_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Deploy lifecycle record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "deploy_authority ≠ autonomous_deploy."
        )
        return (
            body,
            "mission_control_governed_deploy_lifecycle_record",
            _meta(session_id, stage="deploy_decision", record_id=str(record.get("record_id") or "")),
        )

    if is_governed_deploy_handoff_intent(text):
        handoff = prepare_governed_deploy_handoff(session_id=session_id)
        if not handoff.ok:
            body = f"Deploy handoff blocked: {', '.join(handoff.blockers)}"
            return (
                body,
                "mission_control_governed_deploy_handoff_blocked",
                _meta(session_id, stage="handoff_blocked"),
            )
        adapter = handoff.deploy_handoff.get("github_actions_deployment_adapter") or {}
        body = (
            "Deployment execution request artifact prepared. "
            f"Adapter: `{adapter.get('command_template') or adapter.get('adapter_id')}`. "
            "Human must dispatch GitHub Actions workflow — AethOS does not deploy autonomously."
        )
        return (
            body,
            "mission_control_governed_deploy_handoff",
            _meta(session_id, stage="deploy_handoff"),
        )

    if not is_governed_deploy_lifecycle_intent(text):
        return None

    result = build_governed_deploy_lifecycle(session_id=session_id)
    body = render_governed_deploy_lifecycle(result.governed_deploy_lifecycle)
    return (
        body,
        "mission_control_governed_deploy_lifecycle",
        _meta(session_id, stage="governed_deploy_lifecycle"),
    )
