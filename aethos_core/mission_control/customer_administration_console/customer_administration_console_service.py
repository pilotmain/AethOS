# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_306_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_evaluator import (
    normalize_commercial_plan,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
    ADMINISTRATION_AUTHORITY_FIX_306,
    ADMINISTRATION_DOMAINS,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306,
    AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
    BILLING_MUTATION_AUTHORITY_FIX_306,
    CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306,
    CUSTOMER_ADMINISTRATION_COMPOSES_EVIDENCE_ONLY_FIX_306,
    CUSTOMER_ADMINISTRATION_CONSOLE_FIX,
    CUSTOMER_ADMINISTRATION_CONSOLE_INVARIANT,
    CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_306,
    FORBIDDEN_ADMINISTRATION_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_306,
    HUMAN_ADMINISTRATION_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_306,
    TRUST_MUTATION_AUTHORITY_FIX_306,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_evaluator import (
    admin_surface_access,
    evaluate_administration_access,
    governance_administration_rows,
    role_administration_rows,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
    has_administration_decision_approve,
    list_customer_administration_console_records,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.orgs.members import get_member_role, list_members
from aethos_core.orgs.organizations import get_current_organization, list_organizations
from aethos_core.orgs.workspaces import list_workspaces


@dataclass(frozen=True)
class CustomerAdministrationConsoleResult:
    ok: bool
    session_id: str
    customer_administration_console: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_user(*, session_id: str) -> str:
    sid = (session_id or "default").strip()[:64] or "default"
    return sid if sid != "default" else "default"


def build_customer_administration_console(*, session_id: str) -> CustomerAdministrationConsoleResult:
    sid = (session_id or "default").strip()[:64] or "default"
    user_id = _resolve_user(session_id=sid)
    records = list_customer_administration_console_records()

    tenant = build_multi_tenant_platform_foundation(session_id=sid)
    identity = build_identity_access_hardening(session_id=sid)
    provider = build_provider_connection_experience(session_id=sid)
    channel = build_channel_integration_foundation(session_id=sid)
    billing = build_billing_entitlements_foundation(session_id=sid)

    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    members = list_members(org_id=org_id)
    workspaces = list_workspaces(org_id=org_id)
    organizations = list_organizations()

    admin_access = evaluate_administration_access(role=role, requester_org_id=org_id)
    surface_access = admin_surface_access(role=role, requester_org_id=org_id)

    tenant_sections = (tenant.multi_tenant_platform_foundation.get("sections") or {})
    org_registry = (tenant_sections.get("organization_registry") or [{}])[0]
    provider_sections = (provider.provider_connection_experience.get("sections") or {})
    channel_sections = (channel.channel_integration_foundation.get("sections") or {})
    billing_sections = (billing.billing_entitlements_foundation.get("sections") or {})
    identity_sections = (identity.identity_access_hardening.get("sections") or {})

    provider_dashboard = (provider_sections.get("provider_connection_dashboard") or [{}])[0]
    channel_dashboard = (channel_sections.get("channel_dashboard") or [{}])[0]
    billing_dashboard = (billing_sections.get("billing_dashboard") or [{}])[0]
    subscription = (billing_sections.get("subscription_registry") or [{}])[0]
    governance_action = (identity_sections.get("governance_action_report") or [{}])[0]

    commercial_plan = normalize_commercial_plan(str(current_org.get("plan") or "free"))
    cross_tenant_blocked = all(
        str(org.get("org_id") or "") == org_id
        for org in organizations
        if evaluate_administration_access(
            role=role,
            requester_org_id=org_id,
            target_org_id=str(org.get("org_id") or ""),
        )["allowed"]
        or str(org.get("org_id") or "") == org_id
    )

    organization_administration = [
        {
            "report_id": "organization-administration-report",
            "organization_id": org_id,
            "organization_name": current_org.get("name"),
            "organization_profile": {
                "plan": current_org.get("plan"),
                "commercial_plan": commercial_plan,
                "tenant_isolated": current_org.get("tenant_isolated", True),
            },
            "trust_status": "independent_trust_and_evidence",
            "subscription_status": subscription.get("status", "active"),
            "workspace_count": len(workspaces),
            "project_count": len(workspaces),
            "member_count": len(members),
            "organization_registry_composed": bool(org_registry),
            "read_only": True,
        }
    ]

    user_administration = [
        {
            "report_id": "user-administration-report",
            "organization_id": org_id,
            "admin_access_required": True,
            "admin_access_allowed": admin_access["allowed"],
            "users": [
                {
                    "user_id": member.get("user_id"),
                    "role": member.get("role"),
                    "status": "active",
                    "membership_id": member.get("member_id"),
                }
                for member in members
            ],
            "membership_count": len(members),
            "automatic_user_creation_enabled": False,
            "read_only": True,
        }
    ]

    role_administration = [
        {
            "report_id": "role-administration-report",
            "organization_id": org_id,
            "admin_access_required": True,
            "admin_access_allowed": admin_access["allowed"],
            "roles": role_administration_rows(),
            "automatic_permission_granting_enabled": False,
            "read_only": True,
        }
    ]

    workspace_administration = [
        {
            "report_id": "workspace-administration-report",
            "organization_id": org_id,
            "workspaces": [
                {
                    "workspace_id": ws.get("workspace_id"),
                    "name": ws.get("name"),
                    "status": ws.get("status"),
                    "repo_hint": ws.get("repo_hint"),
                    "ownership": org_id,
                    "activity": "active" if ws.get("status") == "active" else "unknown",
                }
                for ws in workspaces
            ],
            "workspace_count": len(workspaces),
            "read_only": True,
        }
    ]

    project_administration = [
        {
            "report_id": "project-administration-report",
            "organization_id": org_id,
            "projects": [
                {
                    "project_id": ws.get("workspace_id"),
                    "name": ws.get("name"),
                    "repository": ws.get("repo_hint"),
                    "trust_state": "governed_evidence_first",
                    "lifecycle_status": ws.get("status", "active"),
                }
                for ws in workspaces
            ],
            "project_count": len(workspaces),
            "read_only": True,
        }
    ]

    provider_administration = [
        {
            "report_id": "provider-administration-report",
            "composed_from_fix_303": True,
            "admin_access_required": True,
            "admin_access_allowed": admin_access["allowed"],
            "connected_providers": provider_dashboard.get("connected_provider_count", 0),
            "phase_1_providers": provider_dashboard.get("phase_1_providers") or [],
            "readiness_summary": provider_dashboard.get("readiness_summary") or [],
            "permission_gaps": provider_dashboard.get("permission_gaps") or [],
            "capability_unlocks": (
                (provider_sections.get("provider_capability_unlock_matrix") or [{}])[0].get("providers") or []
            ),
            "automatic_provider_mutation_enabled": False,
            "read_only": True,
        }
    ]

    channel_administration = [
        {
            "report_id": "channel-administration-report",
            "composed_from_fix_304": True,
            "connected_channels": channel_dashboard.get("connected_channels", 0),
            "total_channels": channel_dashboard.get("total_channels", 0),
            "readiness_summary": channel_dashboard.get("readiness_summary") or [],
            "identity_mapping_health": channel_dashboard.get("identity_mapping_health"),
            "authorization_health": channel_dashboard.get("authorization_health"),
            "read_only": True,
        }
    ]

    billing_administration = [
        {
            "report_id": "billing-administration-report",
            "composed_from_fix_305": True,
            "admin_access_required": True,
            "admin_access_allowed": admin_access["allowed"],
            "plan": billing_dashboard.get("plan"),
            "usage": billing_dashboard.get("usage") or {},
            "limits": billing_dashboard.get("limits") or {},
            "entitlements": (billing_sections.get("entitlement_registry") or [{}])[0].get("features") or [],
            "limit_consumption": billing_dashboard.get("limit_consumption") or {},
            "billing_mutation_authority": False,
            "read_only": True,
        }
    ]

    governance_administration = [
        {
            "report_id": "governance-administration-report",
            "admin_access_required": True,
            "admin_access_allowed": admin_access["allowed"],
            "approvals": [row for row in governance_administration_rows(role=role, org_id=org_id) if row["action"] == "approval_recording"],
            "trust_decisions": [row for row in governance_administration_rows(role=role, org_id=org_id) if row["action"] == "trust_decision"],
            "merge_decisions": [row for row in governance_administration_rows(role=role, org_id=org_id) if row["action"] == "merge_decision"],
            "deploy_decisions": [row for row in governance_administration_rows(role=role, org_id=org_id) if row["action"] == "deploy_decision"],
            "rollback_decisions": [row for row in governance_administration_rows(role=role, org_id=org_id) if row["action"] == "rollback_decision"],
            "governance_actions": governance_action.get("actions") or [],
            "trust_mutation_authority": False,
            "read_only": True,
        }
    ]

    customer_administration_dashboard = [
        {
            "dashboard_id": "customer-administration-dashboard",
            "organization_id": org_id,
            "requester_role": role,
            "admin_access_allowed": admin_access["allowed"],
            "surface_access": surface_access,
            "organization_health": "active",
            "user_health": f"{len(members)} members",
            "provider_health": f"{provider_dashboard.get('connected_provider_count', 0)} connected",
            "channel_health": f"{channel_dashboard.get('connected_channels', 0)}/{channel_dashboard.get('total_channels', 0)}",
            "billing_health": commercial_plan,
            "governance_health": "permission_checked",
            "cross_tenant_administration_blocked": cross_tenant_blocked,
            "read_only": True,
        }
    ]

    sections = {
        "organization_administration_report": organization_administration,
        "user_administration_report": user_administration,
        "role_administration_report": role_administration,
        "workspace_administration_report": workspace_administration,
        "project_administration_report": project_administration,
        "provider_administration_report": provider_administration,
        "channel_administration_report": channel_administration,
        "billing_administration_report": billing_administration,
        "governance_administration_report": governance_administration,
        "customer_administration_dashboard": customer_administration_dashboard,
        "human_administration_review": [
            {
                "review_id": "human-administration-review",
                "decisions_supported": list(HUMAN_ADMINISTRATION_DECISION_KINDS),
                "administration_decision_approve": has_administration_decision_approve(session_id=sid),
                "automatic_user_creation_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_administration_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_ADMINISTRATION_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION,
        "fix": CUSTOMER_ADMINISTRATION_CONSOLE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_306,
        "execution_performed": EXECUTION_PERFORMED_FIX_306,
        "customer_administration_compose_artifacts_only": CUSTOMER_ADMINISTRATION_COMPOSES_EVIDENCE_ONLY_FIX_306,
        "administration_authority": ADMINISTRATION_AUTHORITY_FIX_306,
        "automatic_user_creation_enabled": AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
        "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306,
        "cross_tenant_administration_enabled": CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_306,
        "billing_mutation_authority": BILLING_MUTATION_AUTHORITY_FIX_306,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_306,
        "invariant": CUSTOMER_ADMINISTRATION_CONSOLE_INVARIANT,
        "session_id": sid,
        "requester_user_id": user_id,
        "requester_role": role,
        "administration_access": admin_access,
        "administration_domains": list(ADMINISTRATION_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "administration_decision_approve": has_administration_decision_approve(session_id=sid),
        "fix_306_certification_requirements": list(FIX_306_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_tenant_context": bool(tenant.ok),
            "composes_fix_302_authorization": bool(identity.ok),
            "composes_fix_303_provider_context": bool(provider.ok),
            "composes_fix_304_channel_context": bool(channel.ok),
            "composes_fix_305_billing_context": bool(billing.ok),
            "automatic_user_creation_performed": False,
            "automatic_permission_granting_performed": False,
            "cross_tenant_administration_performed": False,
        },
    }

    return CustomerAdministrationConsoleResult(
        ok=True,
        session_id=sid,
        customer_administration_console=payload,
        detail="Customer administration console composed (visibility ≠ authority, no automatic mutations).",
    )
