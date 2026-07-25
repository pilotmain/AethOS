# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_308_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    normalize_commercial_plan,
    upgrade_opportunities,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
    AUTOMATIC_CHARGING_ENABLED_FIX_308,
    AUTOMATIC_REFUND_ENABLED_FIX_308,
    BILLING_EVENT_TYPES,
    CREDIT_CARD_STORAGE_ENABLED_FIX_308,
    EXECUTION_PERFORMED_FIX_308,
    FORBIDDEN_PAYMENT_READINESS_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_308,
    HUMAN_PAYMENT_READINESS_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_308,
    PAYMENT_INTEGRATION_READINESS_FIX,
    PAYMENT_INTEGRATION_READINESS_INVARIANT,
    PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION,
    PAYMENT_PROCESSING_ENABLED_FIX_308,
    PAYMENT_READINESS_COMPOSES_EVIDENCE_ONLY_FIX_308,
    PAYMENT_READINESS_DOMAINS,
    SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_evaluator import (
    billing_event_model_rows,
    commercial_analytics,
    commercial_governance_gaps,
    payment_provider_readiness_rows,
    resolve_subscription_lifecycle_state,
    subscription_lifecycle_rows,
    usage_monetization_rows,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
    has_payment_readiness_decision_approve,
    list_payment_integration_readiness_records,
)
from aethos_core.orgs.members import get_member_role, list_members
from aethos_core.orgs.organizations import get_current_organization, list_organizations


