# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_310_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_service import (
    build_customer_administration_console,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
    AUTOMATIC_ESCALATION_ENABLED_FIX_310,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310,
    AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310,
    CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
    CUSTOMER_SUPPORT_COMPOSES_EVIDENCE_ONLY_FIX_310,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_FIX,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_INVARIANT,
    CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_310,
    FORBIDDEN_SUPPORT_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_310,
    HUMAN_SUPPORT_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_310,
    SUPPORT_DOMAINS,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_evaluator import (
    aggregate_support_analytics,
    classify_risks,
    derive_opportunities,
    score_customer_health,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_store import (
    has_support_review_decision_approve,
    list_customer_support_success_foundation_records,
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
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)
from aethos_core.orgs.organizations import get_current_organization, list_organizations
from aethos_core.orgs.workspaces import list_workspaces


@dataclass(frozen=True)
class CustomerSupportSuccessFoundationResult:
    ok: bool
    session_id: str
    customer_support_success_foundation: dict[str, Any] = field(default_factory=dict)
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


def build_customer_support_success_foundation(
    *,
    session_id: str,
) -> CustomerSupportSuccessFoundationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_customer_support_success_foundation_records()

    tenant, tenant_ok = _safe_build("fix_300", build_multi_tenant_platform_foundation, session_id=sid)
    onboarding, onboarding_ok = _safe_build("fix_301", build_tenant_onboarding_activation, session_id=sid)
    identity, identity_ok = _safe_build("fix_302", build_identity_access_hardening, session_id=sid)
    provider, provider_ok = _safe_build("fix_303", build_provider_connection_experience, session_id=sid)
    channel, channel_ok = _safe_build("fix_304", build_channel_integration_foundation, session_id=sid)
    billing, billing_ok = _safe_build("fix_305", build_billing_entitlements_foundation, session_id=sid)
    admin, admin_ok = _safe_build("fix_306", build_customer_administration_console, session_id=sid)
    audit, audit_ok = _safe_build("fix_307", build_customer_usage_audit_portal, session_id=sid)
    payment, payment_ok = _safe_build("fix_308", build_payment_integration_readiness, session_id=sid)
    launch, launch_ok = _safe_build("fix_309", build_saas_launch_readiness_assessment, session_id=sid)
    capability, capability_ok = _safe_build("fix_295", build_autonomous_capability_registry, session_id=sid)

    provider_dashboard = {}
    if provider and provider_ok:
        provider_dashboard = (
            (provider.provider_connection_experience.get("sections") or {})
            .get("provider_connection_dashboard", [{}])[0]
        )
    connected_providers = int(provider_dashboard.get("connected_provider_count") or 0)

    onboarding_sections = (onboarding.tenant_onboarding_activation.get("sections") or {}) if onboarding and onboarding_ok else {}
    onboarding_dashboard = (onboarding_sections.get("onboarding_dashboard") or [{}])[0] if onboarding_sections else {}
    onboarding_complete = bool(onboarding_dashboard.get("onboarding_complete"))

    channel_sections = (channel.channel_integration_foundation.get("sections") or {}) if channel and channel_ok else {}
    channel_dashboard = (channel_sections.get("channel_dashboard") or [{}])[0] if channel_sections else {}
    channel_integrated = int(channel_dashboard.get("integrated_channel_count") or 0) > 0

    billing_sections = (billing.billing_entitlements_foundation.get("sections") or {}) if billing and billing_ok else {}
    billing_dashboard = (billing_sections.get("billing_dashboard") or [{}])[0] if billing_sections else {}
    billing_active = bool(billing_dashboard.get("subscription_active"))

    launch_board = launch.saas_launch_readiness_assessment if launch and launch_ok else {}
    launch_status = str(launch_board.get("overall_launch_status") or "UNKNOWN")
    launch_dashboard = (
        (launch_board.get("sections") or {}).get("launch_readiness_dashboard", [{}])[0]
        if launch_board
        else {}
    )

    capability_board = capability.autonomous_capability_registry if capability and capability_ok else {}
    capability_registry = (
        (capability_board.get("sections") or {}).get("capability_registry", [{}])[0]
        if capability_board
        else {}
    )
    capability_count = int(capability_registry.get("capability_count") or 0)

    organizations = list_organizations()
    current_org = get_current_organization()
    current_org_id = str(current_org.get("org_id") or "")

    health_rows: list[dict[str, Any]] = []
    all_risks: list[dict[str, Any]] = []
    all_opportunities: list[dict[str, Any]] = []
    all_escalations: list[dict[str, Any]] = []

    for org in organizations:
        org_id = str(org.get("org_id") or "")
        org_name = str(org.get("name") or org_id or "unknown")
        workspaces = list_workspaces(org_id=org_id)
        member_count = int(org.get("member_count") or 1)
        plan = str(org.get("plan") or "free").lower()
        permission_issues = not identity_ok

        health_status = score_customer_health(
            onboarding_ready=onboarding_ok and (onboarding_complete or org_id == current_org_id),
            provider_ready=provider_ok and connected_providers > 0,
            channel_ready=channel_ok and channel_integrated,
            billing_ready=billing_ok and billing_active,
            workspace_count=len(workspaces),
            member_count=member_count,
            plan=plan,
        )

        health_rows.append(
            {
                "org_id": org_id,
                "org_name": org_name,
                "health_status": health_status,
                "workspace_count": len(workspaces),
                "member_count": member_count,
                "plan": plan,
                "adoption_signals": {
                    "onboarding_ready": onboarding_ok,
                    "provider_connected": connected_providers > 0,
                    "channels_integrated": channel_integrated,
                    "billing_active": billing_active,
                },
                "platform_engagement": {
                    "audit_visible": audit_ok,
                    "admin_visible": admin_ok,
                },
                "read_only": True,
            }
        )

        org_risks = classify_risks(
            org_id=org_id,
            org_name=org_name,
            health_status=health_status,
            onboarding_ready=onboarding_ok and onboarding_complete,
            provider_ready=provider_ok and connected_providers > 0,
            billing_ready=billing_ok and billing_active,
            permission_issues=permission_issues,
        )
        all_risks.extend(org_risks)

        for risk in org_risks:
            if risk.get("level") in {"critical", "high"}:
                all_escalations.append(
                    {
                        "escalation_id": f"esc-{risk['risk_id']}",
                        "org_id": org_id,
                        "org_name": org_name,
                        "severity": risk.get("level"),
                        "detail": risk.get("detail"),
                        "resolution_status": "open",
                        "read_only": True,
                    }
                )

        all_opportunities.extend(
            derive_opportunities(
                org_id=org_id,
                org_name=org_name,
                health_status=health_status,
                plan=plan,
                onboarding_ready=onboarding_ok and onboarding_complete,
                provider_ready=provider_ok and connected_providers > 0,
            )
        )

    healthy = [row for row in health_rows if row.get("health_status") in {"HEALTHY", "HIGH_VALUE"}]
    at_risk = [row for row in health_rows if row.get("health_status") == "AT_RISK"]
    new_customers = [row for row in health_rows if row.get("health_status") == "NEW"]
    high_value = [row for row in health_rows if row.get("health_status") == "HIGH_VALUE"]

    support_requests = [
        {
            "request_id": f"record-{idx}",
            "kind": record.get("kind"),
            "content": record.get("content"),
            "session_id": record.get("session_id"),
            "recorded_at": record.get("recorded_at"),
            "status": "recorded",
            "read_only": True,
        }
        for idx, record in enumerate(records)
    ]

    customer_health_registry = [
        {
            "registry_id": "customer-health-registry",
            "organizations": health_rows,
            "organization_count": len(health_rows),
            "read_only": True,
        }
    ]

    customer_success_dashboard = [
        {
            "dashboard_id": "customer-success-dashboard",
            "healthy_customers": healthy,
            "at_risk_customers": at_risk,
            "new_customers": new_customers,
            "high_value_customers": high_value,
            "healthy_count": len(healthy),
            "at_risk_count": len(at_risk),
            "new_count": len(new_customers),
            "high_value_count": len(high_value),
            "read_only": True,
        }
    ]

    support_request_registry = [
        {
            "registry_id": "support-request-registry",
            "requests": support_requests,
            "request_count": len(support_requests),
            "escalation_records": [
                record
                for record in records
                if str(record.get("kind") or "").startswith("support_review_decision_")
            ],
            "read_only": True,
        }
    ]

    customer_adoption_report = [
        {
            "report_id": "customer-adoption-report",
            "checks": [
                {"check_id": "onboarding", "label": "Tenant onboarding (FIX 301)", "ready": onboarding_ok},
                {"check_id": "providers", "label": "Provider connection (FIX 303)", "ready": provider_ok},
                {"check_id": "channels", "label": "Channel integration (FIX 304)", "ready": channel_ok},
                {"check_id": "billing", "label": "Billing foundations (FIX 305)", "ready": billing_ok},
            ],
            "connected_provider_count": connected_providers,
            "integrated_channel_count": int(channel_dashboard.get("integrated_channel_count") or 0),
            "onboarding_complete": onboarding_complete,
            "evidence_sources": ["FIX 301", "FIX 303", "FIX 304", "FIX 305"],
            "read_only": True,
        }
    ]

    customer_trust_report = [
        {
            "report_id": "customer-trust-report",
            "capability_count": capability_count,
            "capability_registry_ready": capability_ok,
            "launch_readiness_status": launch_status,
            "launch_readiness_ready": launch_ok,
            "evidence_coverage": launch_dashboard.get("evidence_coverage") or {},
            "trust_explanations": [
                "Capability registry composes FIX 295 self-awareness evidence.",
                "Launch readiness composes FIX 309 assessment without launch authority.",
            ],
            "evidence_sources": ["FIX 295", "FIX 309"],
            "read_only": True,
        }
    ]

    customer_risk_registry = [
        {
            "registry_id": "customer-risk-registry",
            "risks": all_risks,
            "risk_count": len(all_risks),
            "categories": {
                "low_adoption": [r for r in all_risks if r.get("category") == "low_adoption"],
                "permission_issue": [r for r in all_risks if r.get("category") == "permission_issue"],
                "provider_readiness_gap": [
                    r for r in all_risks if r.get("category") == "provider_readiness_gap"
                ],
                "billing_concern": [r for r in all_risks if r.get("category") == "billing_concern"],
            },
            "read_only": True,
        }
    ]

    customer_escalation_registry = [
        {
            "registry_id": "customer-escalation-registry",
            "escalations": all_escalations,
            "open_count": sum(1 for row in all_escalations if row.get("resolution_status") == "open"),
            "read_only": True,
        }
    ]

    success_opportunity_registry = [
        {
            "registry_id": "success-opportunity-registry",
            "opportunities": all_opportunities,
            "opportunity_count": len(all_opportunities),
            "by_type": {
                "upsell": [o for o in all_opportunities if o.get("type") == "upsell"],
                "adoption": [o for o in all_opportunities if o.get("type") == "adoption"],
                "training": [o for o in all_opportunities if o.get("type") == "training"],
            },
            "read_only": True,
        }
    ]

    analytics = aggregate_support_analytics(
        health_rows=health_rows,
        risks=all_risks,
        escalations=all_escalations,
        records=records,
    )
    support_analytics_dashboard = [
        {
            "dashboard_id": "support-analytics-dashboard",
            **analytics,
            "adoption_trend": {
                "onboarding_ready": onboarding_ok,
                "provider_ready": provider_ok,
                "channel_ready": channel_ok,
                "billing_ready": billing_ok,
            },
        }
    ]

    customer_support_success_dashboard = [
        {
            "dashboard_id": "customer-support-success-dashboard",
            "healthy_count": len(healthy),
            "at_risk_count": len(at_risk),
            "new_customer_count": len(new_customers),
            "high_value_count": len(high_value),
            "risk_count": len(all_risks),
            "open_escalation_count": analytics.get("open_escalation_count", 0),
            "opportunity_count": len(all_opportunities),
            "launch_readiness_status": launch_status,
            "evidence_coverage": {
                "fix_300_309_composed": sum(
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
                        launch_ok,
                    )
                    if ok
                ),
                "fix_300_309_total": 10,
            },
            "recommendations": [
                "Review at-risk customers before external beta onboarding.",
                "Human support review required — visibility ≠ intervention.",
                "Use support note and customer success note for operator records only.",
            ],
            "customer_contact_performed": False,
            "ticket_execution_performed": False,
            "read_only": True,
        }
    ]

    sections = {
        "customer_health_registry": customer_health_registry,
        "customer_success_dashboard": customer_success_dashboard,
        "support_request_registry": support_request_registry,
        "customer_adoption_report": customer_adoption_report,
        "customer_trust_report": customer_trust_report,
        "customer_risk_registry": customer_risk_registry,
        "customer_escalation_registry": customer_escalation_registry,
        "success_opportunity_registry": success_opportunity_registry,
        "support_analytics_dashboard": support_analytics_dashboard,
        "customer_support_success_dashboard": customer_support_success_dashboard,
        "human_support_review": [
            {
                "review_id": "human-support-review",
                "decisions_supported": list(HUMAN_SUPPORT_DECISION_KINDS),
                "support_review_decision_approve": has_support_review_decision_approve(session_id=sid),
                "customer_support_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_support_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_SUPPORT_ACTIONS
        ],
    }

    blockers = sorted(
        {
            risk["detail"]
            for risk in all_risks
            if risk.get("level") in {"critical", "high"}
        }
    )

    payload: dict[str, Any] = {
        "schema_version": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION,
        "fix": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_310,
        "execution_performed": EXECUTION_PERFORMED_FIX_310,
        "customer_support_compose_artifacts_only": CUSTOMER_SUPPORT_COMPOSES_EVIDENCE_ONLY_FIX_310,
        "customer_support_authority": CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
        "automatic_customer_contact_enabled": AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
        "automatic_escalation_enabled": AUTOMATIC_ESCALATION_ENABLED_FIX_310,
        "automatic_support_resolution_enabled": AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310,
        "automatic_plan_upgrade_enabled": AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_310,
        "invariant": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_INVARIANT,
        "session_id": sid,
        "support_domains": list(SUPPORT_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "support_review_decision_approve": has_support_review_decision_approve(session_id=sid),
        "fix_310_certification_requirements": list(FIX_310_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_through_309": True,
            "capability_registry_composed": capability_ok,
            "launch_readiness_composed": launch_ok,
            "customer_contact_performed": False,
            "ticket_execution_performed": False,
            "provider_mutation_performed": False,
            "subscription_mutation_performed": False,
        },
    }

    return CustomerSupportSuccessFoundationResult(
        ok=True,
        session_id=sid,
        customer_support_success_foundation=payload,
        blockers=blockers,
        detail="Customer support & success foundation composed from evidence (visibility ≠ authority).",
    )
