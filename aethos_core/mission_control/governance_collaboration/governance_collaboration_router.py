# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — chat router for multi-operator governance collaboration."""

from __future__ import annotations

from aethos_core.mission_control.governance_collaboration.governance_collaboration_contract import (
    DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149,
    GOVERNANCE_COLLABORATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_149,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_intent import (
    is_governance_collaboration_intent,
    parse_collaboration_record_intent,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_renderer import (
    render_governance_collaboration,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_service import (
    build_governance_collaboration_workspace,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    append_governance_collaboration_record,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
    build_governance_deliberation_workspace,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_COLLABORATION_ROUTE_ID,
        "matched_module": "mission_control.governance_collaboration.governance_collaboration_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_149 is False else "true",
        "delegated_execution_authority_enabled": "false"
        if DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149 is False
        else "true",
        "mutation_scope": "governance_collaboration_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "collaboration_not_execution",
        **extra,
    }


def route_governance_collaboration(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_collaboration_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        deliberation = build_governance_deliberation_workspace(session_id=session_id)
        workspace = deliberation.workspace if deliberation.ok else {}
        record, blockers = append_governance_collaboration_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(workspace.get("plan_id") or "") or None,
            correlation_id=str(workspace.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Collaboration record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_collaboration_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Collaboration record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Institutional continuity only — no delegated execution authority."
        )
        return (
            body,
            "mission_control_governance_collaboration_record",
            _meta(
                session_id,
                stage="collaboration_record",
                record_id=str(record.get("record_id") or ""),
                collaboration_memory_only="true",
            ),
        )

    if not is_governance_collaboration_intent(text):
        return None

    result = build_governance_collaboration_workspace(session_id=session_id)
    if not result.ok:
        body = f"Governance collaboration unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_collaboration_blocked", _meta(session_id, stage="blocked")

    body = render_governance_collaboration(result.collaboration)
    quorum = (result.collaboration.get("sections") or {}).get("quorum_aware_discussion") or {}
    return (
        body,
        "mission_control_governance_collaboration",
        _meta(
            session_id,
            stage="governance_collaboration",
            collaboration_record_count=str(result.collaboration.get("collaboration_record_count", 0)),
            quorum_advisory_met=str(quorum.get("quorum_advisory_met", False)),
        ),
    )
