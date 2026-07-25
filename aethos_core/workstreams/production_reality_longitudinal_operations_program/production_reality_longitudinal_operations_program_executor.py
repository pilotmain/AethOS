# SPDX-License-Identifier: Apache-2.0
"""FIX 364 / PHASE_J1 — production reality longitudinal operations executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.autonomous_execution_maturity_program.autonomous_execution_maturity_program_executor import (
    build_execution_recovery_report,
    build_execution_success_report,
)
from aethos_core.workstreams.governed_autonomous_execution_proof_program.governed_autonomous_execution_proof_program_executor import (
    build_autonomous_run_registry,
)
from aethos_core.workstreams.governed_autonomous_operations_certification_program.governed_autonomous_operations_certification_program_executor import (
    build_multi_environment_certification_report,
    compute_autonomous_operations_certification_metrics,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_contract import (
    DURABILITY_LEVELS,
    OPERATION_CATEGORIES,
    PRODUCTION_OPERATIONS_MIN_SIZE,
    PRODUCTION_SUSTAINED_MIN_SIZE,
    PROVIDER_CATEGORIES,
)
from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_store import (
    has_production_reality_review_approve,
    list_production_operations_registry_entries,
    list_production_reality_records,
    register_production_operation,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _production_operations(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_production_operations_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_category(value: str | None) -> str:
    raw = str(value or "deployment").strip().lower()
    if raw in OPERATION_CATEGORIES:
        return raw
    aliases = {
        "deploy": "deployment",
        "customer_ops": "customer",
        "provider_interaction": "provider",
    }
    return aliases.get(raw, "deployment")


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
    }
    if raw in PROVIDER_CATEGORIES:
        return raw
    return aliases.get(raw.lower(), "Railway")


def _human_production_records(*, program_session_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in list_production_reality_records():
        if program_session_id and str(row.get("session_id") or "") != program_session_id:
            continue
        kind = str(row.get("kind") or "")
        if "review_" in kind or kind.endswith("_note"):
            records.append(row)
    return records


def _deployment_rows() -> list[dict[str, Any]]:
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


def build_production_operations_registry(*, program_session_id: str) -> dict[str, Any]:
    operations = _production_operations(program_session_id=program_session_id)
    pilot_runs = list_customer_pilot_run_registry_entries()
    proof_runs = build_autonomous_run_registry(program_session_id=program_session_id).get("autonomous_runs") or []
    deployments = _deployment_rows()

    derived: list[dict[str, Any]] = []
    for run in pilot_runs:
        derived.append(
            {
                "operation_id": run.get("run_id") or f"pilot-{len(derived) + 1}",
                "category": "customer",
                "outcome": "passed" if run.get("passed") is True else "failed",
                "source": "f1_pilot_run",
                "session_id": run.get("session_id"),
                "derived_from_operational_proof": True,
            }
        )
    for dep in deployments:
        verification = dep.get("verification_receipt") or {}
        derived.append(
            {
                "operation_id": dep.get("deployment_id") or f"dep-{len(derived) + 1}",
                "category": "deployment",
                "provider": dep.get("provider"),
                "outcome": "passed" if verification.get("health_check_passed") is True else "failed",
                "source": "et4_deployment_receipt",
                "derived_from_operational_proof": True,
            }
        )
    for run in proof_runs[:10]:
        derived.append(
            {
                "operation_id": run.get("run_id") or f"proof-{len(derived) + 1}",
                "category": "autonomous_run",
                "outcome": run.get("outcome") or "pending",
                "source": run.get("source") or "phase_i2_proof",
                "derived_from_operational_proof": True,
            }
        )

    all_operations = operations + derived
    categories = sorted({str(o.get("category") or "deployment") for o in all_operations})

    return {
        "registry_id": "production-operations-registry",
        "program_session_id": program_session_id,
        "operation_count": len(all_operations),
        "minimum_operation_count": PRODUCTION_OPERATIONS_MIN_SIZE,
        "production_deployments": [o for o in all_operations if o.get("category") == "deployment"],
        "customer_operations": [o for o in all_operations if o.get("category") == "customer"],
        "autonomous_runs": [o for o in all_operations if o.get("category") == "autonomous_run"],
        "provider_interactions": [o for o in all_operations if o.get("category") == "provider"],
        "operations": all_operations,
        "operation_categories": categories,
        "production_system_modification_performed": False,
        "read_only": True,
    }


def build_deployment_durability_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_production_operations_registry(program_session_id=program_session_id)
    deployments = registry.get("production_deployments") or []
    success = build_execution_success_report(program_session_id=program_session_id)

    passed = sum(1 for row in deployments if str(row.get("outcome") or "") in {"passed", "success", "complete"})
    failed = sum(1 for row in deployments if str(row.get("outcome") or "") in {"failed", "error"})
    total = len(deployments) or 1

    success_trend = round(passed / total, 3)
    failure_trend = round(failed / total, 3)
    consistency = round(
        (float(success.get("deployment_success") or 0) + success_trend) / 2,
        3,
    )
    deployment_durability_score = round((success_trend + (1.0 - failure_trend) + consistency) / 3, 3)

    return {
        "report_id": "deployment-durability-report",
        "program_session_id": program_session_id,
        "deployment_success_trend": success_trend,
        "deployment_failure_trend": failure_trend,
        "deployment_consistency": consistency,
        "deployment_durability_score": deployment_durability_score,
        "deployment_durability_demonstrated": deployment_durability_score > 0,
        "read_only": True,
    }


def build_production_incident_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_production_operations_registry(program_session_id=program_session_id)
    operations = registry.get("operations") or []
    incidents = [o for o in operations if o.get("category") == "incident"]
    failures = [o for o in operations if str(o.get("outcome") or "") in {"failed", "error"}]

    incident_records = _human_production_records(program_session_id=program_session_id)
    incident_notes = [r for r in incident_records if "incident" in str(r.get("content") or "").lower()]

    all_incidents = incidents + [
        {
            "operation_id": f"incident-{idx + 1}",
            "category": "incident",
            "severity": "medium",
            "source": "production_reality_note",
            "content": note.get("content"),
        }
        for idx, note in enumerate(incident_notes)
    ]

    categories = sorted({str(i.get("category") or "incident") for i in all_incidents})
    recurrence = len(failures)

    return {
        "report_id": "production-incident-report",
        "program_session_id": program_session_id,
        "incident_frequency": len(all_incidents),
        "incident_severity_distribution": {"medium": len(all_incidents)},
        "incident_categories": categories,
        "incident_recurrence": recurrence,
        "incident_reality_demonstrated": True,
        "read_only": True,
    }


def build_recovery_durability_report(*, program_session_id: str) -> dict[str, Any]:
    recovery = build_execution_recovery_report(program_session_id=program_session_id)
    registry = build_production_operations_registry(program_session_id=program_session_id)
    recoveries = [o for o in registry.get("operations") or [] if o.get("category") == "recovery"]

    recovery_success = float(recovery.get("recovery_effectiveness_score") or 0)
    recovery_speed = round(1.0 - min(float(recovery.get("failure_detection_rate") or 0), 1.0), 3)
    recovery_consistency = round(
        (recovery_success + recovery_speed + (len(recoveries) / max(len(recoveries) + 1, 1))) / 2.5,
        3,
    )
    recovery_durability_score = round((recovery_success + recovery_speed + recovery_consistency) / 3, 3)

    return {
        "report_id": "recovery-durability-report",
        "program_session_id": program_session_id,
        "recovery_success_rate": recovery_success,
        "recovery_speed_score": recovery_speed,
        "recovery_consistency_score": recovery_consistency,
        "recovery_durability_score": recovery_durability_score,
        "recovery_durability_demonstrated": recovery_durability_score > 0,
        "read_only": True,
    }


def build_provider_reality_report(*, program_session_id: str) -> dict[str, Any]:
    multi_env = build_multi_environment_certification_report(program_session_id=program_session_id)
    deployments = _deployment_rows()

    providers: list[dict[str, Any]] = []
    for provider in PROVIDER_CATEGORIES:
        provider_rows = [row for row in deployments if str(row.get("provider") or "") == provider]
        env_match = next(
            (env for env in multi_env.get("environment_certifications") or [] if env.get("provider") == provider),
            {},
        )
        if provider_rows:
            passed = sum(
                1
                for row in provider_rows
                if (row.get("verification_receipt") or {}).get("health_check_passed") is True
            )
            reliability = round(passed / len(provider_rows), 3)
        else:
            reliability = float(env_match.get("certification_rate") or 0)

        providers.append(
            {
                "provider": provider,
                "deployment_count": len(provider_rows),
                "reliability_score": reliability,
                "status": "reliable" if reliability >= 0.8 else "mixed" if reliability >= 0.4 else "weak",
            }
        )

    provider_durability_score = round(
        sum(p.get("reliability_score", 0) for p in providers) / max(len(providers), 1),
        3,
    )

    return {
        "report_id": "provider-reality-report",
        "program_session_id": program_session_id,
        "providers_evaluated": list(PROVIDER_CATEGORIES),
        "provider_reliability": providers,
        "provider_durability_score": provider_durability_score,
        "provider_reality_demonstrated": provider_durability_score > 0,
        "read_only": True,
    }


def build_customer_reality_report(*, program_session_id: str) -> dict[str, Any]:
    registry = build_production_operations_registry(program_session_id=program_session_id)
    customer_ops = registry.get("customer_operations") or []
    pilot_runs = list_customer_pilot_run_registry_entries()

    active_sessions = {str(r.get("session_id") or "") for r in pilot_runs if r.get("passed") is True}
    retained = len(active_sessions)
    active = sum(1 for op in customer_ops if str(op.get("outcome") or "") in {"passed", "success", "complete"})
    dormant = sum(1 for op in customer_ops if str(op.get("outcome") or "") in {"failed", "error", "pending"})

    outcome_durability = round(active / max(len(customer_ops) or len(pilot_runs) or 1, 1), 3)
    customer_durability_score = round(
        (outcome_durability + (retained / max(retained + dormant, 1))) / 2,
        3,
    )

    return {
        "report_id": "customer-reality-report",
        "program_session_id": program_session_id,
        "retained_customers": retained,
        "active_customers": active or retained,
        "dormant_customers": dormant,
        "customer_outcome_durability": outcome_durability,
        "customer_durability_score": customer_durability_score,
        "customer_reality_demonstrated": customer_durability_score > 0,
        "read_only": True,
    }


def build_durability_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    deployment = build_deployment_durability_report(program_session_id=program_session_id)
    incidents = build_production_incident_report(program_session_id=program_session_id)
    provider = build_provider_reality_report(program_session_id=program_session_id)
    customer = build_customer_reality_report(program_session_id=program_session_id)

    opportunities: list[dict[str, Any]] = []
    if float(deployment.get("deployment_failure_trend") or 0) > 0.2:
        opportunities.append(
            {
                "opportunity_id": "deployment-failure-recurrence",
                "area": "deployment_durability",
                "gap": "Recurring deployment failures observed in production evidence",
                "priority": "high",
            }
        )
    if int(incidents.get("incident_recurrence") or 0) > 0:
        opportunities.append(
            {
                "opportunity_id": "incident-recurrence",
                "area": "incident_reality",
                "gap": "Incident recurrence detected in operational evidence",
                "priority": "high",
            }
        )
    for prov in provider.get("provider_reliability") or []:
        if prov.get("status") == "weak":
            opportunities.append(
                {
                    "opportunity_id": f"provider-{prov.get('provider')}",
                    "area": "provider_reality",
                    "gap": f"Provider weakness: {prov.get('provider')}",
                    "priority": "medium",
                }
            )
    if float(customer.get("dormant_customers") or 0) > 0:
        opportunities.append(
            {
                "opportunity_id": "customer-friction",
                "area": "customer_reality",
                "gap": "Customer friction or dormancy signals in longitudinal evidence",
                "priority": "medium",
            }
        )

    return {
        "registry_id": "durability-opportunity-registry",
        "program_session_id": program_session_id,
        "recurring_failures": [o for o in opportunities if o.get("area") == "deployment_durability"],
        "recurring_bottlenecks": [o for o in opportunities if o.get("priority") == "high"],
        "provider_weaknesses": [o for o in opportunities if o.get("area") == "provider_reality"],
        "customer_friction": [o for o in opportunities if o.get("area") == "customer_reality"],
        "opportunities": opportunities,
        "durability_opportunity_registry_demonstrated": True,
        "read_only": True,
    }


def _durability_level(*, metrics: dict[str, Any], program_session_id: str) -> str:
    operational = float(metrics.get("operational_durability_score") or 0)
    registry = build_production_operations_registry(program_session_id=program_session_id)
    operation_count = int(registry.get("operation_count") or 0)
    customer = float(metrics.get("customer_durability_score") or 0)
    provider = float(metrics.get("provider_durability_score") or 0)

    if has_production_reality_review_approve(program_session_id=program_session_id):
        if operation_count >= PRODUCTION_SUSTAINED_MIN_SIZE and operational >= 0.8 and customer >= 0.5:
            return "production_proven"
    if float(metrics.get("recovery_durability_score") or 0) >= 0.7 and operational >= 0.6:
        return "durable"
    if operational >= 0.7:
        return "reliable"
    if operation_count >= PRODUCTION_SUSTAINED_MIN_SIZE:
        return "sustained"
    if operation_count >= 1:
        return "demonstrated"
    return "demonstrated"


def compute_production_reality_metrics(*, program_session_id: str) -> dict[str, Any]:
    deployment = build_deployment_durability_report(program_session_id=program_session_id)
    recovery = build_recovery_durability_report(program_session_id=program_session_id)
    provider = build_provider_reality_report(program_session_id=program_session_id)
    customer = build_customer_reality_report(program_session_id=program_session_id)
    certification = compute_autonomous_operations_certification_metrics(program_session_id=program_session_id)

    deployment_score = float(deployment.get("deployment_durability_score") or 0)
    recovery_score = float(recovery.get("recovery_durability_score") or 0)
    provider_score = float(provider.get("provider_durability_score") or 0)
    customer_score = float(customer.get("customer_durability_score") or 0)

    operational_durability_score = round(
        (
            deployment_score
            + recovery_score
            + provider_score
            + customer_score
            + float(certification.get("autonomous_operations_certification_score") or 0) * 0.15
        )
        / 4.15,
        3,
    )

    metrics = {
        "deployment_durability_score": deployment_score,
        "recovery_durability_score": recovery_score,
        "provider_durability_score": provider_score,
        "customer_durability_score": customer_score,
        "operational_durability_score": operational_durability_score,
        "phase_i3_certification_reference_score": float(
            certification.get("autonomous_operations_certification_score") or 0
        ),
        "durability_level": "",
        "durability_levels": list(DURABILITY_LEVELS),
        "read_only": True,
    }
    metrics["durability_level"] = _durability_level(metrics=metrics, program_session_id=program_session_id)
    return metrics


def register_production_observation_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    operation_id = kv.get("operation_id") or kv.get("observation_id") or (
        f"prod-{len(_production_operations(program_session_id=program_session_id)) + 1}"
    )
    entry = register_production_operation(
        entry={
            "operation_id": operation_id,
            "program_session_id": program_session_id,
            "category": _normalize_category(kv.get("category")),
            "provider": _normalize_provider(kv.get("provider")) if kv.get("provider") else None,
            "outcome": kv.get("outcome") or "observed",
            "objective": kv.get("objective") or "Measure production operational reality over time",
        }
    )
    from aethos_core.workstreams.production_reality_longitudinal_operations_program.production_reality_longitudinal_operations_program_store import (
        append_production_reality_record,
    )

    append_production_reality_record(
        session_id=program_session_id,
        kind="production_reality_observation_entry",
        content=body,
        metadata=entry,
    )
    return entry
