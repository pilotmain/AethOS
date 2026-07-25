# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — chat router for issue intent alignment."""

from __future__ import annotations

from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
    AUTONOMOUS_AUTHORITY_ENABLED_FIX_184,
    DIRECT_EXECUTION_PERFORMED_FIX_184,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184,
    EXECUTION_PERFORMED_FIX_184,
    GATE_BYPASS_ENABLED_FIX_184,
    ISSUE_INTENT_ALIGNMENT_ROUTE_ID,
    MUTATION_PERFORMED_FIX_184,
    PATCH_EXECUTION_PERFORMED_FIX_184,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_intent import (
    is_issue_intent_alignment_intent,
    parse_issue_intent_alignment_record_intent,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_renderer import (
    render_issue_intent_alignment,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
    build_issue_intent_alignment,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    append_issue_intent_alignment_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": ISSUE_INTENT_ALIGNMENT_ROUTE_ID,
        "matched_module": "mission_control.issue_intent_alignment.issue_intent_alignment_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_184 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_184 is False else "true",
        "patch_execution_performed": "false" if PATCH_EXECUTION_PERFORMED_FIX_184 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_184 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184 is False
        else "true",
        "autonomous_authority_enabled": "false" if AUTONOMOUS_AUTHORITY_ENABLED_FIX_184 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_184 is False else "true",
        "mutation_scope": "issue_intent_alignment_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "alignment_validation_not_patch_execution",
        **extra,
    }


def route_issue_intent_alignment(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_issue_intent_alignment_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        harness = build_end_to_end_repo_development_pilot_harness(session_id=session_id)
        ctx = harness.end_to_end_repo_development_pilot_harness if harness.ok else {}
        record, blockers = append_issue_intent_alignment_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Issue intent alignment record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_issue_intent_alignment_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Issue intent alignment record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show intent alignment` to review alignment score and findings."
        )
        return (
            body,
            "mission_control_issue_intent_alignment_record",
            _meta(
                session_id,
                stage="issue_intent_alignment_record",
                record_id=str(record.get("record_id") or ""),
                issue_intent_alignment_memory_only="true",
            ),
        )

    if not is_issue_intent_alignment_intent(text):
        return None

    result = build_issue_intent_alignment(session_id=session_id)
    if not result.ok:
        body = f"Issue intent alignment unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_issue_intent_alignment_blocked",
            _meta(session_id, stage="blocked"),
        )

    board = result.issue_intent_alignment
    body = render_issue_intent_alignment(board)
    return (
        body,
        "mission_control_issue_intent_alignment",
        _meta(
            session_id,
            stage="issue_intent_alignment",
            alignment_score=str(board.get("alignment_score", 0)),
            escalation_required=str(board.get("escalation_required", False)).lower(),
        ),
    )
