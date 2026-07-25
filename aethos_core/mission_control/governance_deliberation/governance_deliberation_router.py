# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — chat router for governance deliberation workspace."""

from __future__ import annotations

from aethos_core.mission_control.governance_deliberation.governance_deliberation_contract import (
    AUTOMATIC_APPROVAL_ENABLED_FIX_148,
    GOVERNANCE_DELIBERATION_ROUTE_ID,
    GOVERNANCE_MUTATION_PERFORMED_FIX_148,
    MUTATION_PERFORMED_FIX_148,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_intent import (
    is_governance_deliberation_intent,
    parse_deliberation_record_intent,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_renderer import (
    render_governance_deliberation,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
    build_governance_deliberation_workspace,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    append_governance_deliberation_record,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_DELIBERATION_ROUTE_ID,
        "matched_module": "mission_control.governance_deliberation.governance_deliberation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_148 is False else "true",
        "governance_mutation_performed": "false"
        if GOVERNANCE_MUTATION_PERFORMED_FIX_148 is False
        else "true",
        "automatic_approval_enabled": "false" if AUTOMATIC_APPROVAL_ENABLED_FIX_148 is False else "true",
        "mutation_scope": "governance_deliberation_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "deliberation_not_execution",
        **extra,
    }


def route_governance_deliberation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_deliberation_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        readiness = build_mission_readiness_review(session_id=session_id)
        review = readiness.review if readiness.ok else {}
        record, blockers = append_governance_deliberation_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(review.get("plan_id") or "") or None,
            correlation_id=str(review.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Deliberation record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_deliberation_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Deliberation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Institutional governance memory only — no approval or policy mutation."
        )
        return (
            body,
            "mission_control_governance_deliberation_record",
            _meta(
                session_id,
                stage="deliberation_record",
                record_id=str(record.get("record_id") or ""),
                deliberation_memory_only="true",
            ),
        )

    if not is_governance_deliberation_intent(text):
        return None

    result = build_governance_deliberation_workspace(session_id=session_id)
    if not result.ok:
        body = f"Governance deliberation unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_deliberation_blocked", _meta(session_id, stage="blocked")

    body = render_governance_deliberation(result.workspace)
    return (
        body,
        "mission_control_governance_deliberation",
        _meta(
            session_id,
            stage="governance_deliberation",
            deliberation_record_count=str(result.workspace.get("deliberation_record_count", 0)),
        ),
    )
