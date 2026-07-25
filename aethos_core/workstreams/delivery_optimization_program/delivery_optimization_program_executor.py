# SPDX-License-Identifier: Apache-2.0
"""FIX 340 / WORKSTREAM_C2 — delivery optimization analysis executor."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_contract import (
    EXECUTION_TRACK_FAILURE_KEYS,
    IMPROVEMENT_CATEGORIES,
)
from aethos_core.workstreams.delivery_optimization_program.delivery_optimization_program_store import (
    list_delivery_improvement_opportunity_registry_entries,
    list_delivery_outcome_registry_entries,
    list_delivery_optimization_records,
    register_delivery_outcome,
    register_improvement_opportunity,
)


def _filter_session(rows: list[dict[str, Any]], *, session_id: str | None) -> list[dict[str, Any]]:
    if not session_id:
        return rows
    return [row for row in rows if str(row.get("session_id") or "") == session_id]


def _c1_executions(*, session_id: str | None = None) -> list[dict[str, Any]]:
    from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
        list_delivery_execution_registry_entries,
    )

    return _filter_session(list_delivery_execution_registry_entries(), session_id=session_id)


def _c1_incidents(*, session_id: str | None = None) -> list[dict[str, Any]]:
    from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
        list_delivery_incident_registry_entries,
    )

    return _filter_session(list_delivery_incident_registry_entries(), session_id=session_id)


def _c1_records(*, session_id: str | None = None) -> list[dict[str, Any]]:
    from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
        list_real_world_delivery_proof_records,
    )

    return _filter_session(list_real_world_delivery_proof_records(), session_id=session_id)


def _et5_runs(*, session_id: str | None = None) -> list[dict[str, Any]]:
    from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
        list_delivery_run_registry_entries,
    )

    return _filter_session(list_delivery_run_registry_entries(), session_id=session_id)


def sync_delivery_outcomes(*, session_id: str) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for execution in _c1_executions(session_id=session_id):
        passed = execution.get("passed") is True
        blockers = list(execution.get("blockers") or [])
        outcome_type = "SUCCESS" if passed else "PARTIAL" if blockers else "FAILED"
        entry = register_delivery_outcome(
            entry={
                "outcome_id": f"c2-out-{execution.get('execution_id', uuid4().hex[:8])}",
                "session_id": session_id,
                "source": "workstream_c1",
                "repository": execution.get("repository"),
                "outcome_type": outcome_type,
                "passed": passed,
                "duration_ms": execution.get("duration_ms"),
                "blockers": blockers,
                "recovery_event": passed and bool(blockers) is False and bool(execution.get("duration_ms")),
            }
        )
        outcomes.append(entry)

    for run in _et5_runs(session_id=session_id):
        passed = run.get("passed") is True
        entry = register_delivery_outcome(
            entry={
                "outcome_id": f"c2-out-{run.get('run_id', uuid4().hex[:8])}",
                "session_id": session_id,
                "source": "execution_track_5",
                "scenario_id": run.get("scenario_id"),
                "outcome_type": "SUCCESS" if passed else "FAILED",
                "passed": passed,
                "duration_ms": run.get("duration_ms"),
                "blockers": run.get("blockers") or [],
                "recovery_event": False,
            }
        )
        outcomes.append(entry)

    return outcomes


def build_delivery_outcome_registry(*, session_id: str) -> dict[str, Any]:
    outcomes = sync_delivery_outcomes(session_id=session_id)
    stored = _filter_session(list_delivery_outcome_registry_entries(), session_id=session_id)
    successful = [row for row in stored if row.get("outcome_type") == "SUCCESS"]
    failed = [row for row in stored if row.get("outcome_type") == "FAILED"]
    partial = [row for row in stored if row.get("outcome_type") == "PARTIAL"]
    recovery = [row for row in stored if row.get("recovery_event") is True]

    return {
        "registry_id": "delivery-outcome-registry",
        "outcome_count": len(stored),
        "successful_runs": len(successful),
        "failed_runs": len(failed),
        "partial_runs": len(partial),
        "recovery_events": len(recovery),
        "outcomes": stored[-20:],
        "read_only": True,
    }


def _track_failure_counts(*, session_id: str) -> dict[str, int]:
    counts = {key: 0 for key in EXECUTION_TRACK_FAILURE_KEYS}
    for execution in _c1_executions(session_id=session_id):
        stages = execution.get("stage_results") or {}
        for key in ("execution_track_1", "execution_track_2", "execution_track_3", "execution_track_4"):
            stage = stages.get(key) or {}
            if stage.get("skipped"):
                continue
            if stage.get("verified") is False:
                counts[key] += 1
    for run in _et5_runs(session_id=session_id):
        if run.get("passed") is False:
            counts["execution_track_5"] += 1
        stages = run.get("stage_results") or {}
        for key in ("workspace", "generation", "git_delivery", "deployment"):
            et_key = {
                "workspace": "execution_track_1",
                "generation": "execution_track_2",
                "git_delivery": "execution_track_3",
                "deployment": "execution_track_4",
            }[key]
            stage = stages.get(key) or {}
            if stage.get("skipped"):
                continue
            if stage.get("verified") is False:
                counts[et_key] += 1
    return counts


def analyze_failure_intelligence(*, session_id: str) -> dict[str, Any]:
    counts = _track_failure_counts(session_id=session_id)
    incidents = _c1_incidents(session_id=session_id)
    recurring = [k for k, v in counts.items() if v >= 2]

    return {
        "report_id": "delivery-failure-intelligence-report",
        "execution_track_1_failures": counts["execution_track_1"],
        "execution_track_2_failures": counts["execution_track_2"],
        "execution_track_3_failures": counts["execution_track_3"],
        "execution_track_4_failures": counts["execution_track_4"],
        "execution_track_5_failures": counts["execution_track_5"],
        "recurring_failure_tracks": recurring,
        "incident_count": len(incidents),
        "failure_detected": any(counts.values()) or bool(incidents),
        "read_only": True,
    }


def analyze_intervention_intelligence(*, session_id: str) -> dict[str, Any]:
    proof_records = _c1_records(session_id=session_id)
    opt_records = _filter_session(list_delivery_optimization_records(), session_id=session_id)
    approvals = [
        r
        for r in proof_records + opt_records
        if str(r.get("kind") or "").endswith("_approve") or "review" in str(r.get("kind") or "")
    ]
    corrections = [r for r in proof_records if "note" in str(r.get("kind") or "")]
    recovery_actions = [r for r in proof_records if str(r.get("kind") or "") == "delivery_proof_executed_note"]

    total_runs = len(_c1_executions(session_id=session_id)) + len(_et5_runs(session_id=session_id))
    approval_frequency = round(len(approvals) / total_runs, 4) if total_runs else 0.0

    return {
        "report_id": "delivery-intervention-report",
        "approval_frequency": approval_frequency,
        "approval_count": len(approvals),
        "manual_correction_count": len(corrections),
        "review_loop_count": len(approvals),
        "recovery_action_count": len(recovery_actions),
        "recurring_interventions": approval_frequency >= 0.5 and total_runs >= 2,
        "read_only": True,
    }


def _estimate_stage_duration(*, execution: dict[str, Any], stage_key: str) -> int:
    total = int(execution.get("duration_ms") or 0)
    path = execution.get("execution_path") or []
    if not path or not total:
        return 0
    stage_count = len(path)
    return int(total / stage_count) if stage_count else 0


def analyze_performance_intelligence(*, session_id: str) -> dict[str, Any]:
    executions = _c1_executions(session_id=session_id)
    if not executions:
        return {
            "report_id": "delivery-performance-report",
            "time_to_workspace_ms": 0,
            "time_to_code_ms": 0,
            "time_to_pr_ms": 0,
            "time_to_deployment_ms": 0,
            "total_cycle_time_ms": 0,
            "run_count": 0,
            "read_only": True,
        }

    workspace_times: list[int] = []
    code_times: list[int] = []
    pr_times: list[int] = []
    deploy_times: list[int] = []
    totals: list[int] = []

    for execution in executions:
        total = int(execution.get("duration_ms") or 0)
        totals.append(total)
        per_stage = _estimate_stage_duration(execution=execution, stage_key="")
        path = execution.get("execution_path") or []
        if "ET1" in path:
            workspace_times.append(per_stage)
        if "ET2" in path:
            code_times.append(per_stage)
        if "ET3" in path:
            pr_times.append(per_stage)
        if "ET4" in path:
            deploy_times.append(per_stage)

    def _avg(values: list[int]) -> float:
        return round(sum(values) / len(values), 1) if values else 0.0

    return {
        "report_id": "delivery-performance-report",
        "time_to_workspace_ms": _avg(workspace_times),
        "time_to_code_ms": _avg(code_times),
        "time_to_pr_ms": _avg(pr_times),
        "time_to_deployment_ms": _avg(deploy_times),
        "total_cycle_time_ms": _avg(totals),
        "run_count": len(executions),
        "delivery_bottleneck": max(
            (
                ("workspace", _avg(workspace_times)),
                ("code", _avg(code_times)),
                ("pr", _avg(pr_times)),
                ("deployment", _avg(deploy_times)),
            ),
            key=lambda item: item[1],
        )[0]
        if totals
        else "",
        "read_only": True,
    }


def analyze_reliability_intelligence(*, session_id: str) -> dict[str, Any]:
    outcomes = _filter_session(list_delivery_outcome_registry_entries(), session_id=session_id)
    if not outcomes:
        sync_delivery_outcomes(session_id=session_id)
        outcomes = _filter_session(list_delivery_outcome_registry_entries(), session_id=session_id)

    total = len(outcomes)
    passed = sum(1 for row in outcomes if row.get("passed") is True)
    failed = total - passed
    recovery = sum(1 for row in outcomes if row.get("recovery_event") is True)

    from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_store import (
        list_delivery_verification_registry_entries,
    )

    verifications = _filter_session(list_delivery_verification_registry_entries(), session_id=session_id)
    verified = sum(1 for row in verifications if row.get("verified") is True)

    return {
        "report_id": "delivery-reliability-intelligence-report",
        "success_rate": round(passed / total, 4) if total else 0.0,
        "failure_rate": round(failed / total, 4) if total else 0.0,
        "recovery_rate": round(recovery / failed, 4) if failed else 1.0 if passed else 0.0,
        "verification_rate": round(verified / len(verifications), 4) if verifications else 0.0,
        "run_count": total,
        "read_only": True,
    }


def _build_opportunities_from_analysis(
    *,
    session_id: str,
    failures: dict[str, Any],
    interventions: dict[str, Any],
    performance: dict[str, Any],
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []

    for track, count in (
        ("execution_track_1", failures.get("execution_track_1_failures", 0)),
        ("execution_track_2", failures.get("execution_track_2_failures", 0)),
        ("execution_track_3", failures.get("execution_track_3_failures", 0)),
        ("execution_track_4", failures.get("execution_track_4_failures", 0)),
        ("execution_track_5", failures.get("execution_track_5_failures", 0)),
    ):
        if count > 0:
            opportunities.append(
                register_improvement_opportunity(
                    entry={
                        "opportunity_id": f"c2-opp-{track}-{uuid4().hex[:6]}",
                        "session_id": session_id,
                        "category": "process_improvement",
                        "title": f"Reduce {track} failures",
                        "description": f"Address {count} observed failure(s) in {track}",
                        "impact": "HIGH" if count >= 2 else "MEDIUM",
                        "effort": "MEDIUM",
                        "confidence": 0.8 if count >= 2 else 0.6,
                        "risk": "LOW",
                        "autonomous_mutation": False,
                    }
                )
            )

    if interventions.get("recurring_interventions"):
        opportunities.append(
            register_improvement_opportunity(
                entry={
                    "opportunity_id": f"c2-opp-intervention-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "category": "workflow_improvement",
                    "title": "Reduce human intervention loops",
                    "description": "High approval frequency suggests workflow friction",
                    "impact": "HIGH",
                    "effort": "MEDIUM",
                    "confidence": 0.7,
                    "risk": "LOW",
                    "autonomous_mutation": False,
                }
            )
        )

    bottleneck = performance.get("delivery_bottleneck")
    if bottleneck:
        category = "provider_improvement" if bottleneck == "deployment" else "tooling_improvement"
        opportunities.append(
            register_improvement_opportunity(
                entry={
                    "opportunity_id": f"c2-opp-bottleneck-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "category": category,
                    "title": f"Optimize {bottleneck} stage cycle time",
                    "description": f"Largest estimated time share in {bottleneck} stage",
                    "impact": "MEDIUM",
                    "effort": "LOW",
                    "confidence": 0.65,
                    "risk": "LOW",
                    "autonomous_mutation": False,
                }
            )
        )

    if not opportunities:
        opportunities.append(
            register_improvement_opportunity(
                entry={
                    "opportunity_id": f"c2-opp-baseline-{uuid4().hex[:6]}",
                    "session_id": session_id,
                    "category": "process_improvement",
                    "title": "Establish delivery optimization baseline",
                    "description": "Run additional WORKSTREAM_C1 proofs to enrich optimization signals",
                    "impact": "MEDIUM",
                    "effort": "LOW",
                    "confidence": 0.9,
                    "risk": "LOW",
                    "autonomous_mutation": False,
                }
            )
        )

    return opportunities


def build_improvement_opportunity_registry(*, session_id: str) -> dict[str, Any]:
    failures = analyze_failure_intelligence(session_id=session_id)
    interventions = analyze_intervention_intelligence(session_id=session_id)
    performance = analyze_performance_intelligence(session_id=session_id)
    opportunities = _build_opportunities_from_analysis(
        session_id=session_id,
        failures=failures,
        interventions=interventions,
        performance=performance,
    )
    stored = _filter_session(list_delivery_improvement_opportunity_registry_entries(), session_id=session_id)

    return {
        "registry_id": "delivery-improvement-opportunity-registry",
        "opportunity_count": len(stored),
        "categories": list(IMPROVEMENT_CATEGORIES),
        "opportunities": stored[-20:],
        "newly_identified": len(opportunities),
        "recommendation_only": True,
        "autonomous_mutation": False,
        "read_only": True,
    }


def build_optimization_priority_matrix(*, session_id: str) -> dict[str, Any]:
    opportunities = _filter_session(list_delivery_improvement_opportunity_registry_entries(), session_id=session_id)
    if not opportunities:
        build_improvement_opportunity_registry(session_id=session_id)
        opportunities = _filter_session(list_delivery_improvement_opportunity_registry_entries(), session_id=session_id)

    impact_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    effort_rank = {"LOW": 3, "MEDIUM": 2, "HIGH": 1}

    ranked: list[dict[str, Any]] = []
    for opp in opportunities:
        impact = str(opp.get("impact") or "MEDIUM")
        effort = str(opp.get("effort") or "MEDIUM")
        confidence = float(opp.get("confidence") or 0.5)
        risk = str(opp.get("risk") or "LOW")
        score = impact_rank.get(impact, 2) * effort_rank.get(effort, 2) * confidence
        ranked.append({**opp, "priority_score": round(score, 3), "rank_factors": {"impact": impact, "effort": effort, "confidence": confidence, "risk": risk}})

    ranked.sort(key=lambda row: row.get("priority_score", 0), reverse=True)

    return {
        "matrix_id": "delivery-optimization-priority-matrix",
        "ranked_opportunities": ranked[:10],
        "human_adoption_required": True,
        "autonomous_mutation": False,
        "read_only": True,
    }


def compute_optimization_trends(*, session_id: str) -> dict[str, Any]:
    reliability = analyze_reliability_intelligence(session_id=session_id)
    performance = analyze_performance_intelligence(session_id=session_id)
    interventions = analyze_intervention_intelligence(session_id=session_id)

    return {
        "deployment_success_trend": reliability.get("success_rate", 0.0),
        "intervention_reduction_trend": round(1.0 - interventions.get("approval_frequency", 0.0), 4),
        "delivery_cycle_time_trend": performance.get("total_cycle_time_ms", 0.0),
        "recovery_trend": reliability.get("recovery_rate", 0.0),
        "verification_trend": reliability.get("verification_rate", 0.0),
        "read_only": True,
    }


def run_delivery_optimization_analysis(*, session_id: str) -> dict[str, Any]:
    sync_delivery_outcomes(session_id=session_id)
    failures = analyze_failure_intelligence(session_id=session_id)
    interventions = analyze_intervention_intelligence(session_id=session_id)
    performance = analyze_performance_intelligence(session_id=session_id)
    reliability = analyze_reliability_intelligence(session_id=session_id)
    opportunities = build_improvement_opportunity_registry(session_id=session_id)
    matrix = build_optimization_priority_matrix(session_id=session_id)
    trends = compute_optimization_trends(session_id=session_id)

    return {
        "ok": True,
        "session_id": session_id,
        "failure_intelligence": failures,
        "intervention_intelligence": interventions,
        "performance_intelligence": performance,
        "reliability_intelligence": reliability,
        "improvement_opportunities": opportunities,
        "priority_matrix": matrix,
        "trends": trends,
        "autonomous_mutation_performed": False,
        "detail": "Delivery optimization analysis complete — recommendations require human review",
    }
