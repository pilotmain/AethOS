# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements foundation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_305_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
    AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
    AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305,
    BILLING_AUTHORITY_FIX_305,
    BILLING_DOMAINS,
    BILLING_ENTITLEMENTS_COMPOSES_EVIDENCE_ONLY_FIX_305,
    BILLING_ENTITLEMENTS_FOUNDATION_FIX,
    BILLING_ENTITLEMENTS_FOUNDATION_INVARIANT,
    BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_305,
    FORBIDDEN_BILLING_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_305,
    HUMAN_BILLING_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_305,
    PAYMENT_PROCESSING_ENABLED_FIX_305,
    PLANS,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    free_blocked_from_enterprise_entitlements,
    normalize_commercial_plan,
    plan_capabilities,
    plan_channels,
    plan_limits,
    plan_providers,
    plan_registry_rows,
    upgrade_opportunities,
    usage_within_limits,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
    has_billing_decision_approve,
    list_billing_entitlements_foundation_records,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.orgs.organizations import get_current_organization, list_organizations
from aethos_core.orgs.workspaces import list_workspaces


@dataclass(frozen=True)
class BillingEntitlementsFoundationResult:
    ok: bool
    session_id: str
    billing_entitlements_foundation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _usage_snapshot(*, org_id: str) -> dict[str, int]:
    organizations = list_organizations()
    workspaces = list_workspaces(org_id=org_id)
    return {
        "organizations": len(organizations),
        "workspaces": len(workspaces),
        "projects": len(workspaces),
        "repositories": len({w.get("repo_hint") for w in workspaces if w.get("repo_hint")}),
        "executions": 0,
        "storage_mb": 0,
        "ai_consumption_units": 0,
    }


