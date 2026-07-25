# SPDX-License-Identifier: Apache-2.0
"""FIX 357 / WORKSTREAM_G4 — enterprise platform maturity & readiness audit executor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_executor import (
    compute_validation_metrics,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    list_usage_observation_registry_entries,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    list_customer_pilot_run_registry_entries,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_executor import (
    build_evidence_density_report,
    build_evidence_freshness_report,
    build_trust_maturity_report,
)

_AETHOS_CORE = Path(__file__).resolve().parents[2]
_MISSION_CONTROL = _AETHOS_CORE / "mission_control"
_WORKSTREAMS = _AETHOS_CORE / "workstreams"
_EXECUTION_TRACKS = _AETHOS_CORE / "execution_tracks"

FIX_300_330_CATALOG: tuple[tuple[str, str], ...] = (
    ("FIX 300", "multi_tenant_platform_foundation"),
    ("FIX 301", "tenant_onboarding_activation"),
    ("FIX 302", "identity_access_hardening"),
    ("FIX 303", "provider_connection_experience"),
    ("FIX 304", "channel_integration_foundation"),
    ("FIX 305", "billing_entitlements_foundation"),
    ("FIX 306", "customer_administration_console"),
    ("FIX 307", "customer_usage_audit_portal"),
    ("FIX 308", "payment_integration_readiness"),
    ("FIX 309", "saas_launch_readiness_assessment"),
    ("FIX 310", "customer_support_success_foundation"),
    ("FIX 311", "public_product_experience"),
    ("FIX 312", "limited_beta_launch_program"),
    ("FIX 313", "launch_operations_center"),
    ("FIX 314", "public_launch_readiness_freeze"),
    ("FIX 315", "launch_decision_package"),
    ("FIX 316", "post_launch_operations_baseline"),
    ("FIX 317", "continuous_product_improvement"),
    ("FIX 318", "product_analytics_foundation"),
    ("FIX 319", "customer_feedback_intelligence"),
    ("FIX 320", "growth_adoption_intelligence"),
    ("FIX 321", "customer_journey_intelligence"),
    ("FIX 322", "product_market_fit_intelligence"),
    ("FIX 323", "customer_value_realization_intelligence"),
    ("FIX 324", "strategic_portfolio_intelligence"),
    ("FIX 325", "executive_decision_intelligence"),
    ("FIX 326", "strategic_planning_intelligence"),
    ("FIX 327", "enterprise_program_intelligence"),
    ("FIX 328", "organizational_effectiveness_intelligence"),
    ("FIX 329", "enterprise_operating_review_intelligence"),
    ("FIX 330", "executive_operating_system_dashboard"),
)

EXECUTION_TRACK_CATALOG: tuple[tuple[str, str, str], ...] = (
    (
        "ET1",
        "governed_workspace_creation_repository_bootstrap",
        "list_governed_workspace_creation_records",
    ),
    (
        "ET2",
        "governed_code_generation_changeset_creation",
        "list_governed_code_generation_records",
    ),
    ("ET3", "governed_git_delivery", "list_governed_git_delivery_records"),
    ("ET4", "governed_deployment_execution", "list_governed_deployment_execution_records"),
    (
        "ET5",
        "governed_end_to_end_delivery_certification",
        "list_governed_end_to_end_delivery_certification_records",
    ),
)

WORKSTREAM_AD_CATALOG: tuple[tuple[str, str], ...] = (
    ("WORKSTREAM_A1", "pilotos_operational_proof_program"),
    ("WORKSTREAM_A2", "atlas_operational_proof_program"),
    ("WORKSTREAM_A3", "nexora_operational_proof_program"),
    ("WORKSTREAM_B1", "limited_external_customer_validation_program"),
    ("WORKSTREAM_C1", "real_world_delivery_proof_program"),
    ("WORKSTREAM_C2", "delivery_optimization_program"),
    ("WORKSTREAM_D1", "phase2_provider_execution_expansion_program"),
    ("WORKSTREAM_D2", "multi_cloud_operational_proof_program"),
)

WORKSTREAM_F_CATALOG: tuple[tuple[str, str], ...] = (
    ("WORKSTREAM_F1", "first_customer_delivery_pilot_program"),
    ("WORKSTREAM_F2", "customer_value_adoption_validation_program"),
    ("WORKSTREAM_F3", "multi_customer_value_proof_program"),
    ("WORKSTREAM_F4", "customer_scale_validation_program"),
    ("WORKSTREAM_F5", "commercial_validation_program"),
    ("WORKSTREAM_F6", "unit_economics_business_sustainability_program"),
    ("WORKSTREAM_F7", "business_operating_model_validation_program"),
)

WORKSTREAM_G_CATALOG: tuple[tuple[str, str], ...] = (
    ("WORKSTREAM_G1", "real_evidence_density_trust_maturity_program"),
    ("WORKSTREAM_G2", "real_usage_density_platform_adoption_program"),
    ("WORKSTREAM_G3", "revenue_density_business_viability_program"),
)


def _load_store_rows(module_path: str, list_fn: str) -> list[dict[str, Any]]:
    try:
        mod = __import__(module_path, fromlist=[list_fn])
        rows = getattr(mod, list_fn)()
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []
    return []


def _et_rows(et_id: str, track_slug: str, list_fn: str) -> list[dict[str, Any]]:
    module_path = f"aethos_core.execution_tracks.{track_slug}.{track_slug}_store"
    return _load_store_rows(module_path, list_fn)


def build_platform_inventory_registry(*, program_session_id: str) -> dict[str, Any]:
    fix_modules: list[dict[str, Any]] = []
    for fix_id, slug in FIX_300_330_CATALOG:
        present = (_MISSION_CONTROL / slug).is_dir()
        fix_modules.append(
            {
                "fix_id": fix_id,
                "module_slug": slug,
                "module_present": present,
                "read_only": True,
            }
        )

    execution_tracks: list[dict[str, Any]] = []
    for et_id, track_slug, list_fn in EXECUTION_TRACK_CATALOG:
        rows = _et_rows(et_id, track_slug, list_fn)
        execution_tracks.append(
            {
                "execution_track": et_id,
                "track_slug": track_slug,
                "module_present": (_EXECUTION_TRACKS / track_slug).is_dir(),
                "record_count": len(rows),
                "store_populated": len(rows) > 0,
            }
        )

    workstreams_ad: list[dict[str, Any]] = []
    for ws_id, slug in WORKSTREAM_AD_CATALOG:
        workstreams_ad.append(
            {
                "workstream_id": ws_id,
                "module_slug": slug,
                "module_present": (_WORKSTREAMS / slug).is_dir(),
            }
        )

    workstreams_f: list[dict[str, Any]] = []
    for ws_id, slug in WORKSTREAM_F_CATALOG:
        workstreams_f.append(
            {
                "workstream_id": ws_id,
                "module_slug": slug,
                "module_present": (_WORKSTREAMS / slug).is_dir(),
            }
        )

    workstreams_g: list[dict[str, Any]] = []
    for ws_id, slug in WORKSTREAM_G_CATALOG:
        workstreams_g.append(
            {
                "workstream_id": ws_id,
                "module_slug": slug,
                "module_present": (_WORKSTREAMS / slug).is_dir(),
            }
        )

    fix_present = sum(1 for item in fix_modules if item["module_present"])
    return {
        "registry_id": "platform-inventory-registry",
        "program_session_id": program_session_id,
        "fix_300_330_modules": fix_modules,
        "fix_300_330_present_count": fix_present,
        "fix_300_330_total": len(fix_modules),
        "execution_tracks": execution_tracks,
        "workstreams_a_through_d": workstreams_ad,
        "workstreams_f1_through_f7": workstreams_f,
        "workstreams_g1_through_g3": workstreams_g,
        "inventory_complete": fix_present == len(fix_modules),
        "read_only": True,
    }


def build_architecture_maturity_report(*, program_session_id: str) -> dict[str, Any]:
    inventory = build_platform_inventory_registry(program_session_id=program_session_id)
    fix_coverage = round(
        inventory["fix_300_330_present_count"] / max(inventory["fix_300_330_total"], 1),
        3,
    )
    ws_count = (
        len(inventory["workstreams_a_through_d"])
        + len(inventory["workstreams_f1_through_f7"])
        + len(inventory["workstreams_g1_through_g3"])
    )
    ws_present = sum(
        1
        for group in (
            inventory["workstreams_a_through_d"],
            inventory["workstreams_f1_through_f7"],
            inventory["workstreams_g1_through_g3"],
        )
        for item in group
        if item.get("module_present")
    )
    composability = round(ws_present / max(ws_count, 1), 3)
    certification_modules = sum(
        1
        for ws_id, slug in (*WORKSTREAM_F_CATALOG, *WORKSTREAM_G_CATALOG)
        if (_WORKSTREAMS / slug / f"{slug}_contract.py").is_file()
    )
    maintainability = round(certification_modules / max(ws_count, 1), 3)
    dependency_health = round((fix_coverage + composability) / 2, 3)
    architecture_score = round((fix_coverage + composability + maintainability + dependency_health) / 4, 3)

    return {
        "report_id": "architecture-maturity-report",
        "program_session_id": program_session_id,
        "composability": composability,
        "maintainability": maintainability,
        "coverage": fix_coverage,
        "dependency_health": dependency_health,
        "architecture_maturity_score": architecture_score,
        "architecture_maturity_demonstrated": architecture_score >= 0.8,
        "read_only": True,
    }


def build_execution_maturity_report(*, program_session_id: str) -> dict[str, Any]:
    track_stats: list[dict[str, Any]] = []
    passed_total = 0
    run_total = 0

    for et_id, track_slug, list_fn in EXECUTION_TRACK_CATALOG:
        rows = _et_rows(et_id, track_slug, list_fn)
        passed = sum(1 for row in rows if row.get("passed") is True or row.get("status") == "passed")
        run_total += len(rows)
        passed_total += passed
        track_stats.append(
            {
                "execution_track": et_id,
                "record_count": len(rows),
                "passed_count": passed,
                "reliability": round(passed / len(rows), 3) if rows else 0.0,
            }
        )

    pilot_runs = list_customer_pilot_run_registry_entries()
    delivery_passed = sum(1 for run in pilot_runs if run.get("passed") is True)
    delivery_reliability = round(delivery_passed / len(pilot_runs), 3) if pilot_runs else 0.0

    et5_rows = _et_rows("ET5", "governed_end_to_end_delivery_certification", "list_governed_end_to_end_delivery_certification_records")
    cert_passed = sum(1 for row in et5_rows if row.get("passed") is True)
    cert_reliability = round(cert_passed / len(et5_rows), 3) if et5_rows else 0.0

    execution_score = round(
        (
            (passed_total / run_total if run_total else 0.0)
            + delivery_reliability
            + cert_reliability
        )
        / 3,
        3,
    )

    return {
        "report_id": "execution-maturity-report",
        "program_session_id": program_session_id,
        "execution_track_performance": track_stats,
        "delivery_reliability": delivery_reliability,
        "certification_reliability": cert_reliability,
        "execution_maturity_score": execution_score,
        "execution_maturity_demonstrated": execution_score > 0 or run_total > 0,
        "read_only": True,
    }


def build_operational_maturity_report(*, program_session_id: str) -> dict[str, Any]:
    operational_proof = 0
    provider_proof = 0
    deployment_records = _et_rows("ET4", "governed_deployment_execution", "list_governed_deployment_execution_records")
    deployment_passed = sum(1 for row in deployment_records if row.get("passed") is True)
    deployment_reliability = round(deployment_passed / len(deployment_records), 3) if deployment_records else 0.0

    for ws_id, slug in WORKSTREAM_AD_CATALOG:
        if ws_id.startswith("WORKSTREAM_A"):
            store_path = f"aethos_core.workstreams.{slug}.{slug}_store"
            list_candidates = (
                f"list_{slug.replace('_program', '')}_records",
                f"list_{slug}_records",
            )
            for list_fn in list_candidates:
                rows = _load_store_rows(store_path, list_fn)
                if rows:
                    operational_proof += len(rows)
                    break

    for ws_id, slug in WORKSTREAM_AD_CATALOG:
        if ws_id.startswith("WORKSTREAM_D"):
            store_path = f"aethos_core.workstreams.{slug}.{slug}_store"
            list_fn = f"list_{slug.replace('_program', '')}_records"
            rows = _load_store_rows(store_path, list_fn)
            provider_proof += len(rows)

    recovery_rows = _et_rows(
        "ET5",
        "governed_end_to_end_delivery_certification",
        "list_governed_end_to_end_delivery_certification_records",
    )
    recovery_evidence = len(recovery_rows)

    operational_score = round(
        (
            min(1.0, operational_proof / 3)
            + min(1.0, provider_proof / 2)
            + deployment_reliability
            + min(1.0, recovery_evidence / 3)
        )
        / 4,
        3,
    )

    return {
        "report_id": "operational-maturity-report",
        "program_session_id": program_session_id,
        "operational_proof_coverage": operational_proof,
        "provider_proof_coverage": provider_proof,
        "deployment_reliability": deployment_reliability,
        "recovery_evidence_count": recovery_evidence,
        "operational_maturity_score": operational_score,
        "operational_maturity_demonstrated": operational_score > 0,
        "read_only": True,
    }


def _workstream_store_count(module_path: str, list_fn: str) -> int:
    return len(_load_store_rows(module_path, list_fn))


def build_customer_commercial_maturity_report(*, program_session_id: str) -> dict[str, Any]:
    f1_runs = list_customer_pilot_run_registry_entries()
    f2_observations = list_usage_observation_registry_entries()

    adoption_sessions = {str(o.get("session_id") or "") for o in f2_observations if o.get("session_id")}
    adoption_maturity = round(len(adoption_sessions) / max(len({r.get("session_id") for r in f1_runs}) or 1, 1), 3)

    value_scores: list[float] = []
    retention_scores: list[float] = []
    for session_id in adoption_sessions:
        if not session_id:
            continue
        metrics = compute_validation_metrics(session_id=session_id)
        value_scores.append(float(metrics.get("value_realization_score") or 0))
        retention_scores.append(float(metrics.get("retention_rate") or 0))

    value_maturity = round(sum(value_scores) / len(value_scores), 3) if value_scores else 0.0
    retention_maturity = round(sum(retention_scores) / len(retention_scores), 3) if retention_scores else 0.0

    f_store_counts = {
        "WORKSTREAM_F1": len(f1_runs),
        "WORKSTREAM_F2": len(f2_observations),
        "WORKSTREAM_F3": _workstream_store_count(
            "aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_store",
            "list_multi_customer_value_proof_records",
        ),
        "WORKSTREAM_F4": _workstream_store_count(
            "aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_store",
            "list_customer_scale_validation_records",
        ),
        "WORKSTREAM_F5": _workstream_store_count(
            "aethos_core.workstreams.commercial_validation_program.commercial_validation_program_store",
            "list_commercial_validation_records",
        ),
        "WORKSTREAM_F6": _workstream_store_count(
            "aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_store",
            "list_business_sustainability_records",
        ),
        "WORKSTREAM_F7": _workstream_store_count(
            "aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_store",
            "list_operating_model_records",
        ),
    }

    viability_signal = round((value_maturity + retention_maturity + adoption_maturity) / 3, 3)
    customer_score = round((adoption_maturity + value_maturity + retention_maturity) / 3, 3)
    commercial_score = round((viability_signal + min(1.0, sum(f_store_counts.values()) / 10)) / 2, 3)

    return {
        "report_id": "customer-commercial-maturity-report",
        "program_session_id": program_session_id,
        "adoption_maturity": adoption_maturity,
        "value_maturity": value_maturity,
        "retention_maturity": retention_maturity,
        "business_viability_maturity": viability_signal,
        "customer_maturity_score": customer_score,
        "commercial_maturity_score": commercial_score,
        "workstream_f1_through_f7_store_counts": f_store_counts,
        "workstream_g2_usage_adoption_reference": {"workstream": "WORKSTREAM_G2", "composed_read_only": True},
        "workstream_g3_revenue_density_reference": {"workstream": "WORKSTREAM_G3", "composed_read_only": True},
        "customer_commercial_maturity_demonstrated": customer_score > 0,
        "read_only": True,
    }


def build_evidence_trust_maturity_report(*, program_session_id: str) -> dict[str, Any]:
    density = build_evidence_density_report(program_session_id=program_session_id)
    freshness = build_evidence_freshness_report(program_session_id=program_session_id)
    trust = build_trust_maturity_report(program_session_id=program_session_id)

    evidence_score = round(
        (
            float(density.get("evidence_density_score") or 0)
            + float(freshness.get("evidence_freshness_score") or 0)
            + float(trust.get("trust_maturity_score") or 0)
        )
        / 3,
        3,
    )

    return {
        "report_id": "evidence-trust-maturity-report",
        "program_session_id": program_session_id,
        "evidence_density": density.get("evidence_density_score"),
        "trust_maturity": trust.get("trust_maturity_score"),
        "provenance_quality": density.get("real_evidence_count"),
        "freshness_quality": freshness.get("evidence_freshness_score"),
        "evidence_maturity_score": evidence_score,
        "workstream_g1_evidence_reference": {"workstream": "WORKSTREAM_G1", "composed_read_only": True},
        "trust_promotion_performed": False,
        "evidence_trust_maturity_demonstrated": evidence_score > 0,
        "read_only": True,
    }


def build_platform_gap_registry(*, program_session_id: str) -> dict[str, Any]:
    architecture = build_architecture_maturity_report(program_session_id=program_session_id)
    execution = build_execution_maturity_report(program_session_id=program_session_id)
    operational = build_operational_maturity_report(program_session_id=program_session_id)
    customer = build_customer_commercial_maturity_report(program_session_id=program_session_id)
    evidence = build_evidence_trust_maturity_report(program_session_id=program_session_id)
    inventory = build_platform_inventory_registry(program_session_id=program_session_id)

    gaps: list[dict[str, Any]] = []

    if architecture.get("coverage", 0) < 1.0:
        gaps.append(
            {
                "category": "maturity_gap",
                "detail": "FIX 300–330 module coverage incomplete",
                "severity": "medium",
            }
        )
    if execution.get("execution_maturity_score", 0) < 0.8:
        gaps.append(
            {
                "category": "operational_gap",
                "detail": "Execution track reliability below enterprise threshold",
                "severity": "medium",
            }
        )
    if operational.get("operational_maturity_score", 0) < 0.5:
        gaps.append(
            {
                "category": "operational_gap",
                "detail": "Operational or provider proof coverage limited",
                "severity": "high",
            }
        )
    if customer.get("adoption_maturity", 0) < 0.5:
        gaps.append(
            {
                "category": "adoption_gap",
                "detail": "Customer adoption maturity below target",
                "severity": "medium",
            }
        )
    if evidence.get("evidence_maturity_score", 0) < 0.5:
        gaps.append(
            {
                "category": "evidence_gap",
                "detail": "Evidence density or trust maturity below target",
                "severity": "high",
            }
        )
    for fix in inventory.get("fix_300_330_modules") or []:
        if not fix.get("module_present"):
            gaps.append(
                {
                    "category": "maturity_gap",
                    "detail": f"Missing module for {fix.get('fix_id')}",
                    "severity": "low",
                }
            )

    return {
        "registry_id": "platform-gap-registry",
        "program_session_id": program_session_id,
        "gap_count": len(gaps),
        "maturity_gaps": [g for g in gaps if g.get("category") == "maturity_gap"],
        "operational_gaps": [g for g in gaps if g.get("category") == "operational_gap"],
        "adoption_gaps": [g for g in gaps if g.get("category") == "adoption_gap"],
        "evidence_gaps": [g for g in gaps if g.get("category") == "evidence_gap"],
        "gap_items": gaps[:25],
        "read_only": True,
    }


def _platform_maturity_level(*, overall_score: float) -> str:
    if overall_score >= 0.85:
        return "enterprise_mature"
    if overall_score >= 0.7:
        return "sustainable"
    if overall_score >= 0.55:
        return "adopted"
    if overall_score >= 0.4:
        return "operational"
    return "foundational"


def compute_platform_maturity_metrics(*, program_session_id: str) -> dict[str, Any]:
    architecture = build_architecture_maturity_report(program_session_id=program_session_id)
    execution = build_execution_maturity_report(program_session_id=program_session_id)
    operational = build_operational_maturity_report(program_session_id=program_session_id)
    customer = build_customer_commercial_maturity_report(program_session_id=program_session_id)
    evidence = build_evidence_trust_maturity_report(program_session_id=program_session_id)

    architecture_score = float(architecture.get("architecture_maturity_score") or 0)
    execution_score = float(execution.get("execution_maturity_score") or 0)
    operational_score = float(operational.get("operational_maturity_score") or 0)
    customer_score = float(customer.get("customer_maturity_score") or 0)
    commercial_score = float(customer.get("commercial_maturity_score") or 0)
    evidence_score = float(evidence.get("evidence_maturity_score") or 0)

    overall = round(
        (
            architecture_score
            + execution_score
            + operational_score
            + customer_score
            + commercial_score
            + evidence_score
        )
        / 6,
        3,
    )

    return {
        "architecture_maturity_score": architecture_score,
        "execution_maturity_score": execution_score,
        "operational_maturity_score": operational_score,
        "customer_maturity_score": customer_score,
        "commercial_maturity_score": commercial_score,
        "evidence_maturity_score": evidence_score,
        "overall_platform_maturity_score": overall,
        "platform_maturity_level": _platform_maturity_level(overall_score=overall),
        "read_only": True,
    }
