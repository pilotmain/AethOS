# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_312_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312,
    AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
    AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312,
    AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312,
    BETA_AUTHORITY_FIX_312,
    BETA_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_312,
    BETA_PROGRAM_DOMAINS,
    EXECUTION_PERFORMED_FIX_312,
    FORBIDDEN_BETA_PROGRAM_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_312,
    HUMAN_BETA_ADMISSION_DECISION_KINDS,
    HUMAN_BETA_LAUNCH_DECISION_KINDS,
    LIMITED_BETA_LAUNCH_PROGRAM_FIX,
    LIMITED_BETA_LAUNCH_PROGRAM_INVARIANT,
    LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_312,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_evaluator import (
    aggregate_success_metrics,
    classify_beta_risks,
    derive_beta_launch_recommendation,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
    has_beta_admission_review_decision_approve,
    has_beta_launch_review_decision_approve,
    list_limited_beta_launch_program_records,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
    build_public_product_experience,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)
from aethos_core.orgs.organizations import list_organizations


@dataclass(frozen=True)
class LimitedBetaLaunchProgramResult:
    ok: bool
    session_id: str
    limited_beta_launch_program: dict[str, Any] = field(default_factory=dict)
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


def build_limited_beta_launch_program(*, session_id: str) -> LimitedBetaLaunchProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_limited_beta_launch_program_records()

    launch, launch_ok = _safe_build("fix_309", build_saas_launch_readiness_assessment, session_id=sid)
    support, support_ok = _safe_build(
        "fix_310", build_customer_support_success_foundation, session_id=sid
    )
    public, public_ok = _safe_build("fix_311", build_public_product_experience, session_id=sid)

    launch_board = _payload(launch, "saas_launch_readiness_assessment")
    overall_launch_status = str(launch_board.get("overall_launch_status") or "UNKNOWN")
    launch_blockers = list(launch_board.get("blockers") or [])
    launch_dashboard = (launch_board.get("sections") or {}).get("launch_readiness_dashboard", [{}])[0]

    support_board = _payload(support, "customer_support_success_foundation")
    support_dashboard = (support_board.get("sections") or {}).get(
        "customer_support_success_dashboard", [{}]
    )[0]
    support_risk_registry = (support_board.get("sections") or {}).get("customer_risk_registry", [{}])[0]
    support_risks = list(support_risk_registry.get("risks") or [])
    healthy_count = int(support_dashboard.get("healthy_count") or 0)
    at_risk_count = int(support_dashboard.get("at_risk_count") or 0)

    public_board = _payload(public, "public_product_experience")
    public_dashboard = (public_board.get("sections") or {}).get("public_product_dashboard", [{}])[0]

    organizations = list_organizations()
    org_count = len(organizations)

    admission_records = [
        record
        for record in records
        if str(record.get("kind") or "").startswith("beta_admission_review_decision_")
    ]
    admission_approve_count = sum(
        1 for record in admission_records if record.get("kind") == "beta_admission_review_decision_approve"
    )
    feedback_records = [
        record
        for record in records
        if record.get("kind") in {"beta_candidate_note", "limited_beta_launch_program_record"}
    ]

    cohorts = [
        {
            "cohort_id": "cohort-limited-beta-1",
            "cohort_name": "Limited Beta Cohort 1",
            "goal": "Validate onboarding, provider connection, and first governed workflow",
            "target_size": 10,
            "current_size": min(org_count, 10),
            "status": "ACTIVE" if launch_ok and overall_launch_status != "BLOCKED" else "PLANNED",
            "read_only": True,
        },
        {
            "cohort_id": "cohort-design-partners",
            "cohort_name": "Design Partners",
            "goal": "Collect product and usability feedback before expansion",
            "target_size": 5,
            "current_size": min(org_count, 5),
            "status": "PLANNED",
            "read_only": True,
        },
    ]

    candidates = [
        {
            "candidate_id": f"candidate-{org.get('org_id')}",
            "org_id": org.get("org_id"),
            "org_name": org.get("name"),
            "evaluation_status": "EVALUATED",
            "approval_status": "PENDING_HUMAN_REVIEW",
            "plan": org.get("plan"),
            "read_only": True,
        }
        for org in organizations
    ]

    beta_cohort_registry = [
        {
            "registry_id": "beta-cohort-registry",
            "cohorts": cohorts,
            "cohort_count": len(cohorts),
            "active_cohort_count": sum(1 for row in cohorts if row.get("status") == "ACTIVE"),
            "read_only": True,
        }
    ]

    beta_candidate_registry = [
        {
            "registry_id": "beta-candidate-registry",
            "candidates": candidates,
            "candidate_count": len(candidates),
            "read_only": True,
        }
    ]

    beta_admission_review_registry = [
        {
            "registry_id": "beta-admission-review-registry",
            "admission_requests": [
                {
                    "request_id": f"admission-{idx}",
                    "kind": record.get("kind"),
                    "content": record.get("content"),
                    "recorded_at": record.get("recorded_at"),
                    "status": "recorded",
                    "read_only": True,
                }
                for idx, record in enumerate(admission_records)
            ],
            "review_history": admission_records,
            "admission_review_decision_approve": has_beta_admission_review_decision_approve(session_id=sid),
            "read_only": True,
        }
    ]

    beta_readiness_report = [
        {
            "report_id": "beta-readiness-report",
            "overall_launch_status": overall_launch_status,
            "checks": [
                {
                    "check_id": "launch_assessment",
                    "label": "Launch readiness (FIX 309)",
                    "ready": launch_ok and overall_launch_status != "BLOCKED",
                },
                {
                    "check_id": "customer_success",
                    "label": "Customer success readiness (FIX 310)",
                    "ready": support_ok,
                },
                {
                    "check_id": "public_product",
                    "label": "Public product experience (FIX 311)",
                    "ready": public_ok,
                },
                {
                    "check_id": "human_admission",
                    "label": "Human admission review recorded",
                    "ready": has_beta_admission_review_decision_approve(session_id=sid),
                },
            ],
            "launch_blockers": launch_blockers,
            "evidence_coverage": launch_dashboard.get("evidence_coverage") or {},
            "evidence_sources": ["FIX 309", "FIX 310", "FIX 311"],
            "read_only": True,
        }
    ]

    feedback_items = [
        {
            "feedback_id": f"feedback-{idx}",
            "category": "product"
            if "product" in str(record.get("content") or "").lower()
            else "usability"
            if "usability" in str(record.get("content") or "").lower()
            else "capability"
            if "capability" in str(record.get("content") or "").lower()
            else "trust",
            "content": record.get("content"),
            "recorded_at": record.get("recorded_at"),
            "read_only": True,
        }
        for idx, record in enumerate(feedback_records)
    ]

    beta_feedback_registry = [
        {
            "registry_id": "beta-feedback-registry",
            "feedback_items": feedback_items,
            "feedback_count": len(feedback_items),
            "categories": {
                "product": [row for row in feedback_items if row.get("category") == "product"],
                "usability": [row for row in feedback_items if row.get("category") == "usability"],
                "capability": [row for row in feedback_items if row.get("category") == "capability"],
                "trust": [row for row in feedback_items if row.get("category") == "trust"],
            },
            "read_only": True,
        }
    ]

    beta_risks = classify_beta_risks(
        launch_blockers=launch_blockers,
        support_risks=support_risks,
        launch_status=overall_launch_status,
    )
    beta_risk_registry = [
        {
            "registry_id": "beta-risk-registry",
            "risks": beta_risks,
            "risk_count": len(beta_risks),
            "categories": {
                "product": [r for r in beta_risks if r.get("category") == "product"],
                "operational": [r for r in beta_risks if r.get("category") == "operational"],
                "adoption": [r for r in beta_risks if r.get("category") == "adoption"],
                "governance": [r for r in beta_risks if r.get("category") == "governance"],
            },
            "read_only": True,
        }
    ]

    success_metrics = aggregate_success_metrics(
        org_count=max(org_count, 1),
        healthy_count=healthy_count,
        onboarding_ready=public_ok,
        provider_ready=launch_ok,
        connected_providers=1 if launch_ok else 0,
        channel_ready=launch_ok,
        audit_ready=support_ok,
    )
    beta_success_metrics = [{"metrics_id": "beta-success-metrics", **success_metrics}]

    beta_operations_dashboard = [
        {
            "dashboard_id": "beta-operations-dashboard",
            "active_cohort_count": sum(1 for row in cohorts if row.get("status") == "ACTIVE"),
            "active_participant_count": org_count,
            "open_risk_count": len([r for r in beta_risks if r.get("level") in {"critical", "high"}]),
            "candidate_count": len(candidates),
            "feedback_count": len(feedback_items),
            **success_metrics,
            "read_only": True,
        }
    ]

    beta_evidence_registry = [
        {
            "registry_id": "beta-evidence-registry",
            "readiness_evidence": {
                "launch_status": overall_launch_status,
                "launch_ready": launch_ok,
                "support_ready": support_ok,
                "public_ready": public_ok,
            },
            "feedback_evidence": {"feedback_count": len(feedback_items)},
            "success_evidence": success_metrics,
            "operational_evidence": {
                "proven_capabilities": public_dashboard.get("proven_capability_count"),
                "trust_baselines": public_dashboard.get("trust_baseline_count"),
            },
            "read_only": True,
        }
    ]

    recommendation = derive_beta_launch_recommendation(
        overall_launch_status=overall_launch_status,
        at_risk_count=at_risk_count,
        risk_count=len(beta_risks),
        healthy_count=healthy_count,
        admission_approve_count=admission_approve_count,
        feedback_count=len(feedback_items),
    )

    beta_launch_recommendation = [
        {
            "recommendation_id": "beta-launch-recommendation",
            "recommendation": recommendation,
            "rationale": (
                "Derived from FIX 309 launch status, FIX 310 customer health, "
                "admission reviews, and feedback evidence — not automatic launch."
            ),
            "automatic_launch_performed": False,
            "customer_provisioning_performed": False,
            "read_only": True,
        }
    ]

    sections = {
        "beta_cohort_registry": beta_cohort_registry,
        "beta_candidate_registry": beta_candidate_registry,
        "beta_admission_review_registry": beta_admission_review_registry,
        "beta_readiness_report": beta_readiness_report,
        "beta_feedback_registry": beta_feedback_registry,
        "beta_risk_registry": beta_risk_registry,
        "beta_success_metrics": beta_success_metrics,
        "beta_operations_dashboard": beta_operations_dashboard,
        "beta_evidence_registry": beta_evidence_registry,
        "beta_launch_recommendation": beta_launch_recommendation,
        "human_beta_review": [
            {
                "review_id": "human-beta-review",
                "admission_decisions_supported": list(HUMAN_BETA_ADMISSION_DECISION_KINDS),
                "launch_decisions_supported": list(HUMAN_BETA_LAUNCH_DECISION_KINDS),
                "beta_admission_review_decision_approve": has_beta_admission_review_decision_approve(
                    session_id=sid
                ),
                "beta_launch_review_decision_approve": has_beta_launch_review_decision_approve(session_id=sid),
                "beta_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_beta_program_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_BETA_PROGRAM_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION,
        "fix": LIMITED_BETA_LAUNCH_PROGRAM_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_312,
        "execution_performed": EXECUTION_PERFORMED_FIX_312,
        "beta_program_compose_artifacts_only": BETA_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_312,
        "beta_authority": BETA_AUTHORITY_FIX_312,
        "automatic_user_admission_enabled": AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312,
        "automatic_customer_provisioning_enabled": AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
        "automatic_plan_assignment_enabled": AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_312,
        "invariant": LIMITED_BETA_LAUNCH_PROGRAM_INVARIANT,
        "session_id": sid,
        "beta_program_domains": list(BETA_PROGRAM_DOMAINS),
        "beta_launch_recommendation": recommendation,
        "sections": sections,
        "operator_record_count": len(records),
        "beta_admission_review_decision_approve": has_beta_admission_review_decision_approve(session_id=sid),
        "beta_launch_review_decision_approve": has_beta_launch_review_decision_approve(session_id=sid),
        "fix_312_certification_requirements": list(FIX_312_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_through_311": True,
            "user_provisioning_performed": False,
            "entitlement_mutation_performed": False,
            "subscription_mutation_performed": False,
            "trust_mutation_performed": False,
            "automatic_beta_expansion_performed": False,
            "automatic_launch_performed": False,
        },
    }

    return LimitedBetaLaunchProgramResult(
        ok=True,
        session_id=sid,
        limited_beta_launch_program=payload,
        blockers=launch_blockers,
        detail="Limited beta launch program composed from evidence (management ≠ provisioning authority).",
    )
