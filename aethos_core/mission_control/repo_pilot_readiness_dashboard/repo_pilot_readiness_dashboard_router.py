# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — chat router for repo pilot readiness dashboard."""

from __future__ import annotations

from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_contract import (
    AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182,
    DIRECT_EXECUTION_PERFORMED_FIX_182,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182,
    EXECUTION_PERFORMED_FIX_182,
    GATE_BYPASS_ENABLED_FIX_182,
    MUTATION_PERFORMED_FIX_182,
    PILOT_EXECUTION_PERFORMED_FIX_182,
    REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_intent import (
    is_repo_pilot_readiness_dashboard_intent,
    parse_repo_pilot_readiness_dashboard_record_intent,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_renderer import (
    render_repo_pilot_readiness_dashboard,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    build_repo_pilot_readiness_dashboard,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_store import (
    append_repo_pilot_readiness_dashboard_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID,
        "matched_module": "mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_182 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_182 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_182 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182 is False
        else "true",
        "pilot_execution_performed": "false" if PILOT_EXECUTION_PERFORMED_FIX_182 is False else "true",
        "autonomous_readiness_mutation_enabled": "false"
        if AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_182 is False else "true",
        "mutation_scope": "repo_pilot_readiness_dashboard_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "readiness_dashboard_not_pilot_execution",
        **extra,
    }


def route_repo_pilot_readiness_dashboard(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_repo_pilot_readiness_dashboard_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        harness = build_end_to_end_repo_development_pilot_harness(session_id=session_id)
        ctx = harness.end_to_end_repo_development_pilot_harness if harness.ok else {}
        record, blockers = append_repo_pilot_readiness_dashboard_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ctx.get("plan_id") or "") or None,
            correlation_id=str(ctx.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Readiness dashboard record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_repo_pilot_readiness_dashboard_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Readiness dashboard record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show pilot readiness` to review preflight blockers."
        )
        return (
            body,
            "mission_control_repo_pilot_readiness_dashboard_record",
            _meta(
                session_id,
                stage="repo_pilot_readiness_dashboard_record",
                record_id=str(record.get("record_id") or ""),
                repo_pilot_readiness_dashboard_memory_only="true",
            ),
        )

    if not is_repo_pilot_readiness_dashboard_intent(text):
        return None

    result = build_repo_pilot_readiness_dashboard(session_id=session_id)
    if not result.ok:
        body = f"Repo pilot readiness dashboard unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_repo_pilot_readiness_dashboard_blocked",
            _meta(session_id, stage="blocked"),
        )

    body = render_repo_pilot_readiness_dashboard(result.repo_pilot_readiness_dashboard)
    return (
        body,
        "mission_control_repo_pilot_readiness_dashboard",
        _meta(
            session_id,
            stage="repo_pilot_readiness_dashboard",
            pilot_preflight_ready=str(
                result.repo_pilot_readiness_dashboard.get("pilot_preflight_ready", False)
            ).lower(),
            pilot_blocker_count=str(result.repo_pilot_readiness_dashboard.get("pilot_blocker_count", 0)),
        ),
    )
