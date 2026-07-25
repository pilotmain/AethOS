# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — chat router for end-to-end repo development pilot harness."""

from __future__ import annotations

from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
    DEPLOY_ENABLED_FIX_181,
    DIRECT_EXECUTION_PERFORMED_FIX_181,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID,
    EXECUTION_PERFORMED_FIX_181,
    GATE_BYPASS_ENABLED_FIX_181,
    MERGE_ENABLED_FIX_181,
    MUTATION_PERFORMED_FIX_181,
    RAILWAY_MUTATION_ENABLED_FIX_181,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_intent import (
    is_end_to_end_repo_development_pilot_harness_intent,
    is_run_pilot_harness_intent,
    parse_end_to_end_repo_development_pilot_harness_record_intent,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_renderer import (
    render_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
    run_end_to_end_repo_development_pilot,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    append_end_to_end_repo_development_pilot_harness_record,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
    build_governed_chat_command_invocation_from_handoff,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID,
        "matched_module": "mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_181 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_181 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_181 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181 is False
        else "true",
        "autonomous_pipeline_execution_enabled": "false"
        if AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_181 is False else "true",
        "merge_enabled": "false" if MERGE_ENABLED_FIX_181 is False else "true",
        "deploy_enabled": "false" if DEPLOY_ENABLED_FIX_181 is False else "true",
        "railway_mutation_enabled": "false" if RAILWAY_MUTATION_ENABLED_FIX_181 is False else "true",
        "mutation_scope": "end_to_end_repo_development_pilot_harness_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "pilot_harness_not_autonomous_execution",
        **extra,
    }


def route_end_to_end_repo_development_pilot_harness(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if is_run_pilot_harness_intent(text):
        outcome = run_end_to_end_repo_development_pilot(session_id=session_id)
        report = outcome.pilot_report
        body = (
            f"Pilot run complete through chat governance. Audit `{outcome.audit_id}`. "
            f"Stages completed: {', '.join(outcome.stages_completed) or 'none'}. "
            f"Railway coupling: {report.get('railway_coupling_detected', False)}. "
            f"Autonomous execution: false.\n\n"
            f"Evidence bundle ok: {report.get('evidence_bundle_ok')}. "
            f"Pending stages: {', '.join(report.get('stages_pending') or []) or 'none'}."
        )
        if not outcome.ok:
            body = (
                f"Pilot run partial/blocked: {', '.join(outcome.blockers) or 'see stage matrix'}. "
                f"Audit `{outcome.audit_id}`.\n\n{body}"
            )
        return (
            body,
            "mission_control_end_to_end_repo_development_pilot_harness_run",
            _meta(
                session_id,
                stage="pilot_run",
                audit_id=outcome.audit_id,
                chat_governance_routed="true",
                autonomous_pipeline_execution="false",
            ),
        )

    record_intent = parse_end_to_end_repo_development_pilot_harness_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        invocation = build_governed_chat_command_invocation_from_handoff(session_id=session_id)
        ctx = invocation.governed_chat_command_invocation_from_handoff if invocation.ok else {}
        record, blockers = append_end_to_end_repo_development_pilot_harness_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Pilot harness record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_end_to_end_repo_development_pilot_harness_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Pilot harness record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `run pilot` to advance stages through chat governance."
        )
        return (
            body,
            "mission_control_end_to_end_repo_development_pilot_harness_record",
            _meta(
                session_id,
                stage="pilot_harness_record",
                record_id=str(record.get("record_id") or ""),
                end_to_end_repo_development_pilot_harness_memory_only="true",
            ),
        )

    if not is_end_to_end_repo_development_pilot_harness_intent(text):
        return None

    result = build_end_to_end_repo_development_pilot_harness(session_id=session_id)
    if not result.ok:
        body = f"Pilot harness unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_end_to_end_repo_development_pilot_harness_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_end_to_end_repo_development_pilot_harness(result.end_to_end_repo_development_pilot_harness)
    return (
        body,
        "mission_control_end_to_end_repo_development_pilot_harness",
        _meta(
            session_id,
            stage="end_to_end_repo_development_pilot_harness",
            pilot_record_count=str(
                result.end_to_end_repo_development_pilot_harness.get("pilot_record_count", 0)
            ),
        ),
    )
