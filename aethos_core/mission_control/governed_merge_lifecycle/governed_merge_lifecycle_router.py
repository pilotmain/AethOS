# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — chat router for governed merge lifecycle."""

from __future__ import annotations

from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
    APPROVAL_BYPASS_ENABLED_FIX_200,
    AUTONOMOUS_MERGE_ENABLED_FIX_200,
    DEPLOY_AUTHORITY_FIX_200,
    GATE_BYPASS_ENABLED_FIX_200,
    GOVERNED_MERGE_LIFECYCLE_ROUTE_ID,
    MERGE_AUTHORITY_FIX_200,
    MUTATION_PERFORMED_FIX_200,
    PROVIDER_AUTHORITY_FIX_200,
    RAILWAY_AUTHORITY_FIX_200,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_intent import (
    is_governed_merge_handoff_intent,
    is_governed_merge_lifecycle_intent,
    parse_governed_merge_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_renderer import (
    render_governed_merge_lifecycle,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
    build_governed_merge_lifecycle,
    prepare_governed_merge_handoff,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
    append_governed_merge_lifecycle_record,
)
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_MERGE_LIFECYCLE_ROUTE_ID,
        "matched_module": (
            "mission_control.governed_merge_lifecycle.governed_merge_lifecycle_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_200 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_200 is False else "true",
        "autonomous_merge_enabled": "false"
        if AUTONOMOUS_MERGE_ENABLED_FIX_200 is False
        else "true",
        "approval_bypass_enabled": "false"
        if APPROVAL_BYPASS_ENABLED_FIX_200 is False
        else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_200 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_200 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_200 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_200 is False else "true",
        "mutation_scope": "governed_merge_lifecycle",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "merge_lifecycle_not_autonomous_merge",
        **extra,
    }


def route_governed_merge_lifecycle(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_governed_merge_lifecycle_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        plan = load_issue_plan_for_session(session_id=session_id)
        plan_id = str((plan or {}).get("plan_id") or "") or None
        record, blockers = append_governed_merge_lifecycle_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=plan_id,
        )
        if blockers or not record:
            body = f"Merge lifecycle record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_governed_merge_lifecycle_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Merge lifecycle record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "merge_authority ≠ autonomous_merge."
        )
        return (
            body,
            "mission_control_governed_merge_lifecycle_record",
            _meta(session_id, stage="merge_decision", record_id=str(record.get("record_id") or "")),
        )

    if is_governed_merge_handoff_intent(text):
        handoff = prepare_governed_merge_handoff(session_id=session_id)
        if not handoff.ok:
            body = f"Merge handoff blocked: {', '.join(handoff.blockers)}"
            return (
                body,
                "mission_control_governed_merge_handoff_blocked",
                _meta(session_id, stage="handoff_blocked"),
            )
        adapter = handoff.merge_handoff.get("merge_execution_adapter") or {}
        body = (
            "Merge execution request artifact prepared. "
            f"Adapter: `{adapter.get('command_template') or adapter.get('adapter_id')}`. "
            "Human must execute merge — AethOS does not merge autonomously."
        )
        return (
            body,
            "mission_control_governed_merge_handoff",
            _meta(session_id, stage="merge_handoff"),
        )

    if not is_governed_merge_lifecycle_intent(text):
        return None

    result = build_governed_merge_lifecycle(session_id=session_id)
    body = render_governed_merge_lifecycle(result.governed_merge_lifecycle)
    return (
        body,
        "mission_control_governed_merge_lifecycle",
        _meta(session_id, stage="governed_merge_lifecycle"),
    )