@dataclass(frozen=True)
class PaymentIntegrationReadinessResult:
    ok: bool
    session_id: str
    payment_integration_readiness: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_payment_integration_readiness(*, session_id: str) -> PaymentIntegrationReadinessResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_payment_integration_readiness_records()

    billing = build_billing_entitlements_foundation(session_id=sid)
    billing_payload = billing.billing_entitlements_foundation
    billing_sections = (billing_payload.get("sections") or {})
    subscription = (billing_sections.get("subscription_registry") or [{}])[0]
    billing_dashboard = (billing_sections.get("billing_dashboard") or [{}])[0]
    usage_registry = (billing_sections.get("usage_registry") or [{}])[0]

    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    org_plan_raw = str(current_org.get("plan") or "free")
    commercial_plan = normalize_commercial_plan(org_plan_raw)
    trial_status = str(subscription.get("trial_status") or "none")
    usage = dict(usage_registry.get("usage") or billing_dashboard.get("usage") or {})
    members = list_members(org_id=org_id)
    owner = next((m for m in members if m.get("role") == "admin"), members[0] if members else None)
    lifecycle_state = resolve_subscription_lifecycle_state(
        commercial_plan=commercial_plan,
        trial_status=trial_status,
    )

    customer_billing_identity = [
        {
            "registry_id": "customer-billing-identity-registry",
            "organization_id": org_id,
            "organization_name": current_org.get("name"),
            "billing_identity": f"billing-{org_id}",
            "subscription_owner_user_id": (owner or {}).get("user_id"),
            "subscription_owner_role": (owner or {}).get("role"),
            "customer_reference": f"cust-{org_id}",
            "commercial_plan": commercial_plan,
            "provider_customer_reference": None,
            "read_only": True,
        }
    ]

    payment_provider_registry = [
        {
            "registry_id": "payment-provider-registry",
            "providers": payment_provider_readiness_rows(),
            "provider_count": len(payment_provider_readiness_rows()),
            "payment_processing_enabled": False,
            "read_only": True,
        }
    ]

    subscription_lifecycle_registry = [
        {
            "registry_id": "subscription-lifecycle-registry",
            "current_state": lifecycle_state,
            "states": subscription_lifecycle_rows(
                commercial_plan=commercial_plan,
                trial_status=trial_status,
            ),
            "subscription_mutation_authority": False,
            "read_only": True,
        }
    ]

    billing_event_registry = [
        {
            "registry_id": "billing-event-registry",
            "events": billing_event_model_rows(records=records),
            "event_types": list(BILLING_EVENT_TYPES),
            "payment_processing_enabled": False,
            "read_only": True,
        }
    ]

    invoice_readiness_registry = [
        {
            "registry_id": "invoice-readiness-registry",
            "invoice_generation_enabled": False,
            "billing_period": "monthly",
            "future_invoice_metadata": {
                "organization_id": org_id,
                "plan": commercial_plan,
                "currency": "USD",
                "line_items_from_usage": True,
            },
            "usage_summary": usage,
            "read_only": True,
        }
    ]

    usage_monetization_registry = [
        {
            "registry_id": "usage-monetization-registry",
            "composed_from_fix_305": True,
            "plan": commercial_plan,
            "categories": usage_monetization_rows(plan=commercial_plan, usage=usage),
            "limit_consumption": billing_dashboard.get("limit_consumption") or {},
            "read_only": True,
        }
    ]

    analytics = commercial_analytics(
        commercial_plan=commercial_plan,
        org_count=len(list_organizations()),
    )
    commercial_analytics_dashboard = [
        {
            "dashboard_id": "commercial-analytics-dashboard",
            "organization_id": org_id,
            **analytics,
        }
    ]

    upgrade_path_registry = [
        {
            "registry_id": "upgrade-path-registry",
            "current_plan": commercial_plan,
            "eligible_paths": upgrade_opportunities(plan=commercial_plan),
            "automatic_plan_upgrade_enabled": False,
            "read_only": True,
        }
    ]

    payment_readiness_dashboard = [
        {
            "dashboard_id": "payment-readiness-dashboard",
            "organization_id": org_id,
            "provider_readiness": "readiness_only_no_api_integration",
            "subscription_readiness": lifecycle_state,
            "invoice_readiness": "modeled_not_generated",
            "usage_readiness": "fix_305_composed",
            "payment_processing_enabled": False,
            "credit_card_storage_enabled": False,
            "read_only": True,
        }
    ]

    governance_gaps = commercial_governance_gaps(
        commercial_plan=commercial_plan,
        usage=usage,
        billing_identity_complete=bool(customer_billing_identity[0].get("customer_reference")),
    )
    commercial_governance_report = [
        {
            "report_id": "commercial-governance-report",
            "organization_id": org_id,
            "commercial_risks": governance_gaps,
            "missing_billing_data": [g for g in governance_gaps if "billing" in g.get("gap", "")],
            "missing_usage_data": [g for g in governance_gaps if "usage" in g.get("gap", "")],
            "missing_entitlement_data": [],
            "payment_processing_enabled": False,
            "read_only": True,
        }
    ]

    sections = {
        "customer_billing_identity_registry": customer_billing_identity,
        "payment_provider_registry": payment_provider_registry,
        "subscription_lifecycle_registry": subscription_lifecycle_registry,
        "billing_event_registry": billing_event_registry,
        "invoice_readiness_registry": invoice_readiness_registry,
        "usage_monetization_registry": usage_monetization_registry,
        "commercial_analytics_dashboard": commercial_analytics_dashboard,
        "upgrade_path_registry": upgrade_path_registry,
        "payment_readiness_dashboard": payment_readiness_dashboard,
        "commercial_governance_report": commercial_governance_report,
        "human_payment_readiness_review": [
            {
                "review_id": "human-payment-readiness-review",
                "decisions_supported": list(HUMAN_PAYMENT_READINESS_DECISION_KINDS),
                "payment_readiness_decision_approve": has_payment_readiness_decision_approve(session_id=sid),
                "payment_processing_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_payment_readiness_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PAYMENT_READINESS_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION,
        "fix": PAYMENT_INTEGRATION_READINESS_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_308,
        "execution_performed": EXECUTION_PERFORMED_FIX_308,
        "payment_readiness_compose_artifacts_only": PAYMENT_READINESS_COMPOSES_EVIDENCE_ONLY_FIX_308,
        "payment_processing_enabled": PAYMENT_PROCESSING_ENABLED_FIX_308,
        "credit_card_storage_enabled": CREDIT_CARD_STORAGE_ENABLED_FIX_308,
        "automatic_charging_enabled": AUTOMATIC_CHARGING_ENABLED_FIX_308,
        "automatic_refund_enabled": AUTOMATIC_REFUND_ENABLED_FIX_308,
        "subscription_mutation_authority": SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_308,
        "invariant": PAYMENT_INTEGRATION_READINESS_INVARIANT,
        "session_id": sid,
        "requester_role": get_member_role(org_id=org_id),
        "payment_readiness_domains": list(PAYMENT_READINESS_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "payment_readiness_decision_approve": has_payment_readiness_decision_approve(session_id=sid),
        "fix_308_certification_requirements": list(FIX_308_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_305_billing_entitlements": bool(billing.ok),
            "payment_collection_performed": False,
            "credit_card_storage_performed": False,
            "subscription_mutation_performed": False,
            "provider_api_mutation_performed": False,
        },
    }

    return PaymentIntegrationReadinessResult(
        ok=True,
        session_id=sid,
        payment_integration_readiness=payload,
        detail="Payment integration readiness composed (readiness ≠ processing, no payment authority).",
    )
