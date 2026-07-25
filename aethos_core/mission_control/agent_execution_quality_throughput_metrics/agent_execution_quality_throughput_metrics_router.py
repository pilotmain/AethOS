# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — chat router for agent execution quality and throughput metrics."""

from __future__ import annotations

from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_190,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID,
    AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
    DEPLOY_AUTHORITY_FIX_190,
    GATE_BYPASS_ENABLED_FIX_190,
    MERGE_AUTHORITY_FIX_190,
    MUTATION_PERFORMED_FIX_190,
    PROVIDER_AUTHORITY_FIX_190,
    RAILWAY_AUTHORITY_FIX_190,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_intent import (
    is_agent_execution_quality_throughput_metrics_intent,
    parse_agent_execution_quality_throughput_metrics_record_intent,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_renderer import (
    render_agent_execution_quality_throughput_metrics,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_service import (
    build_agent_execution_quality_throughput_metrics,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
    append_agent_execution_quality_throughput_metrics_record,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
    build_bounded_multi_agent_delivery_execution,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID,
        "matched_module": (
            "mission_control.agent_execution_quality_throughput_metrics."
            "agent_execution_quality_throughput_metrics_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_190 is False else "true",
        "agent_metrics_grant_authority": "false" if AGENT_METRICS_GRANT_AUTHORITY_FIX_190 is False else "true",
        "agent_execution_authority": "false" if AGENT_EXECUTION_AUTHORITY_FIX_190 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_190 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_190 is False else "true",
        "railway_authority": "false" if RAILWAY_AUTHORITY_FIX_190 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_190 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_190 is False else "true",
        "mutation_scope": "agent_execution_quality_throughput_metrics",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "agent_metrics_not_authority",
        **extra,
    }


def route_agent_execution_quality_throughput_metrics(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_agent_execution_quality_throughput_metrics_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        execution = build_bounded_multi_agent_delivery_execution(session_id=session_id)
        board = execution.bounded_multi_agent_delivery_execution if execution.ok else {}
        record, blockers = append_agent_execution_quality_throughput_metrics_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(board.get("plan_id") or "") or None,
            correlation_id=str(board.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Agent metrics record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_agent_execution_quality_throughput_metrics_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Agent metrics record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Metrics ≠ authority."
        )
        return (
            body,
            "mission_control_agent_execution_quality_throughput_metrics_record",
            _meta(session_id, stage="metrics_record", record_id=str(record.get("record_id") or "")),
        )

    if not is_agent_execution_quality_throughput_metrics_intent(text):
        return None

    result = build_agent_execution_quality_throughput_metrics(session_id=session_id)
    body = render_agent_execution_quality_throughput_metrics(
        result.agent_execution_quality_throughput_metrics
    )
    return (
        body,
        "mission_control_agent_execution_quality_throughput_metrics",
        _meta(
            session_id,
            stage="agent_execution_quality_throughput_metrics",
            throughput_score=str(result.agent_execution_quality_throughput_metrics.get("throughput_score") or ""),
        ),
    )