def build_billing_entitlements_foundation(*, session_id: str) -> BillingEntitlementsFoundationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_billing_entitlements_foundation_records()

    tenant = build_multi_tenant_platform_foundation(session_id=sid)
    build_channel_integration_foundation(session_id=sid)
    build_provider_connection_experience(session_id=sid)

    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    org_plan_raw = str(current_org.get("plan") or "free")
    commercial_plan = normalize_commercial_plan(org_plan_raw)
    usage = _usage_snapshot(org_id=org_id)
    limits = plan_limits(commercial_plan)
    limit_report = usage_within_limits(plan=commercial_plan, usage=usage)
    blocked_enterprise = free_blocked_from_enterprise_entitlements(plan=commercial_plan)

    plan_registry = [
        {
            "registry_id": "plan-registry",
            "plans": plan_registry_rows(),
            "plan_count": len(PLANS),
            "read_only": True,
        }
    ]

    created_at = current_org.get("created_at")
    subscription_registry = [
        {
            "registry_id": "subscription-registry",
            "organization_id": org_id,
            "organization_name": current_org.get("name"),
            "org_plan_raw": org_plan_raw,
            "commercial_plan": commercial_plan,
            "status": "active",
            "start_date": created_at,
            "renewal_date": None,
            "trial_status": "none" if commercial_plan != "FREE" else "eligible",
            "automatic_subscription_creation_enabled": False,
            "read_only": True,
        }
    ]

    entitlement_registry = [
        {
            "registry_id": "entitlement-registry",
            "plan": commercial_plan,
            "features": list(plan_capabilities(commercial_plan)),
            "limits": limits,
            "capabilities": list(plan_capabilities(commercial_plan)),
            "provider_access": list(plan_providers(commercial_plan)),
            "channel_access": list(plan_channels(commercial_plan)),
            "enterprise_only_blocked": blocked_enterprise,
            "entitlements_not_authority": True,
            "read_only": True,
        }
    ]

    usage_registry = [
        {
            "registry_id": "usage-registry",
            "organization_id": org_id,
            "usage": usage,
            "metrics_tracked": [
                "organizations",
                "workspaces",
                "projects",
                "repositories",
                "executions",
                "storage",
                "ai_consumption",
            ],
            "read_only": True,
        }
    ]

    capability_entitlement_matrix = [
        {
            "matrix_id": "capability-entitlement-matrix",
            "plans": [
                {"plan": plan, "capabilities": list(plan_capabilities(plan)), "read_only": True}
                for plan in PLANS
            ],
            "read_only": True,
        }
    ]

    channel_entitlement_matrix = [
        {
            "matrix_id": "channel-entitlement-matrix",
            "plans": [
                {"plan": plan, "channels": list(plan_channels(plan)), "read_only": True}
                for plan in PLANS
            ],
            "read_only": True,
        }
    ]

    provider_entitlement_matrix = [
        {
            "matrix_id": "provider-entitlement-matrix",
            "plans": [
                {"plan": plan, "providers": list(plan_providers(plan)), "read_only": True}
                for plan in PLANS
            ],
            "read_only": True,
        }
    ]

    usage_limit_report = [
        {
            "report_id": "usage-limit-report",
            "plan": commercial_plan,
            "limits": limits,
            "usage": usage,
            "consumption": limit_report,
            "read_only": True,
        }
    ]

    billing_readiness = [
        {
            "report_id": "billing-readiness-report",
            "subscription_status": "active",
            "trial_status": subscription_registry[0]["trial_status"],
            "entitlements": list(plan_capabilities(commercial_plan)),
            "limit_consumption": limit_report,
            "payment_processing_enabled": False,
            "billing_authority": False,
            "read_only": True,
        }
    ]

    billing_dashboard = [
        {
            "dashboard_id": "billing-dashboard",
            "plan": commercial_plan,
            "org_plan_raw": org_plan_raw,
            "entitlements": entitlement_registry[0],
            "usage": usage,
            "limits": limits,
            "limit_consumption": limit_report,
            "upgrade_opportunities": upgrade_opportunities(plan=commercial_plan),
            "subscription": subscription_registry[0],
            "payment_processing_enabled": False,
            "automatic_plan_upgrade_enabled": False,
            "automatic_plan_downgrade_enabled": False,
            "read_only": True,
        }
    ]

    sections = {
        "plan_registry": plan_registry,
        "subscription_registry": subscription_registry,
        "entitlement_registry": entitlement_registry,
        "usage_registry": usage_registry,
        "capability_entitlement_matrix": capability_entitlement_matrix,
        "channel_entitlement_matrix": channel_entitlement_matrix,
        "provider_entitlement_matrix": provider_entitlement_matrix,
        "usage_limit_report": usage_limit_report,
        "billing_readiness_report": billing_readiness,
        "billing_dashboard": billing_dashboard,
        "human_billing_review": [
            {
                "review_id": "human-billing-review",
                "decisions_supported": list(HUMAN_BILLING_DECISION_KINDS),
                "billing_decision_approve": has_billing_decision_approve(session_id=sid),
                "payment_processing_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_billing_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_BILLING_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION,
        "fix": BILLING_ENTITLEMENTS_FOUNDATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_305,
        "execution_performed": EXECUTION_PERFORMED_FIX_305,
        "billing_entitlements_compose_artifacts_only": BILLING_ENTITLEMENTS_COMPOSES_EVIDENCE_ONLY_FIX_305,
        "billing_authority": BILLING_AUTHORITY_FIX_305,
        "automatic_subscription_creation_enabled": AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305,
        "automatic_plan_upgrade_enabled": AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
        "automatic_plan_downgrade_enabled": AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305,
        "payment_processing_enabled": PAYMENT_PROCESSING_ENABLED_FIX_305,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_305,
        "invariant": BILLING_ENTITLEMENTS_FOUNDATION_INVARIANT,
        "session_id": sid,
        "billing_domains": list(BILLING_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "billing_decision_approve": has_billing_decision_approve(session_id=sid),
        "fix_305_certification_requirements": list(FIX_305_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_tenant_context": bool(tenant.ok),
            "composes_fix_304_channel_context": True,
            "composes_fix_303_provider_context": True,
            "payment_collection_performed": False,
            "subscription_mutation_performed": False,
            "automatic_plan_change_performed": False,
        },
    }

    return BillingEntitlementsFoundationResult(
        ok=True,
        session_id=sid,
        billing_entitlements_foundation=payload,
        detail="Billing & entitlements foundation composed (entitlements ≠ authority, no payment processing).",
    )
