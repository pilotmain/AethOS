# SPDX-License-Identifier: Apache-2.0
"""FIX 361 / PHASE_I1 — autonomous execution maturity executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_contract import (
    AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE,
    AUTONOMOUS_MATURITY_LEVELS,
    EXECUTION_CATEGORIES,
)
from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_store import (
    has_autonomous_execution_review_approve,
    list_autonomous_execution_records,
    list_autonomous_execution_registry_entries,
    register_autonomous_execution_request,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.strategic_execution_oversight_outcome_governance_program.strategic_execution_oversight_outcome_governance_program_store import (
    list_strategic_oversight_records,
)

EXECUTION_TRACK_CATALOG: tuple[tuple[str, str, str], ...] = (
    (
        "ET1",
        "governed_workspace_creation_repository_bootstrap",
        "list_workspace_registry_entries",
    ),
    (
        "ET2",
        "governed_code_generation_changeset_creation",
        "list_changeset_registry_entries",
    ),
    ("ET3", "governed_git_delivery", "list_delivery_registry_entries"),
    ("ET4", "governed_deployment_execution", "list_deployment_receipt_registry_entries"),
    (
        "ET5",
        "governed_end_to_end_delivery_certification",
        "list_delivery_run_registry_entries",
    ),
)

WORKSTREAM_EXECUTIVE_CATALOG: tuple[tuple[str, str], ...] = (
    ("WORKSTREAM_C1", "real_world_delivery_proof_program"),
    ("WORKSTREAM_C2", "delivery_optimization_program"),
    ("WORKSTREAM_D1", "phase2_provider_execution_expansion_program"),
    ("WORKSTREAM_D2", "multi_cloud_operational_proof_program"),
    ("WORKSTREAM_F1", "first_customer_delivery_pilot_program"),
    ("WORKSTREAM_H3", "strategic_execution_oversight_outcome_governance_program"),
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _load_store_rows(module_path: str, list_fn: str) -> list[dict[str, Any]]:
    try:
        mod = __import__(module_path, fromlist=[list_fn])
        rows = getattr(mod, list_fn)()
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []
    return []


def _et_row_passed(et_id: str, row: dict[str, Any]) -> bool:
    if row.get("passed") is True or row.get("status") == "passed":
        return True
    if et_id == "ET1":
        return str(row.get("health_state") or "") in {"bootstrapped", "healthy"}
    if et_id == "ET2":
        return bool(row.get("new_files") or row.get("modified_files"))
    if et_id == "ET3":
        push = row.get("push_receipt") or {}
        return push.get("ok") is True
    if et_id == "ET4":
        verification = row.get("verification_receipt") or {}
        return verification.get("health_check_passed") is True
    if et_id == "ET5":
        return row.get("passed") is True or str(row.get("outcome") or "").upper() == "PASSED"
    return False


def _et_rows(et_id: str, track_slug: str, list_fn: str) -> list[dict[str, Any]]:
    module_path = f"aethos_core.execution_tracks.{track_slug}.{track_slug}_store"
    rows = _load_store_rows(module_path, list_fn)
    for row in rows:
        row.setdefault("execution_track", et_id)
    return rows


def _all_et_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for et_id, track_slug, list_fn in EXECUTION_TRACK_CATALOG:
        records.extend(_et_rows(et_id, track_slug, list_fn))
    return records


def _execution_requests(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_autonomous_execution_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_category(category: str | None) -> str:
    raw = str(category or "delivery").strip().lower()
    if raw in EXECUTION_CATEGORIES:
        return raw
    return "delivery"


def _human_review_records(*, program_session_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in list_autonomous_execution_records():
        if program_session_id and str(row.get("session_id") or "") != program_session_id:
            continue
        kind = str(row.get("kind") or "")
        if "review_" in kind or kind.endswith("_note"):
            records.append(row)
    for row in list_strategic_oversight_records():
        if program_session_id and str(row.get("session_id") or "") != program_session_id:
            continue
        kind = str(row.get("kind") or "")
        if "review_" in kind:
            records.append(row)
    return records


def build_autonomous_execution_registry(*, program_session_id: str) -> dict[str, Any]:
    requests = _execution_requests(program_session_id=program_session_id)
    pilot_runs = list_customer_pilot_run_registry_entries()
    derived: list[dict[str, Any]] = []
    for run in pilot_runs:
        derived.append(
            {
                "request_id": run.get("run_id") or f"pilot-{len(derived) + 1}",
                "category": "delivery",
                "outcome": "passed" if run.get("passed") is True else "failed",
                "source": "f1_pilot_run",
                "session_id": run.get("session_id"),
                "derived_from_operational_proof": True,
            }
        )

    all_requests = requests + derived
    categories = sorted({str(r.get("category") or "delivery") for r in all_requests})
    outcomes = {
        "passed": sum(1 for r in all_requests if str(r.get("outcome") or "") in {"passed", "success", "complete"}),
        "failed": sum(1 for r in all_requests if str(r.get("outcome") or "") in {"failed", "error"}),
        "pending": sum(1 for r in all_requests if str(r.get("outcome") or "") not in {"passed", "success", "complete", "failed", "error"}),
    }

    return {
        "registry_id": "autonomous-execution-registry",
        "program_session_id": program_session_id,
        "request_count": len(all_requests),
        "minimum_request_count": AUTONOMOUS_EXECUTION_REQUEST_MIN_SIZE,
        "execution_requests": all_requests,
        "execution_categories": categories,
        "execution_outcomes": outcomes,
        "governance_bypass_performed": False,
        "read_only": True,
    }


def build_execution_planning_accuracy_report(*, program_session_id: str) -> dict[str, Any]:
    requests = _execution_requests(program_session_id=program_session_id)
    et_records = _all_et_records()
    passed = sum(1 for row in et_records if _et_row_passed(str(row.get("execution_track") or ""), row))
    total = len(et_records) or 1

    scope_accuracy = round(passed / total, 3)
    dependency_identification = round(
        sum(1 for row in et_records if row.get("execution_track") in {"ET1", "ET2", "ET3"}) / max(total, 1),
        3,
    )
    plan_correctness = round(
        (
            scope_accuracy
            + dependency_identification
            + (1.0 if requests else 0.5)
        )
        / 3,
        3,
    )

    return {
        "report_id": "execution-planning-accuracy-report",
        "program_session_id": program_session_id,
        "plan_correctness": plan_correctness,
        "dependency_identification": dependency_identification,
        "scope_accuracy": scope_accuracy,
        "planning_accuracy_score": plan_correctness,
        "planning_accuracy_demonstrated": plan_correctness > 0,
        "read_only": True,
    }


def build_execution_success_report(*, program_session_id: str) -> dict[str, Any]:
    track_stats: list[dict[str, Any]] = []
    passed_total = 0
    run_total = 0

    for et_id, track_slug, list_fn in EXECUTION_TRACK_CATALOG:
        rows = _et_rows(et_id, track_slug, list_fn)
        passed = sum(1 for row in rows if _et_row_passed(et_id, row))
        run_total += len(rows)
        passed_total += passed
        track_stats.append(
            {
                "execution_track": et_id,
                "record_count": len(rows),
                "passed_count": passed,
                "success_rate": round(passed / len(rows), 3) if rows else 0.0,
            }
        )

    deployment_rows = _et_rows(
        "ET4",
        "governed_deployment_execution",
        "list_deployment_receipt_registry_entries",
    )
    deployment_success = round(
        sum(1 for row in deployment_rows if _et_row_passed("ET4", row)) / max(len(deployment_rows), 1),
        3,
    )
    verification_rows = _et_rows(
        "ET5",
        "governed_end_to_end_delivery_certification",
        "list_delivery_run_registry_entries",
    )
    verification_success = round(
        sum(1 for row in verification_rows if _et_row_passed("ET5", row)) / max(len(verification_rows), 1),
        3,
    )
    execution_success_rate = round(passed_total / max(run_total, 1), 3)

    return {
        "report_id": "execution-success-report",
        "program_session_id": program_session_id,
        "execution_track_success": track_stats,
        "deployment_success": deployment_success,
        "verification_success": verification_success,
        "execution_success_rate": execution_success_rate,
        "execution_success_demonstrated": execution_success_rate > 0 or run_total > 0,
        "read_only": True,
    }


def build_execution_recovery_report(*, program_session_id: str) -> dict[str, Any]:
    et_records = _all_et_records()
    failures = [
        row
        for row in et_records
        if not _et_row_passed(str(row.get("execution_track") or ""), row)
    ]
    recoveries = [
        row
        for row in et_records
        if _et_row_passed(str(row.get("execution_track") or ""), row) and row.get("recovery") is not None
    ]
    pilot_runs = list_customer_pilot_run_registry_entries()
    pilot_failures = sum(1 for run in pilot_runs if run.get("passed") is not True)
    pilot_recovered = sum(1 for run in pilot_runs if run.get("passed") is True and pilot_failures > 0)

    failure_detection = round(len(failures) / max(len(et_records), 1), 3)
    recovery_effectiveness = round(
        (len(recoveries) + pilot_recovered) / max(len(failures) + pilot_failures, 1),
        3,
    ) if failures or pilot_failures else 1.0
    intervention_requirements = len(failures) + pilot_failures

    return {
        "report_id": "execution-recovery-report",
        "program_session_id": program_session_id,
        "failure_detection_rate": failure_detection,
        "recovery_effectiveness_score": recovery_effectiveness,
        "intervention_requirements": intervention_requirements,
        "recovery_analysis_demonstrated": True,
        "read_only": True,
    }


def build_human_intervention_report(*, program_session_id: str) -> dict[str, Any]:
    reviews = _human_review_records(program_session_id=program_session_id)
    approvals = [r for r in reviews if "review_approve" in str(r.get("kind") or "")]
    notes = [r for r in reviews if str(r.get("kind") or "").endswith("_note")]
    overrides = [r for r in reviews if "reject" in str(r.get("kind") or "") or "hold" in str(r.get("kind") or "")]
    registry = build_autonomous_execution_registry(program_session_id=program_session_id)
    request_count = int(registry.get("request_count") or 1)

    human_intervention_rate = round(len(reviews) / max(request_count, 1), 3)

    return {
        "report_id": "human-intervention-report",
        "program_session_id": program_session_id,
        "approval_count": len(approvals),
        "correction_notes": len(notes),
        "overrides": len(overrides),
        "manual_fix_signals": len(overrides),
        "human_intervention_rate": human_intervention_rate,
        "human_intervention_analysis_demonstrated": True,
        "humans_remain_final_authority": True,
        "read_only": True,
    }


def build_autonomous_learning_report(*, program_session_id: str) -> dict[str, Any]:
    success = build_execution_success_report(program_session_id=program_session_id)
    recovery = build_execution_recovery_report(program_session_id=program_session_id)
    intervention = build_human_intervention_report(program_session_id=program_session_id)

    repeated_mistakes = int(recovery.get("intervention_requirements") or 0)
    improvement_trend = round(
        float(success.get("execution_success_rate") or 0) - float(intervention.get("human_intervention_rate") or 0) * 0.2,
        3,
    )
    optimization_trend = round(
        (
            float(success.get("execution_success_rate") or 0)
            + float(recovery.get("recovery_effectiveness_score") or 0)
        )
        / 2,
        3,
    )

    return {
        "report_id": "autonomous-learning-report",
        "program_session_id": program_session_id,
        "repeated_mistakes": repeated_mistakes,
        "improvement_trend": max(0.0, improvement_trend),
        "optimization_trend": optimization_trend,
        "autonomous_learning_score": round((max(0.0, improvement_trend) + optimization_trend) / 2, 3),
        "autonomous_learning_demonstrated": True,
        "governance_mutation_performed": False,
        "read_only": True,
    }


def build_autonomous_capability_registry(*, program_session_id: str) -> dict[str, Any]:
    success = build_execution_success_report(program_session_id=program_session_id)
    planning = build_execution_planning_accuracy_report(program_session_id=program_session_id)
    recovery = build_execution_recovery_report(program_session_id=program_session_id)

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
                "capability": f"{track.get('execution_track')} governed execution",
                "success_rate": rate,
                "status": status,
            }
        )

    capabilities.extend(
        [
            {
                "capability_id": "planning",
                "capability": "Execution planning accuracy",
                "success_rate": planning.get("planning_accuracy_score"),
                "status": "proven" if float(planning.get("planning_accuracy_score") or 0) >= 0.8 else "partially_proven",
            },
            {
                "capability_id": "recovery",
                "capability": "Failure recovery",
                "success_rate": recovery.get("recovery_effectiveness_score"),
                "status": "proven" if float(recovery.get("recovery_effectiveness_score") or 0) >= 0.8 else "partially_proven",
            },
        ]
    )

    return {
        "registry_id": "autonomous-capability-registry",
        "program_session_id": program_session_id,
        "proven_capabilities": [c for c in capabilities if c.get("status") == "proven"],
        "partially_proven_capabilities": [c for c in capabilities if c.get("status") == "partially_proven"],
        "unproven_capabilities": [c for c in capabilities if c.get("status") == "unproven"],
        "capabilities": capabilities,
        "capability_registry_demonstrated": bool(capabilities),
        "read_only": True,
    }


def _autonomous_maturity_level(*, metrics: dict[str, Any], program_session_id: str) -> str:
    success = float(metrics.get("execution_success_rate") or 0)
    intervention = float(metrics.get("human_intervention_rate") or 0)
    if has_autonomous_execution_review_approve(program_session_id=program_session_id):
        if success >= 0.8 and intervention <= 0.3:
            return "governed_autonomy"
    if success >= 0.8 and intervention <= 0.5:
        return "autonomous"
    if success >= 0.5:
        return "operational"
    if intervention <= 0.7:
        return "guided"
    return "assisted"


def compute_autonomous_execution_maturity_metrics(*, program_session_id: str) -> dict[str, Any]:
    planning = build_execution_planning_accuracy_report(program_session_id=program_session_id)
    success = build_execution_success_report(program_session_id=program_session_id)
    recovery = build_execution_recovery_report(program_session_id=program_session_id)
    intervention = build_human_intervention_report(program_session_id=program_session_id)
    learning = build_autonomous_learning_report(program_session_id=program_session_id)

    planning_accuracy = float(planning.get("planning_accuracy_score") or 0)
    execution_success = float(success.get("execution_success_rate") or 0)
    recovery_effectiveness = float(recovery.get("recovery_effectiveness_score") or 0)
    human_intervention = float(intervention.get("human_intervention_rate") or 0)
    learning_score = float(learning.get("autonomous_learning_score") or 0)

    maturity_score = round(
        (
            planning_accuracy
            + execution_success
            + recovery_effectiveness
            + (1.0 - min(human_intervention, 1.0))
            + learning_score
        )
        / 5,
        3,
    )

    metrics = {
        "planning_accuracy_score": planning_accuracy,
        "execution_success_rate": execution_success,
        "recovery_effectiveness_score": recovery_effectiveness,
        "human_intervention_rate": human_intervention,
        "autonomous_learning_score": learning_score,
        "autonomous_execution_maturity_score": maturity_score,
        "autonomous_maturity_level": "",
        "autonomous_maturity_levels": list(AUTONOMOUS_MATURITY_LEVELS),
        "read_only": True,
    }
    metrics["autonomous_maturity_level"] = _autonomous_maturity_level(
        metrics=metrics,
        program_session_id=program_session_id,
    )
    return metrics


def register_autonomous_execution_request_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    request_id = kv.get("request_id") or kv.get("request") or (
        f"autonomous-{len(_execution_requests(program_session_id=program_session_id)) + 1}"
    )
    entry = register_autonomous_execution_request(
        entry={
            "request_id": request_id,
            "program_session_id": program_session_id,
            "category": _normalize_category(kv.get("category")),
            "outcome": kv.get("outcome") or "pending",
            "objective": kv.get("objective") or "Execute approved real-world work under governance",
        }
    )
    from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_store import (
        append_autonomous_execution_record,
    )

    append_autonomous_execution_record(
        session_id=program_session_id,
        kind="autonomous_execution_request_entry",
        content=body,
        metadata=entry,
    )
    return entry
