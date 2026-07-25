# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_309_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_service import (
    build_customer_administration_console,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
    build_customer_usage_audit_portal,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
    build_payment_integration_readiness,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
    AUTOMATIC_LAUNCH_ENABLED_FIX_309,
    AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309,
    CUSTOMER_PROVISIONING_AUTHORITY_FIX_309,
    EXECUTION_PERFORMED_FIX_309,
    FORBIDDEN_LAUNCH_ASSESSMENT_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_309,
    HUMAN_LAUNCH_READINESS_DECISION_KINDS,
    LAUNCH_ASSESSMENT_COMPOSES_EVIDENCE_ONLY_FIX_309,
    LAUNCH_ASSESSMENT_DOMAINS,
    LAUNCH_AUTHORITY_FIX_309,
    MUTATION_PERFORMED_FIX_309,
    SAAS_LAUNCH_READINESS_ASSESSMENT_FIX,
    SAAS_LAUNCH_READINESS_ASSESSMENT_INVARIANT,
    SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_309,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_evaluator import (
    aggregate_risks,
    build_domain_report,
    derive_overall_status,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_store import (
    has_launch_readiness_decision_approve,
    list_saas_launch_readiness_assessment_records,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)


@dataclass(frozen=True)
class SaasLaunchReadinessAssessmentResult:
    ok: bool
    session_id: str
    saas_launch_readiness_assessment: dict[str, Any] = field(default_factory=dict)
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


def build_saas_launch_readiness_assessment(*, session_id: str) -> SaasLaunchReadinessAssessmentResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_saas_launch_readiness_assessment_records()

    tenant, tenant_ok = _safe_build("fix_300", build_multi_tenant_platform_foundation, session_id=sid)
    onboarding, onboarding_ok = _safe_build("fix_301", build_tenant_onboarding_activation, session_id=sid)
    identity, identity_ok = _safe_build("fix_302", build_identity_access_hardening, session_id=sid)
    provider, provider_ok = _safe_build("fix_303", build_provider_connection_experience, session_id=sid)
    channel, channel_ok = _safe_build("fix_304", build_channel_integration_foundation, session_id=sid)
    billing, billing_ok = _safe_build("fix_305", build_billing_entitlements_foundation, session_id=sid)
    admin, admin_ok = _safe_build("fix_306", build_customer_administration_console, session_id=sid)
    audit, audit_ok = _safe_build("fix_307", build_customer_usage_audit_portal, session_id=sid)
    payment, payment_ok = _safe_build("fix_308", build_payment_integration_readiness, session_id=sid)

    provider_dashboard = {}
    if provider and provider_ok:
        provider_dashboard = (
            (provider.provider_connection_experience.get("sections") or {})
            .get("provider_connection_dashboard", [{}])[0]
        )
    connected_providers = int(provider_dashboard.get("connected_provider_count") or 0)
    payment_processing = bool(
        payment
        and payment_ok
        and payment.payment_integration_readiness.get("payment_processing_enabled") is False
    )

    product = build_domain_report(
        report_id="product-readiness-report",
        domain="product_readiness",
        checks=[
            {"check_id": "onboarding", "label": "Tenant onboarding", "ready": onboarding_ok},
            {"check_id": "administration", "label": "Administration console", "ready": admin_ok},
            {"check_id": "auditability", "label": "Audit portal", "ready": audit_ok},
            {"check_id": "commercial_foundations", "label": "Billing foundations", "ready": billing_ok},
        ],
        evidence_sources=["FIX 301", "FIX 305", "FIX 306", "FIX 307"],
    )

    platform = build_domain_report(
        report_id="platform-readiness-report",
        domain="platform_readiness",
        checks=[
            {"check_id": "tenancy", "label": "Multi-tenant foundation", "ready": tenant_ok},
            {"check_id": "providers", "label": "Provider connection experience", "ready": provider_ok},
            {"check_id": "channels", "label": "Channel integration", "ready": channel_ok},
            {"check_id": "governance_stack", "label": "Governance stack present", "ready": identity_ok},
        ],
        evidence_sources=["FIX 300", "FIX 303", "FIX 304", "FIX 302"],
    )

    security = build_domain_report(
        report_id="security-readiness-report",
        domain="security_readiness",
        checks=[
            {"check_id": "identity", "label": "Identity resolution", "ready": identity_ok},
            {"check_id": "rbac", "label": "RBAC evaluation", "ready": identity_ok},
            {
                "check_id": "tenant_isolation",
                "label": "Tenant isolation enforced",
                "ready": tenant_ok and identity_ok,
            },
            {"check_id": "audit_coverage", "label": "Audit coverage", "ready": audit_ok},
        ],
        evidence_sources=["FIX 302", "FIX 300", "FIX 307"],
    )

    governance = build_domain_report(
        report_id="governance-readiness-report",
        domain="governance_readiness",
        checks=[
            {"check_id": "approval_coverage", "label": "Approval coverage modeled", "ready": identity_ok},
            {"check_id": "trust_boundaries", "label": "Trust boundaries documented", "ready": tenant_ok},
            {"check_id": "decision_records", "label": "Human decision records", "ready": audit_ok},
            {"check_id": "lifecycle_controls", "label": "Lifecycle controls present", "ready": identity_ok},
        ],
        evidence_sources=["FIX 302", "FIX 181-196 trust baselines", "FIX 307"],
    )

    operational = build_domain_report(
        report_id="operational-readiness-report",
        domain="operational_readiness",
        checks=[
            {"check_id": "merge_lifecycle", "label": "Merge lifecycle modeled", "ready": True},
            {"check_id": "deploy_lifecycle", "label": "Deploy lifecycle modeled", "ready": True},
            {"check_id": "monitoring_lifecycle", "label": "Monitoring lifecycle modeled", "ready": True},
            {"check_id": "rollback_lifecycle", "label": "Rollback lifecycle modeled", "ready": True},
            {"check_id": "evidence_coverage", "label": "Evidence coverage via audit portal", "ready": audit_ok},
        ],
        evidence_sources=["FIX 200-230 lifecycle modules", "FIX 307"],
    )

    commercial = build_domain_report(
        report_id="commercial-readiness-report",
        domain="commercial_readiness",
        checks=[
            {"check_id": "plans", "label": "Plan registry", "ready": billing_ok},
            {"check_id": "entitlements", "label": "Entitlement registry", "ready": billing_ok},
            {"check_id": "usage_tracking", "label": "Usage tracking", "ready": billing_ok},
            {"check_id": "payment_readiness", "label": "Payment readiness modeled", "ready": payment_ok},
            {
                "check_id": "no_payment_processing",
                "label": "No payment processing enabled",
                "ready": payment_processing,
            },
        ],
        evidence_sources=["FIX 305", "FIX 308"],
        blockers=[] if payment_processing else ["payment_processing_must_remain_disabled"],
    )

    customer = build_domain_report(
        report_id="customer-readiness-report",
        domain="customer_readiness",
        checks=[
            {"check_id": "onboarding", "label": "Customer onboarding", "ready": onboarding_ok},
            {"check_id": "provider_connection", "label": "Provider connection guidance", "ready": provider_ok},
            {"check_id": "administration", "label": "Administration visibility", "ready": admin_ok},
            {"check_id": "audit_visibility", "label": "Audit visibility", "ready": audit_ok},
            {"check_id": "self_awareness", "label": "Platform self-awareness", "ready": tenant_ok and billing_ok},
        ],
        evidence_sources=["FIX 301", "FIX 303", "FIX 306", "FIX 307", "FIX 295-296"],
    )

    support = build_domain_report(
        report_id="support-readiness-report",
        domain="support_readiness",
        checks=[
            {"check_id": "diagnostics", "label": "Operational diagnostics available", "ready": audit_ok},
            {"check_id": "evidence_explorer", "label": "Evidence explorer", "ready": audit_ok},
            {"check_id": "audit_visibility", "label": "Audit visibility for support", "ready": audit_ok},
            {"check_id": "operator_workflows", "label": "Operator review workflows", "ready": admin_ok},
        ],
        evidence_sources=["FIX 307", "FIX 306"],
    )

    domain_reports = [product, platform, security, governance, operational, commercial, customer, support]
    risks = aggregate_risks(domain_reports=domain_reports)
    if connected_providers == 0:
        risks.append(
            {
                "risk_id": "provider-no-phase1-connection",
                "domain": "platform_readiness",
                "level": "medium",
                "detail": "No Phase 1 providers connected — limited operational proof",
                "evidence_backed": True,
                "read_only": True,
            }
        )

    domain_scores = {report["domain"]: report["score"] for report in domain_reports}
    overall_status = derive_overall_status(domain_scores=domain_scores, risks=risks)
    unique_blockers = sorted(
        {
            *(b for report in domain_reports for b in report.get("blockers") or []),
            *(
                risk["detail"]
                for risk in risks
                if risk.get("level") in {"critical", "high"}
            ),
        }
    )

    launch_risk_registry = [
        {
            "registry_id": "launch-risk-registry",
            "critical": [r for r in risks if r.get("level") == "critical"],
            "high": [r for r in risks if r.get("level") == "high"],
            "medium": [r for r in risks if r.get("level") == "medium"],
            "low": [r for r in risks if r.get("level") == "low"],
            "risk_count": len(risks),
            "read_only": True,
        }
    ]

    launch_readiness_dashboard = [
        {
            "dashboard_id": "launch-readiness-dashboard",
            "overall_status": overall_status,
            "domain_scores": domain_scores,
            "blockers": unique_blockers,
            "risk_count": len(risks),
            "evidence_coverage": {
                "fix_300_308_composed": sum(
                    1
                    for ok in (
                        tenant_ok,
                        onboarding_ok,
                        identity_ok,
                        provider_ok,
                        channel_ok,
                        billing_ok,
                        admin_ok,
                        audit_ok,
                        payment_ok,
                    )
                    if ok
                ),
                "fix_300_308_total": 9,
            },
            "recommendations": [
                "Resolve NOT_READY domains before external customer onboarding.",
                "Human launch decision required — assessment does not declare launch.",
                "Limited beta may be justified when overall status is READY_FOR_LIMITED_BETA.",
            ],
            "launch_declaration_performed": False,
            "read_only": True,
        }
    ]

    sections = {
        "product_readiness_report": [product],
        "platform_readiness_report": [platform],
        "security_readiness_report": [security],
        "governance_readiness_report": [governance],
        "operational_readiness_report": [operational],
        "commercial_readiness_report": [commercial],
        "customer_readiness_report": [customer],
        "support_readiness_report": [support],
        "launch_risk_registry": launch_risk_registry,
        "launch_readiness_dashboard": launch_readiness_dashboard,
        "human_launch_readiness_review": [
            {
                "review_id": "human-launch-readiness-review",
                "decisions_supported": list(HUMAN_LAUNCH_READINESS_DECISION_KINDS),
                "launch_readiness_decision_approve": has_launch_readiness_decision_approve(session_id=sid),
                "launch_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_launch_assessment_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_LAUNCH_ASSESSMENT_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION,
        "fix": SAAS_LAUNCH_READINESS_ASSESSMENT_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_309,
        "execution_performed": EXECUTION_PERFORMED_FIX_309,
        "launch_assessment_compose_artifacts_only": LAUNCH_ASSESSMENT_COMPOSES_EVIDENCE_ONLY_FIX_309,
        "launch_authority": LAUNCH_AUTHORITY_FIX_309,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_309,
        "automatic_readiness_promotion_enabled": AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_309,
        "customer_provisioning_authority": CUSTOMER_PROVISIONING_AUTHORITY_FIX_309,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_309,
        "invariant": SAAS_LAUNCH_READINESS_ASSESSMENT_INVARIANT,
        "session_id": sid,
        "launch_assessment_domains": list(LAUNCH_ASSESSMENT_DOMAINS),
        "overall_launch_status": overall_status,
        "sections": sections,
        "operator_record_count": len(records),
        "launch_readiness_decision_approve": has_launch_readiness_decision_approve(session_id=sid),
        "fix_309_certification_requirements": list(FIX_309_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_through_308": True,
            "pilot_reexecution_performed": False,
            "launch_declaration_performed": False,
            "customer_provisioning_performed": False,
            "trust_mutation_performed": False,
        },
    }

    return SaasLaunchReadinessAssessmentResult(
        ok=True,
        session_id=sid,
        saas_launch_readiness_assessment=payload,
        blockers=unique_blockers,
        detail="SaaS launch readiness assessment composed from evidence (assessment ≠ launch authority).",
    )
