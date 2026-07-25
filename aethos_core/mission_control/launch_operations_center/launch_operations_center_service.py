# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_313_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
    build_governed_deploy_lifecycle,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
    build_governed_merge_lifecycle,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
    build_governed_monitoring_lifecycle,
)
from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
    build_governed_rollback_lifecycle,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313,
    AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313,
    AUTOMATIC_LAUNCH_ENABLED_FIX_313,
    AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313,
    EXECUTION_PERFORMED_FIX_313,
    FORBIDDEN_LAUNCH_OPERATIONS_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_313,
    HUMAN_LAUNCH_OPERATIONS_DECISION_KINDS,
    LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
    LAUNCH_OPERATIONS_CENTER_FIX,
    LAUNCH_OPERATIONS_CENTER_INVARIANT,
    LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION,
    LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_313,
    LAUNCH_OPERATIONS_DOMAINS,
    MUTATION_PERFORMED_FIX_313,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_evaluator import (
    aggregate_blockers,
    aggregate_risks,
    derive_launch_phase,
    derive_launch_recommendation,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_store import (
    has_launch_operations_review_decision_approve,
    list_launch_operations_center_records,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
    build_limited_beta_launch_program,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
    build_public_product_experience,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)


@dataclass(frozen=True)
class LaunchOperationsCenterResult:
    ok: bool
    session_id: str
    launch_operations_center: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _safe_build(name: str, builder, *, session_id: str) -> tuple[Any, bool]:
    try:
        result = builder(session_id=session_id)
        return result, bool(getattr(result, "ok", True))
    except Exception:
        return None, False


def _payload(result: Any, attr: str) -> dict[str, Any]:
    if not result:
        return {}
    value = getattr(result, attr, None)
    return value if isinstance(value, dict) else {}


def build_launch_operations_center(*, session_id: str) -> LaunchOperationsCenterResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_launch_operations_center_records()

    launch, launch_ok = _safe_build("fix_309", build_saas_launch_readiness_assessment, session_id=sid)
    support, support_ok = _safe_build("fix_310", build_customer_support_success_foundation, session_id=sid)
    public, public_ok = _safe_build("fix_311", build_public_product_experience, session_id=sid)
    beta, beta_ok = _safe_build("fix_312", build_limited_beta_launch_program, session_id=sid)
    provider, provider_ok = _safe_build("fix_303", build_provider_connection_experience, session_id=sid)
    merge, merge_ok = _safe_build("fix_200", build_governed_merge_lifecycle, session_id=sid)
    deploy, deploy_ok = _safe_build("fix_210", build_governed_deploy_lifecycle, session_id=sid)
    monitoring, monitoring_ok = _safe_build("fix_220", build_governed_monitoring_lifecycle, session_id=sid)
    rollback, rollback_ok = _safe_build("fix_230", build_governed_rollback_lifecycle, session_id=sid)

    launch_board = _payload(launch, "saas_launch_readiness_assessment")
    overall_launch_status = str(launch_board.get("overall_launch_status") or "UNKNOWN")
    launch_blockers = list(launch_board.get("blockers") or [])
    launch_risk_registry = (launch_board.get("sections") or {}).get("launch_risk_registry", [{}])[0]
    launch_risks = [
        {**row, "source": "FIX 309"}
        for row in (launch_risk_registry.get("critical") or [])
        + (launch_risk_registry.get("high") or [])
        + (launch_risk_registry.get("medium") or [])
    ]

    support_board = _payload(support, "customer_support_success_foundation")
    support_dashboard = (support_board.get("sections") or {}).get(
        "customer_support_success_dashboard", [{}]
    )[0]
    support_risk_registry = (support_board.get("sections") or {}).get("customer_risk_registry", [{}])[0]
    customer_risks = [{**row, "source": "FIX 310"} for row in (support_risk_registry.get("risks") or [])]
    healthy_count = int(support_dashboard.get("healthy_count") or 0)
    at_risk_count = int(support_dashboard.get("at_risk_count") or 0)
    open_escalations = int(support_dashboard.get("open_escalation_count") or 0)
    customer_blockers = [
        risk["detail"]
        for risk in customer_risks
        if risk.get("level") in {"critical", "high"} and risk.get("detail")
    ]

    beta_board = _payload(beta, "limited_beta_launch_program")
    beta_recommendation = str(beta_board.get("beta_launch_recommendation") or "DO_NOT_LAUNCH")
    beta_blockers = list(beta_board.get("blockers") or [])
    beta_ops = (beta_board.get("sections") or {}).get("beta_operations_dashboard", [{}])[0]
    beta_monitor = (beta_board.get("sections") or {}).get("beta_cohort_registry", [{}])[0]
    beta_feedback = (beta_board.get("sections") or {}).get("beta_feedback_registry", [{}])[0]
    beta_metrics = (beta_board.get("sections") or {}).get("beta_success_metrics", [{}])[0]
    beta_risk_registry = (beta_board.get("sections") or {}).get("beta_risk_registry", [{}])[0]
    beta_risks = [{**row, "source": "FIX 312"} for row in (beta_risk_registry.get("risks") or [])]

    public_board = _payload(public, "public_product_experience")

    provider_board = _payload(provider, "provider_connection_experience")
    provider_sections = provider_board.get("sections") or {}
    provider_dashboard = (provider_sections.get("provider_connection_dashboard") or [{}])[0]
    provider_matrix = (provider_sections.get("provider_readiness_matrix") or [{}])[0]
    providers = list(provider_matrix.get("providers") or provider_dashboard.get("providers") or [])

    operational_blockers: list[str] = []
    lifecycle_checks = [
        ("merge", merge_ok),
        ("deploy", deploy_ok),
        ("monitoring", monitoring_ok),
        ("rollback", rollback_ok),
    ]
    for name, ok in lifecycle_checks:
        if not ok:
            operational_blockers.append(f"{name}_lifecycle_evidence_unavailable")

    platform_healthy = all(ok for _, ok in lifecycle_checks)
    current_phase = derive_launch_phase(
        overall_launch_status=overall_launch_status,
        beta_recommendation=beta_recommendation,
    )

    all_blockers = aggregate_blockers(
        launch_blockers=launch_blockers,
        beta_blockers=beta_blockers,
        operational_blockers=operational_blockers,
        customer_blockers=customer_blockers,
    )
    risk_buckets = aggregate_risks(
        launch_risks=launch_risks,
        beta_risks=beta_risks,
        customer_risks=customer_risks,
    )
    all_risks_flat = [
        row
        for bucket in risk_buckets.values()
        for row in bucket
    ]
    critical_risk_count = sum(1 for row in all_risks_flat if row.get("level") == "critical")

    recommendation = derive_launch_recommendation(
        overall_launch_status=overall_launch_status,
        beta_recommendation=beta_recommendation,
        blocker_count=len(all_blockers),
        critical_risk_count=critical_risk_count,
        at_risk_count=at_risk_count,
        healthy_count=healthy_count,
        platform_healthy=platform_healthy,
    )

    review_status = (
        "HUMAN_REVIEW_APPROVED"
        if has_launch_operations_review_decision_approve(session_id=sid)
        else "PENDING_HUMAN_REVIEW"
    )

    launch_status_registry = [
        {
            "registry_id": "launch-status-registry",
            "current_launch_phase": current_phase,
            "readiness_status": overall_launch_status,
            "beta_status": beta_recommendation,
            "review_status": review_status,
            "read_only": True,
        }
    ]

    launch_blocker_registry = [
        {
            "registry_id": "launch-blocker-registry",
            "blockers": all_blockers,
            "blocker_count": len(all_blockers),
            "read_only": True,
        }
    ]

    launch_risk_dashboard = [
        {
            "dashboard_id": "launch-risk-dashboard",
            **risk_buckets,
            "risk_count": len(all_risks_flat),
            "critical_risk_count": critical_risk_count,
            "read_only": True,
        }
    ]

    beta_operations_monitor = [
        {
            "monitor_id": "beta-operations-monitor",
            "cohorts": beta_monitor.get("cohorts") or [],
            "active_cohort_count": beta_ops.get("active_cohort_count", 0),
            "feedback_count": beta_feedback.get("feedback_count", 0),
            "activation_rate": beta_metrics.get("activation_rate", 0),
            "customer_health_score": beta_metrics.get("customer_health_score", 0),
            "beta_recommendation": beta_recommendation,
            "evidence_sources": ["FIX 312"],
            "read_only": True,
        }
    ]

    customer_operations_monitor = [
        {
            "monitor_id": "customer-operations-monitor",
            "healthy_count": healthy_count,
            "at_risk_count": at_risk_count,
            "open_escalation_count": open_escalations,
            "risk_count": len(customer_risks),
            "adoption_ready": support_ok,
            "evidence_sources": ["FIX 310"],
            "read_only": True,
        }
    ]

    platform_operations_monitor = [
        {
            "monitor_id": "platform-operations-monitor",
            "delivery_health": merge_ok,
            "deploy_health": deploy_ok,
            "monitoring_health": monitoring_ok,
            "recovery_health": rollback_ok,
            "platform_healthy": platform_healthy,
            "evidence_sources": ["FIX 200-230"],
            "read_only": True,
        }
    ]

    provider_operations_monitor = [
        {
            "monitor_id": "provider-operations-monitor",
            "connected_provider_count": int(provider_dashboard.get("connected_provider_count") or 0),
            "providers": providers[:8],
            "github_ready": provider_ok,
            "railway_ready": provider_ok,
            "vercel_ready": provider_ok,
            "planned_providers": [p for p in providers if str(p.get("status", "")).upper() != "CONNECTED"][:4],
            "evidence_sources": ["FIX 303"],
            "read_only": True,
        }
    ]

    launch_evidence_registry = [
        {
            "registry_id": "launch-evidence-registry",
            "readiness_evidence": {
                "launch_status": overall_launch_status,
                "launch_ready": launch_ok,
            },
            "beta_evidence": {
                "beta_recommendation": beta_recommendation,
                "beta_ready": beta_ok,
            },
            "trust_evidence": {
                "public_ready": public_ok,
                "trust_baseline_count": (
                    (public_board.get("sections") or {})
                    .get("trust_explorer", [{}])[0]
                    .get("baseline_count")
                ),
            },
            "operational_evidence": {
                "platform_healthy": platform_healthy,
                "provider_ready": provider_ok,
            },
            "read_only": True,
        }
    ]

    launch_recommendation = [
        {
            "recommendation_id": "launch-recommendation",
            "recommendation": recommendation,
            "rationale": (
                "Derived from FIX 309 readiness, FIX 312 beta signals, FIX 310 customer health, "
                "and FIX 200-230 platform lifecycle — not launch execution."
            ),
            "launch_execution_performed": False,
            "read_only": True,
        }
    ]

    launch_operations_dashboard = [
        {
            "dashboard_id": "launch-operations-dashboard",
            "current_launch_phase": current_phase,
            "launch_recommendation": recommendation,
            "readiness_status": overall_launch_status,
            "beta_status": beta_recommendation,
            "blocker_count": len(all_blockers),
            "critical_risk_count": critical_risk_count,
            "healthy_count": healthy_count,
            "at_risk_count": at_risk_count,
            "platform_healthy": platform_healthy,
            "active_cohort_count": beta_ops.get("active_cohort_count", 0),
            "recommendations": [
                "Resolve launch blockers before expanding beta or public review.",
                "Human launch decision required — operations center observes only.",
                "Monitor customer health and platform lifecycle signals continuously.",
            ],
            "launch_execution_performed": False,
            "read_only": True,
        }
    ]

    sections = {
        "launch_status_registry": launch_status_registry,
        "launch_blocker_registry": launch_blocker_registry,
        "launch_risk_dashboard": launch_risk_dashboard,
        "beta_operations_monitor": beta_operations_monitor,
        "customer_operations_monitor": customer_operations_monitor,
        "platform_operations_monitor": platform_operations_monitor,
        "provider_operations_monitor": provider_operations_monitor,
        "launch_evidence_registry": launch_evidence_registry,
        "launch_recommendation": launch_recommendation,
        "launch_operations_dashboard": launch_operations_dashboard,
        "human_launch_operations_review": [
            {
                "review_id": "human-launch-operations-review",
                "decisions_supported": list(HUMAN_LAUNCH_OPERATIONS_DECISION_KINDS),
                "launch_operations_review_decision_approve": has_launch_operations_review_decision_approve(
                    session_id=sid
                ),
                "launch_operations_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_launch_operations_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_LAUNCH_OPERATIONS_ACTIONS
        ],
    }

    unique_blockers = sorted({row["detail"] for row in all_blockers if row.get("detail")})

    payload: dict[str, Any] = {
        "schema_version": LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION,
        "fix": LAUNCH_OPERATIONS_CENTER_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_313,
        "execution_performed": EXECUTION_PERFORMED_FIX_313,
        "launch_operations_compose_artifacts_only": LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_313,
        "launch_operations_authority": LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_313,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313,
        "automatic_customer_admission_enabled": AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313,
        "automatic_provider_mutation_enabled": AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_313,
        "invariant": LAUNCH_OPERATIONS_CENTER_INVARIANT,
        "session_id": sid,
        "launch_operations_domains": list(LAUNCH_OPERATIONS_DOMAINS),
        "launch_recommendation": recommendation,
        "current_launch_phase": current_phase,
        "sections": sections,
        "operator_record_count": len(records),
        "launch_operations_review_decision_approve": has_launch_operations_review_decision_approve(
            session_id=sid
        ),
        "fix_313_certification_requirements": list(FIX_313_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_309_through_312_and_lifecycle": True,
            "launch_execution_performed": False,
            "customer_provisioning_performed": False,
            "beta_expansion_performed": False,
            "provider_mutation_performed": False,
            "operational_mutation_performed": False,
        },
    }

    return LaunchOperationsCenterResult(
        ok=True,
        session_id=sid,
        launch_operations_center=payload,
        blockers=unique_blockers,
        detail="Launch operations center composed from evidence (visibility ≠ launch authority).",
    )
