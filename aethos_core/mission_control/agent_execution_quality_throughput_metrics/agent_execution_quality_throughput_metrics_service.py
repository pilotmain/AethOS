# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — agent execution quality and throughput metrics service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_190_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_190,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_FIX,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_INVARIANT,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_PRINCIPLES,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION,
    AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_190,
    DEPLOY_AUTHORITY_FIX_190,
    FORBIDDEN_METRICS_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_190,
    GOVERNANCE_MUTATION_PERFORMED_FIX_190,
    MERGE_AUTHORITY_FIX_190,
    METRIC_AGENT_ROLE_IDS,
    METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190,
    MUTATION_PERFORMED_FIX_190,
    EXECUTION_PERFORMED_FIX_190,
    PROVIDER_AUTHORITY_FIX_190,
    RAILWAY_AUTHORITY_FIX_190,
    THROUGHPUT_METRIC_IDS,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
    list_agent_execution_quality_throughput_metrics_records,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_PIPELINE_ORDER,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
    build_bounded_multi_agent_delivery_execution,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
    list_agent_execution_receipts,
    list_bounded_multi_agent_delivery_execution_records,
)


@dataclass(frozen=True)
class AgentExecutionQualityThroughputMetricsResult:
    ok: bool
    session_id: str
    agent_execution_quality_throughput_metrics: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _receipts_by_role(receipts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {role: [] for role in METRIC_AGENT_ROLE_IDS}
    for receipt in receipts:
        role = str((receipt.get("metadata") or {}).get("agent_role_id") or "")
        if role in grouped:
            grouped[role].append(receipt)
    for role in grouped:
        grouped[role].sort(key=lambda r: str(r.get("recorded_at") or ""))
    return grouped


def _human_intervention_count(
    *,
    session_id: str,
    metrics_records: list[dict[str, Any]],
    execution_records: list[dict[str, Any]],
) -> int:
    count = 0
    for record in metrics_records + execution_records:
        if str(record.get("author") or "") == "operator" and str(record.get("kind") or "") in {
            "human_intervention_note",
            "execution_note",
            "metrics_observation",
            "throughput_note",
        }:
            count += 1

    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    plan = load_issue_plan_for_session(session_id=session_id)
    if plan:
        for event in plan.get("events") or []:
            if str(event.get("actor") or "") == "operator":
                count += 1
    return count


def _alignment_contribution(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
        build_issue_intent_alignment,
    )

    result = build_issue_intent_alignment(session_id=session_id)
    if not result.ok:
        return {
            "contribution_id": "alignment-unavailable",
            "alignment_score": None,
            "contribution_weight": 0,
            "detail": "No FIX 184 alignment assessment for session.",
            "read_only": True,
        }
    board = result.issue_intent_alignment
    score = int(board.get("alignment_score") or 0)
    return {
        "contribution_id": "alignment-score-contribution",
        "alignment_score": score,
        "contribution_weight": min(100, score),
        "aligned": score >= 70,
        "detail": "Alignment score contribution from FIX 184 (advisory).",
        "read_only": True,
    }


def _per_agent_metrics(*, grouped: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role_id in METRIC_AGENT_ROLE_IDS:
        role_receipts = grouped.get(role_id) or []
        successes = sum(1 for r in role_receipts if (r.get("metadata") or {}).get("work_performed"))
        failures = len(role_receipts) - successes
        retry_count = max(0, len(role_receipts) - 1)

        duration_ms: int | None = None
        if len(role_receipts) >= 2:
            start = _parse_ts(str(role_receipts[0].get("recorded_at") or ""))
            end = _parse_ts(str(role_receipts[-1].get("recorded_at") or ""))
            if start and end:
                duration_ms = max(0, int((end - start).total_seconds() * 1000))

        rows.append(
            {
                "metric_row_id": f"agent-{role_id}",
                "agent_role_id": role_id,
                "execution_receipt_count": len(role_receipts),
                "success_count": successes,
                "failure_count": failures,
                "retry_count": retry_count,
                "duration_ms": duration_ms,
                "last_status": (role_receipts[-1].get("metadata") or {}).get("status") if role_receipts else None,
                "read_only": True,
            }
        )
    return rows


def _verification_contribution(*, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    receipts = grouped.get("verification_agent") or []
    if not receipts:
        return {
            "contribution_id": "verification-none",
            "contribution_score": 0,
            "evidence_gaps": [],
            "detail": "No VerificationAgent execution receipts.",
            "read_only": True,
        }
    meta = receipts[-1].get("metadata") or {}
    blockers = list(meta.get("blockers") or [])
    gap_count = len(blockers)
    score = max(0, 100 - gap_count * 15)
    return {
        "contribution_id": "verification-contribution",
        "contribution_score": score,
        "evidence_gaps": blockers[:8],
        "work_performed": bool(meta.get("work_performed")),
        "detail": "Verification contribution from VerificationAgent receipts.",
        "read_only": True,
    }


def _diff_audit_quality(*, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    receipts = grouped.get("diff_audit_agent") or []
    if not receipts:
        return {
            "quality_id": "diff-audit-none",
            "quality_score": 0,
            "scope_drift_detected": None,
            "detail": "No DiffAuditAgent execution receipts.",
            "read_only": True,
        }
    meta = receipts[-1].get("metadata") or {}
    blockers = list(meta.get("blockers") or [])
    drift_penalty = 20 if "patch_proposal_missing" in blockers else 0
    score = 100 - drift_penalty if meta.get("work_performed") else max(0, 40 - drift_penalty)
    return {
        "quality_id": "diff-audit-quality",
        "quality_score": score,
        "scope_drift_detected": "patch_proposal_missing" in blockers,
        "work_performed": bool(meta.get("work_performed")),
        "detail": "Diff audit quality from scope drift signals in receipts.",
        "read_only": True,
    }


def _risk_scoring_consistency(*, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    receipts = grouped.get("risk_agent") or []
    if not receipts:
        return {
            "consistency_id": "risk-none",
            "consistency_score": 0,
            "receipt_count": 0,
            "detail": "No RiskAgent execution receipts.",
            "read_only": True,
        }
    scores: list[int] = []
    for receipt in receipts:
        meta = receipt.get("metadata") or {}
        if meta.get("risk_score") is not None:
            scores.append(int(meta.get("risk_score")))
    consistency = 100 if len(receipts) <= 1 else (80 if len(set(scores)) <= 1 else 50)
    return {
        "consistency_id": "risk-scoring-consistency",
        "consistency_score": consistency,
        "receipt_count": len(receipts),
        "retry_count": max(0, len(receipts) - 1),
        "detail": "Risk scoring consistency across RiskAgent receipts.",
        "read_only": True,
    }


def _package_completion_rate(*, grouped: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    completed = 0
    for role_id in METRIC_AGENT_ROLE_IDS:
        receipts = grouped.get(role_id) or []
        if receipts and (receipts[-1].get("metadata") or {}).get("work_performed"):
            completed += 1
    total = len(METRIC_AGENT_ROLE_IDS)
    rate = round((completed / total) * 100, 1) if total else 0.0
    return {
        "rate_id": "package-completion-rate",
        "completed_packages": completed,
        "total_packages": total,
        "completion_rate_percent": rate,
        "pipeline_order": list(AGENT_EXECUTION_PIPELINE_ORDER),
        "read_only": True,
    }


def _end_to_end_throughput_score(
    *,
    per_agent: list[dict[str, Any]],
    package_completion: dict[str, Any],
    alignment: dict[str, Any],
    verification: dict[str, Any],
    diff_audit: dict[str, Any],
    risk: dict[str, Any],
    human_interventions: int,
) -> dict[str, Any]:
    success_total = sum(row.get("success_count") or 0 for row in per_agent)
    receipt_total = sum(row.get("execution_receipt_count") or 0 for row in per_agent)
    success_rate = (success_total / receipt_total * 100) if receipt_total else 0.0

    score = 0.0
    score += float(package_completion.get("completion_rate_percent") or 0) * 0.35
    score += success_rate * 0.2
    score += float(alignment.get("contribution_weight") or 0) * 0.15
    score += float(verification.get("contribution_score") or 0) * 0.1
    score += float(diff_audit.get("quality_score") or 0) * 0.1
    score += float(risk.get("consistency_score") or 0) * 0.1
    score -= min(30, human_interventions * 5)
    score = max(0.0, min(100.0, round(score, 1)))

    label = "high" if score >= 75 else "moderate" if score >= 50 else "low" if score > 0 else "unmeasured"
    return {
        "score_id": "end-to-end-throughput",
        "throughput_score": score,
        "throughput_label": label,
        "success_rate_percent": round(success_rate, 1),
        "human_intervention_penalty_applied": human_interventions > 0,
        "metrics_not_authority": True,
        "detail": "Composite throughput score — evidence only, not authority.",
        "read_only": True,
    }


def build_agent_execution_quality_throughput_metrics(
    *, session_id: str
) -> AgentExecutionQualityThroughputMetricsResult:
    sid = (session_id or "default").strip()[:64] or "default"

    execution_view = build_bounded_multi_agent_delivery_execution(session_id=sid)
    execution_payload = (
        execution_view.bounded_multi_agent_delivery_execution if execution_view.ok else {}
    )
    plan_id = str(execution_payload.get("plan_id") or "") or None
    correlation_id = str(execution_payload.get("correlation_id") or "") or None

    receipts_all = list_agent_execution_receipts(session_id=sid, plan_id=None)
    receipts = receipts_all
    if plan_id:
        scoped = [r for r in receipts_all if str(r.get("plan_id") or "") in ("", plan_id)]
        if scoped:
            receipts = scoped
    execution_records = list_bounded_multi_agent_delivery_execution_records(
        session_id=sid, plan_id=None
    )
    if plan_id:
        scoped_records = [
            r for r in execution_records if str(r.get("plan_id") or "") in ("", plan_id)
        ]
        if scoped_records:
            execution_records = scoped_records
    metrics_records = list_agent_execution_quality_throughput_metrics_records(
        session_id=sid, plan_id=plan_id
    )

    grouped = _receipts_by_role(receipts)
    per_agent = _per_agent_metrics(grouped=grouped)
    alignment = _alignment_contribution(session_id=sid)
    verification = _verification_contribution(grouped=grouped)
    diff_audit = _diff_audit_quality(grouped=grouped)
    risk = _risk_scoring_consistency(grouped=grouped)
    package_completion = _package_completion_rate(grouped=grouped)
    human_interventions = _human_intervention_count(
        session_id=sid,
        metrics_records=metrics_records,
        execution_records=execution_records,
    )
    throughput = _end_to_end_throughput_score(
        per_agent=per_agent,
        package_completion=package_completion,
        alignment=alignment,
        verification=verification,
        diff_audit=diff_audit,
        risk=risk,
        human_interventions=human_interventions,
    )

    blockers: list[str] = []
    if not receipts:
        blockers.append("no_fix_189_execution_receipts")

    sections = {
        "per_agent_execution_receipts": [
            {
                "receipt_id": r.get("record_id"),
                "agent_role_id": (r.get("metadata") or {}).get("agent_role_id"),
                "recorded_at": r.get("recorded_at"),
                "work_performed": (r.get("metadata") or {}).get("work_performed"),
                "status": (r.get("metadata") or {}).get("status"),
                "read_only": True,
            }
            for r in receipts
        ],
        "time_per_agent": [
            {
                "agent_role_id": row["agent_role_id"],
                "duration_ms": row["duration_ms"],
                "receipt_count": row["execution_receipt_count"],
                "read_only": True,
            }
            for row in per_agent
        ],
        "success_failure_per_agent": per_agent,
        "retry_count": [
            {
                "agent_role_id": row["agent_role_id"],
                "retry_count": row["retry_count"],
                "read_only": True,
            }
            for row in per_agent
        ],
        "human_intervention_count": [
            {
                "count_id": "human-intervention-total",
                "intervention_count": human_interventions,
                "includes_operator_plan_events": True,
                "read_only": True,
            }
        ],
        "alignment_score_contribution": [alignment],
        "verification_contribution": [verification],
        "diff_audit_quality": [diff_audit],
        "risk_scoring_consistency": [risk],
        "package_completion_rate": [package_completion],
        "end_to_end_throughput_score": [throughput],
        "forbidden_metrics_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_METRICS_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION,
        "fix": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_190,
        "execution_performed": EXECUTION_PERFORMED_FIX_190,
        "metrics_compose_receipts_only": METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190,
        "agent_metrics_grant_authority": AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_190,
        "merge_authority": MERGE_AUTHORITY_FIX_190,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_190,
        "railway_authority": RAILWAY_AUTHORITY_FIX_190,
        "provider_authority": PROVIDER_AUTHORITY_FIX_190,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_190,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_190,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_190,
        "invariant": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "throughput_score": throughput.get("throughput_score"),
        "throughput_label": throughput.get("throughput_label"),
        "package_completion_rate_percent": package_completion.get("completion_rate_percent"),
        "human_intervention_count": human_interventions,
        "execution_receipt_count": len(receipts),
        "metric_ids": list(THROUGHPUT_METRIC_IDS),
        "sections": sections,
        "metrics_record_count": len(metrics_records),
        "fix_190_certification_requirements": list(FIX_190_CERTIFICATION_REQUIREMENTS),
        "agent_execution_quality_throughput_metrics_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_PRINCIPLES
        ],
        "sources": {
            "bounded_multi_agent_delivery_execution": execution_view.ok,
            "fix_189_receipt_count": len(receipts),
            "pipeline_state": execution_payload.get("pipeline_state"),
        },
    }

    return AgentExecutionQualityThroughputMetricsResult(
        ok=True,
        session_id=sid,
        agent_execution_quality_throughput_metrics=payload,
        blockers=blockers,
        detail="Agent execution quality and throughput metrics assembled (agent metrics ≠ agent authority).",
    )
