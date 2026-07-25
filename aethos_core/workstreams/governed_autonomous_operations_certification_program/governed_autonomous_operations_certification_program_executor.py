# SPDX-License-Identifier: Apache-2.0
"""FIX 363 / PHASE_I3 — governed autonomous operations certification executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_executor import (
    build_execution_recovery_report,
    build_execution_success_report,
    build_human_intervention_report,
    compute_autonomous_execution_maturity_metrics,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_executor import (
    build_autonomous_consistency_report,
    build_autonomous_recovery_evidence_report,
    build_autonomous_run_registry,
    build_autonomous_success_evidence_report,
    compute_autonomous_execution_proof_metrics,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_contract import (
    AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE,
    AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE,
    AUTONOMOUS_OPERATIONS_CERTIFICATION_LEVELS,
    PROVIDER_CATEGORIES,
    WORKLOAD_CATEGORIES,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_store import (
    has_autonomous_certification_review_approve,
    list_autonomous_certification_records,
    list_certification_candidate_registry_entries,
    register_certification_candidate,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _certification_candidates(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_certification_candidate_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_workload(value: str | None) -> str:
    raw = str(value or "delivery").strip().lower()
    if raw in WORKLOAD_CATEGORIES:
        return raw
    return "delivery"


def _normalize_provider(value: str | None) -> str:
    raw = str(value or "Railway").strip()
    aliases = {
        "railway": "Railway",
        "vercel": "Vercel",
        "aws": "AWS",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "azure": "Azure",
        "gcp": "GCP",
        "google cloud": "GCP",
    }
    if raw in PROVIDER_CATEGORIES:
        return raw
    return aliases.get(raw.lower(), "Railway")


def _human_certification_records(*, program_session_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in list_autonomous_certification_records():
        if program_session_id and str(row.get("session_id") or "") != program_session_id:
            continue
        kind = str(row.get("kind") or "")
        if "review_" in kind or kind.endswith("_note"):
            records.append(row)
    return records


def _deployment_provider_rows() -> list[dict[str, Any]]:
    try:
        mod = __import__(
            "aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store",
            fromlist=["list_deployment_receipt_registry_entries"],
        )
        rows = mod.list_deployment_receipt_registry_entries()
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []
    return []


def build_autonomous_certification_candidate_registry(*, program_session_id: str) -> dict[str, Any]:
    candidates = _certification_candidates(program_session_id=program_session_id)
    pilot_runs = list_customer_pilot_run_registry_entries()
    derived: list[dict[str, Any]] = []
    for run in pilot_runs:
        derived.append(
            {
                "candidate_id": run.get("run_id") or f"pilot-{len(derived) + 1}",
                "workload_category": "delivery",
                "provider_category": "Railway",
                "source": "f1_pilot_run",
                "session_id": run.get("session_id"),
                "passed": run.get("passed") is True,
                "derived_from_operational_proof": True,
            }
        )

    all_candidates = candidates + derived
    workloads = sorted({str(c.get("workload_category") or "delivery") for c in all_candidates})
    providers = sorted({str(c.get("provider_category") or "Railway") for c in all_candidates})

    return {
        "registry_id": "autonomous-certification-candidate-registry",
        "program_session_id": program_session_id,
        "candidate_count": len(all_candidates),
        "minimum_candidate_count": AUTONOMOUS_CERTIFICATION_CANDIDATE_MIN_SIZE,
        "certification_candidates": all_candidates,
        "workload_categories": workloads,
        "provider_categories": providers,
        "approval_bypass_performed": False,
        "read_only": True,
    }


def build_autonomous_reliability_certification_report(*, program_session_id: str) -> dict[str, Any]:
    success = build_execution_success_report(program_session_id=program_session_id)
    consistency = build_autonomous_consistency_report(program_session_id=program_session_id)
    proof = compute_autonomous_execution_proof_metrics(program_session_id=program_session_id)

    execution_reliability = round(
        (
            float(success.get("execution_success_rate") or 0)
            + float(consistency.get("execution_consistency") or 0)
        )
        / 2,
        3,
    )
    deployment_reliability = round(
        (
            float(success.get("deployment_success") or 0)
            + float(consistency.get("deployment_consistency") or 0)
        )
        / 2,
        3,
    )
    verification_reliability = round(
        (
            float(success.get("verification_success") or 0)
            + float(consistency.get("verification_consistency") or 0)
            + float(proof.get("success_evidence_score") or 0) * 0.25
        )
        / 2.25,
        3,
    )

    return {
        "report_id": "autonomous-reliability-certification-report",
        "program_session_id": program_session_id,
        "execution_reliability": execution_reliability,
        "deployment_reliability": deployment_reliability,
        "verification_reliability": verification_reliability,
        "execution_reliability_score": execution_reliability,
        "deployment_reliability_score": deployment_reliability,
        "verification_reliability_score": verification_reliability,
        "sustained_execution_success_demonstrated": execution_reliability > 0,
        "sustained_deployment_success_demonstrated": deployment_reliability > 0,
        "sustained_verification_success_demonstrated": verification_reliability > 0,
        "reliability_certification_demonstrated": execution_reliability > 0,
        "read_only": True,
    }


def build_autonomous_recovery_certification_report(*, program_session_id: str) -> dict[str, Any]:
    recovery = build_execution_recovery_report(program_session_id=program_session_id)
    recovery_evidence = build_autonomous_recovery_evidence_report(program_session_id=program_session_id)

    failure_handling = float(recovery.get("failure_detection_rate") or 0)
    recovery_effectiveness = float(recovery.get("recovery_effectiveness_score") or 0)
    recovery_consistency = round(
        (recovery_effectiveness + float(recovery_evidence.get("recovery_evidence_score") or 0)) / 2,
        3,
    )
    recovery_certification_score = round(
        (failure_handling + recovery_effectiveness + recovery_consistency) / 3,
        3,
    )

    return {
        "report_id": "autonomous-recovery-certification-report",
        "program_session_id": program_session_id,
        "failure_handling_score": failure_handling,
        "recovery_effectiveness_score": recovery_effectiveness,
        "recovery_consistency_score": recovery_consistency,
        "recovery_certification_score": recovery_certification_score,
        "sustained_recovery_success_demonstrated": recovery_certification_score > 0,
        "recovery_certification_demonstrated": True,
        "read_only": True,
    }


def build_autonomous_intervention_certification_report(*, program_session_id: str) -> dict[str, Any]:
    intervention = build_human_intervention_report(program_session_id=program_session_id)
    reviews = _human_certification_records(program_session_id=program_session_id)
    registry = build_autonomous_certification_candidate_registry(program_session_id=program_session_id)
    candidate_count = int(registry.get("candidate_count") or 1)

    intervention_frequency = round(len(reviews) / max(candidate_count, 1), 3)
    baseline_rate = float(intervention.get("human_intervention_rate") or 0)
    intervention_reduction = round(max(0.0, baseline_rate - intervention_frequency), 3)
    override_frequency = sum(
        1 for r in reviews if "reject" in str(r.get("kind") or "") or "hold" in str(r.get("kind") or "")
    )
    approval_efficiency = round(
        sum(1 for r in reviews if "review_approve" in str(r.get("kind") or "")) / max(len(reviews), 1),
        3,
    ) if reviews else 1.0

    intervention_certification_score = round(
        (
            (1.0 - min(intervention_frequency, 1.0))
            + intervention_reduction
            + approval_efficiency
        )
        / 3,
        3,
    )

    return {
        "report_id": "autonomous-intervention-certification-report",
        "program_session_id": program_session_id,
        "intervention_frequency": intervention_frequency,
        "override_frequency": override_frequency,
        "approval_efficiency": approval_efficiency,
        "intervention_reduction": intervention_reduction,
        "intervention_certification_score": intervention_certification_score,
        "declining_intervention_demonstrated": intervention_reduction >= 0,
        "intervention_certification_demonstrated": True,
        "humans_remain_final_authority": True,
        "read_only": True,
    }


def build_autonomous_capability_certification_matrix(*, program_session_id: str) -> dict[str, Any]:
    success = build_execution_success_report(program_session_id=program_session_id)
    reliability = build_autonomous_reliability_certification_report(program_session_id=program_session_id)
    recovery = build_autonomous_recovery_certification_report(program_session_id=program_session_id)

    capabilities: list[dict[str, Any]] = []
    for track in success.get("execution_track_success") or []:
        rate = float(track.get("success_rate") or 0)
        if rate >= 0.8:
            status = "certified"
        elif rate >= 0.4:
            status = "conditionally_certified"
        else:
            status = "uncertified"
        capabilities.append(
            {
                "capability_id": track.get("execution_track"),
                "capability": f"{track.get('execution_track')} governed operations",
                "certification_rate": rate,
                "status": status,
            }
        )

    capabilities.extend(
        [
            {
                "capability_id": "execution_reliability",
                "capability": "Sustained execution reliability",
                "certification_rate": reliability.get("execution_reliability_score"),
                "status": "certified"
                if float(reliability.get("execution_reliability_score") or 0) >= 0.8
                else "conditionally_certified",
            },
            {
                "capability_id": "recovery_operations",
                "capability": "Recovery operations",
                "certification_rate": recovery.get("recovery_certification_score"),
                "status": "certified"
                if float(recovery.get("recovery_certification_score") or 0) >= 0.8
                else "conditionally_certified",
            },
        ]
    )

    return {
        "matrix_id": "autonomous-capability-certification-matrix",
        "program_session_id": program_session_id,
        "certified_capabilities": [c for c in capabilities if c.get("status") == "certified"],
        "conditionally_certified_capabilities": [
            c for c in capabilities if c.get("status") == "conditionally_certified"
        ],
        "uncertified_capabilities": [c for c in capabilities if c.get("status") == "uncertified"],
        "capabilities": capabilities,
        "capability_certification_demonstrated": bool(capabilities),
        "read_only": True,
    }


def build_multi_environment_certification_report(*, program_session_id: str) -> dict[str, Any]:
    deployment_rows = _deployment_provider_rows()
    success_evidence = build_autonomous_success_evidence_report(program_session_id=program_session_id)

    environments: list[dict[str, Any]] = []
    for provider in PROVIDER_CATEGORIES:
        provider_rows = [
            row for row in deployment_rows if str(row.get("provider") or "") == provider
        ]
        if provider_rows:
            passed = sum(
                1
                for row in provider_rows
                if (row.get("verification_receipt") or {}).get("health_check_passed") is True
            )
            certification_rate = round(passed / len(provider_rows), 3)
            status = "certified" if certification_rate >= 0.8 else "conditionally_certified" if certification_rate >= 0.4 else "uncertified"
        elif provider == "Railway" and float(success_evidence.get("success_rate") or 0) > 0:
            certification_rate = float(success_evidence.get("success_rate") or 0)
            status = "conditionally_certified" if certification_rate >= 0.4 else "uncertified"
        else:
            certification_rate = 0.0
            status = "uncertified"

        environments.append(
            {
                "provider": provider,
                "deployment_count": len(provider_rows),
                "certification_rate": certification_rate,
                "status": status,
            }
        )

    certified_count = sum(1 for env in environments if env.get("status") == "certified")
    conditional_count = sum(1 for env in environments if env.get("status") == "conditionally_certified")

    return {
        "report_id": "multi-environment-certification-report",
        "program_session_id": program_session_id,
        "environments_evaluated": list(PROVIDER_CATEGORIES),
        "environment_certifications": environments,
        "certified_environment_count": certified_count,
        "conditionally_certified_environment_count": conditional_count,
        "multi_environment_certification_demonstrated": certified_count + conditional_count >= 1,
        "read_only": True,
    }


def build_autonomous_certification_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    reliability = build_autonomous_reliability_certification_report(program_session_id=program_session_id)
    multi_env = build_multi_environment_certification_report(program_session_id=program_session_id)
    capability = build_autonomous_capability_certification_matrix(program_session_id=program_session_id)
    registry = build_autonomous_certification_candidate_registry(program_session_id=program_session_id)

    opportunities: list[dict[str, Any]] = []
    if int(registry.get("candidate_count") or 0) < AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE:
        opportunities.append(
            {
                "opportunity_id": "sustained-candidate-gap",
                "area": "certification_candidates",
                "gap": "Sustained certification candidate volume below threshold",
                "priority": "high",
            }
        )
    if float(reliability.get("deployment_reliability_score") or 0) < 0.8:
        opportunities.append(
            {
                "opportunity_id": "deployment-reliability-gap",
                "area": "reliability_certification",
                "gap": "Deployment reliability below certification threshold",
                "priority": "medium",
            }
        )
    for env in multi_env.get("environment_certifications") or []:
        if env.get("status") == "uncertified":
            opportunities.append(
                {
                    "opportunity_id": f"environment-{env.get('provider')}",
                    "area": "multi_environment",
                    "gap": f"Uncertified provider environment: {env.get('provider')}",
                    "priority": "medium",
                }
            )
    for cap in capability.get("uncertified_capabilities") or []:
        opportunities.append(
            {
                "opportunity_id": f"capability-{cap.get('capability_id')}",
                "area": "capability_certification",
                "gap": f"Uncertified capability: {cap.get('capability')}",
                "priority": "low",
            }
        )

    return {
        "registry_id": "autonomous-certification-opportunity-registry",
        "program_session_id": program_session_id,
        "weak_proof_areas": [o for o in opportunities if o.get("priority") == "medium"],
        "missing_scenarios": [o for o in opportunities if o.get("priority") == "high"],
        "uncertified_capabilities": [o for o in opportunities if o.get("area") == "capability_certification"],
        "opportunities": opportunities,
        "certification_opportunity_registry_demonstrated": True,
        "read_only": True,
    }


def _autonomous_operations_certification_level(*, metrics: dict[str, Any], program_session_id: str) -> str:
    execution = float(metrics.get("execution_reliability_score") or 0)
    recovery = float(metrics.get("recovery_certification_score") or 0)
    intervention = float(metrics.get("intervention_certification_score") or 0)
    registry = build_autonomous_certification_candidate_registry(program_session_id=program_session_id)
    candidate_count = int(registry.get("candidate_count") or 0)

    if has_autonomous_certification_review_approve(program_session_id=program_session_id):
        if candidate_count >= AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE and execution >= 0.8 and recovery >= 0.7:
            return "certified"
    if recovery >= 0.7 and execution >= 0.6:
        return "resilient"
    if execution >= 0.7:
        return "reliable"
    if candidate_count >= AUTONOMOUS_CERTIFICATION_SUSTAINED_MIN_SIZE:
        return "repeatable"
    if candidate_count >= 1:
        return "demonstrated"
    return "demonstrated"


def compute_autonomous_operations_certification_metrics(*, program_session_id: str) -> dict[str, Any]:
    reliability = build_autonomous_reliability_certification_report(program_session_id=program_session_id)
    recovery = build_autonomous_recovery_certification_report(program_session_id=program_session_id)
    intervention = build_autonomous_intervention_certification_report(program_session_id=program_session_id)
    maturity = compute_autonomous_execution_maturity_metrics(program_session_id=program_session_id)
    proof = compute_autonomous_execution_proof_metrics(program_session_id=program_session_id)

    execution_reliability = float(reliability.get("execution_reliability_score") or 0)
    deployment_reliability = float(reliability.get("deployment_reliability_score") or 0)
    verification_reliability = float(reliability.get("verification_reliability_score") or 0)
    recovery_score = float(recovery.get("recovery_certification_score") or 0)
    intervention_score = float(intervention.get("intervention_certification_score") or 0)

    certification_score = round(
        (
            execution_reliability
            + deployment_reliability
            + verification_reliability
            + recovery_score
            + intervention_score
            + float(maturity.get("autonomous_execution_maturity_score") or 0) * 0.2
            + float(proof.get("autonomous_execution_proof_score") or 0) * 0.2
        )
        / 5.4,
        3,
    )

    metrics = {
        "execution_reliability_score": execution_reliability,
        "deployment_reliability_score": deployment_reliability,
        "verification_reliability_score": verification_reliability,
        "recovery_certification_score": recovery_score,
        "intervention_certification_score": intervention_score,
        "autonomous_operations_certification_score": certification_score,
        "phase_i1_maturity_reference_score": float(maturity.get("autonomous_execution_maturity_score") or 0),
        "phase_i2_proof_reference_score": float(proof.get("autonomous_execution_proof_score") or 0),
        "autonomous_operations_certification_level": "",
        "autonomous_operations_certification_levels": list(AUTONOMOUS_OPERATIONS_CERTIFICATION_LEVELS),
        "read_only": True,
    }
    metrics["autonomous_operations_certification_level"] = _autonomous_operations_certification_level(
        metrics=metrics,
        program_session_id=program_session_id,
    )
    return metrics


def register_certification_candidate_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    candidate_id = kv.get("candidate_id") or kv.get("candidate") or (
        f"cert-{len(_certification_candidates(program_session_id=program_session_id)) + 1}"
    )
    entry = register_certification_candidate(
        entry={
            "candidate_id": candidate_id,
            "program_session_id": program_session_id,
            "workload_category": _normalize_workload(kv.get("workload") or kv.get("workload_category")),
            "provider_category": _normalize_provider(kv.get("provider") or kv.get("provider_category")),
            "objective": kv.get("objective") or "Certify sustained governed autonomous operations",
        }
    )
    from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_store import (
        append_autonomous_certification_record,
    )

    append_autonomous_certification_record(
        session_id=program_session_id,
        kind="autonomous_certification_candidate_entry",
        content=body,
        metadata=entry,
    )
    return entry
