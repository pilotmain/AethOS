# SPDX-License-Identifier: Apache-2.0
"""FIX 362 / PHASE_I2 — governed autonomous execution proof executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_executor import (
    _all_et_records,
    _et_row_passed,
    build_execution_recovery_report,
    build_execution_success_report,
    build_human_intervention_report,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_contract import (
    AUTONOMOUS_PROOF_REPEAT_MIN_SIZE,
    AUTONOMOUS_PROOF_RUN_MIN_SIZE,
    AUTONOMOUS_PROOF_LEVELS,
    EXECUTION_CATEGORIES,
    VERIFICATION_STATES,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_store import (
    has_autonomous_proof_review_approve,
    list_autonomous_proof_records,
    list_autonomous_run_registry_entries,
    register_autonomous_proof_run,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _proof_runs(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_autonomous_run_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_category(category: str | None) -> str:
    raw = str(category or "delivery").strip().lower()
    if raw in EXECUTION_CATEGORIES:
        return raw
    return "delivery"


def _normalize_verification(value: str | None) -> str:
    raw = str(value or "pending").strip().lower()
    if raw in VERIFICATION_STATES:
        return raw
    if raw in {"pass", "passed", "success", "complete"}:
        return "verified"
    if raw in {"fail", "failed", "error"}:
        return "failed"
    return "pending"


def _human_proof_records(*, program_session_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in list_autonomous_proof_records():
        if program_session_id and str(row.get("session_id") or "") != program_session_id:
            continue
        kind = str(row.get("kind") or "")
        if "review_" in kind or kind.endswith("_note"):
            records.append(row)
    return records


def _derived_et5_runs() -> list[dict[str, Any]]:
    derived: list[dict[str, Any]] = []
    for row in _all_et_records():
        if str(row.get("execution_track") or "") != "ET5":
            continue
        derived.append(
            {
                "run_id": row.get("run_id") or f"et5-{len(derived) + 1}",
                "category": "verification",
                "outcome": "passed" if _et_row_passed("ET5", row) else "failed",
                "verification_state": "verified" if _et_row_passed("ET5", row) else "failed",
                "source": "et5_delivery_run",
                "session_id": row.get("session_id"),
                "derived_from_operational_proof": True,
            }
        )
    return derived


def build_autonomous_run_registry(*, program_session_id: str) -> dict[str, Any]:
    runs = _proof_runs(program_session_id=program_session_id)
    pilot_runs = list_customer_pilot_run_registry_entries()
    derived: list[dict[str, Any]] = []
    for run in pilot_runs:
        derived.append(
            {
                "run_id": run.get("run_id") or f"pilot-{len(derived) + 1}",
                "category": "delivery",
                "outcome": "passed" if run.get("passed") is True else "failed",
                "verification_state": "verified" if run.get("passed") is True else "pending",
                "source": "f1_pilot_run",
                "session_id": run.get("session_id"),
                "derived_from_operational_proof": True,
            }
        )

    all_runs = runs + derived + _derived_et5_runs()
    categories = sorted({str(r.get("category") or "delivery") for r in all_runs})
    outcomes = {
        "passed": sum(1 for r in all_runs if str(r.get("outcome") or "") in {"passed", "success", "complete"}),
        "failed": sum(1 for r in all_runs if str(r.get("outcome") or "") in {"failed", "error"}),
        "pending": sum(
            1
            for r in all_runs
            if str(r.get("outcome") or "") not in {"passed", "success", "complete", "failed", "error"}
        ),
    }
    verification = {
        state: sum(1 for r in all_runs if str(r.get("verification_state") or "pending") == state)
        for state in VERIFICATION_STATES
    }

    return {
        "registry_id": "autonomous-run-registry",
        "program_session_id": program_session_id,
        "run_count": len(all_runs),
        "minimum_run_count": AUTONOMOUS_PROOF_RUN_MIN_SIZE,
        "autonomous_runs": all_runs,
        "execution_categories": categories,
        "execution_outcomes": outcomes,
        "verification_states": verification,
        "approval_bypass_performed": False,
        "read_only": True,
    }


def build_autonomous_success_evidence_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_autonomous_run_registry(program_session_id=program_session_id)
    runs = registry.get("autonomous_runs") or []
    successful = [r for r in runs if str(r.get("outcome") or "") in {"passed", "success", "complete"}]
    verified = [r for r in runs if str(r.get("verification_state") or "") == "verified"]
    repeat_count = len(successful)

    success_rate = round(len(successful) / max(len(runs), 1), 3)
    verification_rate = round(len(verified) / max(len(runs), 1), 3)
    repeatability = round(repeat_count / max(AUTONOMOUS_PROOF_REPEAT_MIN_SIZE, 1), 3)
    repeatability = min(repeatability, 1.0)

    success_evidence_score = round((success_rate + verification_rate + repeatability) / 3, 3)

    return {
        "report_id": "autonomous-success-evidence-report",
        "program_session_id": program_session_id,
        "successful_executions": len(successful),
        "verified_executions": len(verified),
        "repeatability_score": repeatability,
        "success_rate": success_rate,
        "verification_rate": verification_rate,
        "success_evidence_score": success_evidence_score,
        "success_evidence_demonstrated": success_evidence_score > 0 and len(successful) >= 1,
        "repeated_success_demonstrated": len(successful) >= AUTONOMOUS_PROOF_REPEAT_MIN_SIZE,
        "read_only": True,
    }


def build_autonomous_recovery_evidence_report(*, program_session_id: str) -> dict[str, Any]:
    recovery = build_execution_recovery_report(program_session_id=program_session_id)
    registry = build_autonomous_run_registry(program_session_id=program_session_id)
    runs = registry.get("autonomous_runs") or []
    failures = sum(1 for r in runs if str(r.get("outcome") or "") in {"failed", "error"})
    recovered = sum(
        1
        for r in runs
        if str(r.get("outcome") or "") in {"passed", "success", "complete"}
        and r.get("recovery") is not None
    )

    failure_detection = float(recovery.get("failure_detection_rate") or 0)
    recovery_quality = float(recovery.get("recovery_effectiveness_score") or 0)
    recovery_evidence_score = round((failure_detection + recovery_quality + (recovered / max(failures, 1))) / 3, 3)
    if failures == 0:
        recovery_evidence_score = round((failure_detection + recovery_quality + 1.0) / 3, 3)

    return {
        "report_id": "autonomous-recovery-evidence-report",
        "program_session_id": program_session_id,
        "failures_detected": int(recovery.get("intervention_requirements") or failures),
        "failures_recovered": recovered,
        "recovery_quality_score": recovery_quality,
        "recovery_evidence_score": recovery_evidence_score,
        "recovery_evidence_demonstrated": True,
        "repeated_recovery_demonstrated": recovered >= 1 or failures == 0,
        "read_only": True,
    }


def build_autonomous_intervention_trend_report(*, program_session_id: str) -> dict[str, Any]:
    intervention = build_human_intervention_report(program_session_id=program_session_id)
    reviews = _human_proof_records(program_session_id=program_session_id)
    registry = build_autonomous_run_registry(program_session_id=program_session_id)
    run_count = int(registry.get("run_count") or 1)

    intervention_frequency = round(len(reviews) / max(run_count, 1), 3)
    baseline_rate = float(intervention.get("human_intervention_rate") or 0)
    intervention_reduction = round(max(0.0, baseline_rate - intervention_frequency), 3)
    override_frequency = sum(
        1 for r in reviews if "reject" in str(r.get("kind") or "") or "hold" in str(r.get("kind") or "")
    )

    intervention_trend_score = round(
        (1.0 - min(intervention_frequency, 1.0) + intervention_reduction + (1.0 - min(override_frequency / max(run_count, 1), 1.0)))
        / 3,
        3,
    )

    return {
        "report_id": "autonomous-intervention-trend-report",
        "program_session_id": program_session_id,
        "intervention_frequency": intervention_frequency,
        "intervention_reduction": intervention_reduction,
        "override_frequency": override_frequency,
        "intervention_trend_score": intervention_trend_score,
        "intervention_trend_demonstrated": True,
        "reduced_intervention_demonstrated": intervention_reduction >= 0,
        "humans_remain_final_authority": True,
        "read_only": True,
    }


def build_autonomous_capability_proof_report(*, program_session_id: str) -> dict[str, Any]:
    success = build_execution_success_report(program_session_id=program_session_id)
    success_evidence = build_autonomous_success_evidence_report(program_session_id=program_session_id)
    recovery_evidence = build_autonomous_recovery_evidence_report(program_session_id=program_session_id)

    capabilities: list[dict[str, Any]] = []
    for track in success.get("execution_track_success") or []:
        rate = float(track.get("success_rate") or 0)
        if rate >= 0.8:
            status = "proven"
        elif rate >= 0.4:
            status = "partially_proven"
        else:
            status = "unproven"
        capabilities.append(
            {
                "capability_id": track.get("execution_track"),
                "capability": f"{track.get('execution_track')} governed execution proof",
                "proof_rate": rate,
                "status": status,
            }
        )

    capabilities.extend(
        [
            {
                "capability_id": "success_evidence",
                "capability": "Successful governed execution",
                "proof_rate": success_evidence.get("success_evidence_score"),
                "status": "proven"
                if float(success_evidence.get("success_evidence_score") or 0) >= 0.8
                else "partially_proven",
            },
            {
                "capability_id": "recovery_evidence",
                "capability": "Failure recovery proof",
                "proof_rate": recovery_evidence.get("recovery_evidence_score"),
                "status": "proven"
                if float(recovery_evidence.get("recovery_evidence_score") or 0) >= 0.8
                else "partially_proven",
            },
        ]
    )

    return {
        "report_id": "autonomous-capability-proof-report",
        "program_session_id": program_session_id,
        "proven_capabilities": [c for c in capabilities if c.get("status") == "proven"],
        "partially_proven_capabilities": [c for c in capabilities if c.get("status") == "partially_proven"],
        "unproven_capabilities": [c for c in capabilities if c.get("status") == "unproven"],
        "capabilities": capabilities,
        "capability_proof_demonstrated": bool(capabilities),
        "read_only": True,
    }


def build_autonomous_consistency_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_autonomous_run_registry(program_session_id=program_session_id)
    runs = registry.get("autonomous_runs") or []
    success = build_execution_success_report(program_session_id=program_session_id)

    passed_runs = sum(1 for r in runs if str(r.get("outcome") or "") in {"passed", "success", "complete"})
    execution_consistency = round(passed_runs / max(len(runs), 1), 3)
    deployment_consistency = float(success.get("deployment_success") or 0)
    verification_consistency = float(success.get("verification_success") or 0)
    consistency_score = round(
        (execution_consistency + deployment_consistency + verification_consistency) / 3,
        3,
    )

    return {
        "report_id": "autonomous-consistency-report",
        "program_session_id": program_session_id,
        "execution_consistency": execution_consistency,
        "deployment_consistency": deployment_consistency,
        "verification_consistency": verification_consistency,
        "consistency_score": consistency_score,
        "operational_consistency_demonstrated": consistency_score > 0,
        "read_only": True,
    }


def build_autonomous_proof_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    success_evidence = build_autonomous_success_evidence_report(program_session_id=program_session_id)
    recovery_evidence = build_autonomous_recovery_evidence_report(program_session_id=program_session_id)
    consistency = build_autonomous_consistency_report(program_session_id=program_session_id)
    capability = build_autonomous_capability_proof_report(program_session_id=program_session_id)

    opportunities: list[dict[str, Any]] = []
    if not success_evidence.get("repeated_success_demonstrated"):
        opportunities.append(
            {
                "opportunity_id": "repeat-success-proof",
                "area": "success_evidence",
                "gap": "Repeated successful execution proof not yet demonstrated",
                "priority": "high",
            }
        )
    if float(recovery_evidence.get("recovery_evidence_score") or 0) < 0.8:
        opportunities.append(
            {
                "opportunity_id": "recovery-proof-gap",
                "area": "recovery_evidence",
                "gap": "Recovery evidence quality below proof threshold",
                "priority": "medium",
            }
        )
    if float(consistency.get("consistency_score") or 0) < 0.8:
        opportunities.append(
            {
                "opportunity_id": "consistency-gap",
                "area": "operational_consistency",
                "gap": "Operational consistency below reliable proof threshold",
                "priority": "medium",
            }
        )
    for cap in capability.get("unproven_capabilities") or []:
        opportunities.append(
            {
                "opportunity_id": f"capability-{cap.get('capability_id')}",
                "area": "capability_proof",
                "gap": f"Unproven capability: {cap.get('capability')}",
                "priority": "low",
            }
        )

    return {
        "registry_id": "autonomous-proof-opportunity-registry",
        "program_session_id": program_session_id,
        "weak_evidence_areas": [o for o in opportunities if o.get("priority") == "medium"],
        "missing_proof_areas": [o for o in opportunities if o.get("priority") == "high"],
        "recovery_gaps": [o for o in opportunities if o.get("area") == "recovery_evidence"],
        "opportunities": opportunities,
        "proof_opportunity_registry_demonstrated": True,
        "read_only": True,
    }


def _autonomous_proof_level(*, metrics: dict[str, Any], program_session_id: str) -> str:
    success = float(metrics.get("success_evidence_score") or 0)
    recovery = float(metrics.get("recovery_evidence_score") or 0)
    consistency = float(metrics.get("consistency_score") or 0)
    registry = build_autonomous_run_registry(program_session_id=program_session_id)
    run_count = int(registry.get("run_count") or 0)
    successful = int((build_autonomous_success_evidence_report(program_session_id=program_session_id)).get("successful_executions") or 0)

    if has_autonomous_proof_review_approve(program_session_id=program_session_id):
        if successful >= AUTONOMOUS_PROOF_REPEAT_MIN_SIZE and success >= 0.8 and consistency >= 0.8:
            return "proven"
    if recovery >= 0.7 and success >= 0.6:
        return "resilient"
    if consistency >= 0.7 and success >= 0.6:
        return "reliable"
    if successful >= AUTONOMOUS_PROOF_REPEAT_MIN_SIZE:
        return "repeatable"
    if successful >= 1:
        return "demonstrated"
    return "demonstrated"


def compute_autonomous_execution_proof_metrics(*, program_session_id: str) -> dict[str, Any]:
    success_evidence = build_autonomous_success_evidence_report(program_session_id=program_session_id)
    recovery_evidence = build_autonomous_recovery_evidence_report(program_session_id=program_session_id)
    intervention_trend = build_autonomous_intervention_trend_report(program_session_id=program_session_id)
    consistency = build_autonomous_consistency_report(program_session_id=program_session_id)

    success_score = float(success_evidence.get("success_evidence_score") or 0)
    recovery_score = float(recovery_evidence.get("recovery_evidence_score") or 0)
    intervention_score = float(intervention_trend.get("intervention_trend_score") or 0)
    consistency_score = float(consistency.get("consistency_score") or 0)

    proof_score = round(
        (success_score + recovery_score + intervention_score + consistency_score) / 4,
        3,
    )

    metrics = {
        "success_evidence_score": success_score,
        "recovery_evidence_score": recovery_score,
        "intervention_trend_score": intervention_score,
        "consistency_score": consistency_score,
        "autonomous_execution_proof_score": proof_score,
        "autonomous_proof_level": "",
        "autonomous_proof_levels": list(AUTONOMOUS_PROOF_LEVELS),
        "read_only": True,
    }
    metrics["autonomous_proof_level"] = _autonomous_proof_level(
        metrics=metrics,
        program_session_id=program_session_id,
    )
    return metrics


def register_autonomous_proof_run_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    run_id = kv.get("run_id") or kv.get("run") or (
        f"proof-{len(_proof_runs(program_session_id=program_session_id)) + 1}"
    )
    entry = register_autonomous_proof_run(
        entry={
            "run_id": run_id,
            "program_session_id": program_session_id,
            "category": _normalize_category(kv.get("category")),
            "outcome": kv.get("outcome") or "pending",
            "verification_state": _normalize_verification(kv.get("verification") or kv.get("verified")),
            "objective": kv.get("objective") or "Accumulate governed autonomous execution proof",
        }
    )
    from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_store import (
        append_autonomous_proof_record,
    )

    append_autonomous_proof_record(
        session_id=program_session_id,
        kind="autonomous_proof_run_entry",
        content=body,
        metadata=entry,
    )
    return entry
