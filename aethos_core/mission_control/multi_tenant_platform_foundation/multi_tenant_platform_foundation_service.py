# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.governance.governance_friction_approval_contract import FIX_300_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
    AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
    CROSS_TENANT_ACCESS_ENABLED_FIX_300,
    CROSS_TENANT_TRUST_ENABLED_FIX_300,
    DEPLOYMENT_AUTHORITY_FIX_300,
    EXECUTION_PERFORMED_FIX_300,
    FORBIDDEN_TENANT_PLATFORM_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_300,
    GOVERNANCE_MUTATION_PERFORMED_FIX_300,
    HUMAN_TENANT_DECISION_KINDS,
    MERGE_AUTHORITY_FIX_300,
    MULTI_TENANT_PLATFORM_COMPOSES_EVIDENCE_ONLY_FIX_300,
    MULTI_TENANT_PLATFORM_FOUNDATION_FIX,
    MULTI_TENANT_PLATFORM_FOUNDATION_INVARIANT,
    MULTI_TENANT_PLATFORM_FOUNDATION_PRINCIPLES,
    MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_300,
    PERMISSION_ESCALATION_ENABLED_FIX_300,
    PROVIDER_MUTATION_AUTHORITY_FIX_300,
    REPOSITORY_MUTATION_AUTHORITY_FIX_300,
    ROLLBACK_AUTHORITY_FIX_300,
    TENANT_AUTHORITY_FIX_300,
    TENANT_CHANNELS,
    TENANT_DOMAINS,
    TENANT_PERMISSIONS,
    TENANT_ROLES,
    TRUST_MUTATION_AUTHORITY_FIX_300,
    TENANT_ROLE_MAP,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
    has_human_tenant_decision_approve,
    list_multi_tenant_platform_foundation_records,
)
from aethos_core.orgs.members import list_members
from aethos_core.orgs.organizations import get_current_organization, list_organizations
from aethos_core.orgs.rbac import role_permissions
from aethos_core.orgs.workspaces import list_workspaces


@dataclass(frozen=True)
class MultiTenantPlatformFoundationResult:
    ok: bool
    session_id: str
    multi_tenant_platform_foundation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _map_role(role: str) -> str:
    lowered = str(role or "").lower()
    for source, mapped in TENANT_ROLE_MAP:
        if lowered == source:
            return mapped
    if lowered == "owner":
        return "OWNER"
    return "OBSERVER"


def _organization_registry(*, tenant_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = get_current_organization()
    organizations = list_organizations()
    org_notes = [r for r in tenant_records if r.get("kind") == "organization_create_review_note"]
    return [
        {
            "registry_id": "organization-registry",
            "organization_count": len(organizations),
            "current_organization_id": current.get("org_id"),
            "organizations": [
                {
                    "organization_id": org.get("org_id"),
                    "name": org.get("name"),
                    "plan": org.get("plan"),
                    "tenant_isolated": org.get("tenant_isolated", True),
                    "governance_profile": "independent_trust_and_evidence",
                    "read_only": True,
                }
                for org in organizations
            ],
            "settings": {
                "tenant_isolation_required": True,
                "cross_tenant_access_enabled": False,
                "automatic_tenant_creation_enabled": False,
            },
            "operator_review_note_count": len(org_notes),
            "read_only": True,
        }
    ]


def _workspace_registry(*, tenant_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    workspaces = list_workspaces(org_id=current_org.get("org_id"))
    ws_notes = [r for r in tenant_records if r.get("kind") == "workspace_create_review_note"]
    return [
        {
            "registry_id": "workspace-registry",
            "organization_id": current_org.get("org_id"),
            "workspace_count": len(workspaces),
            "workspaces": [
                {
                    "workspace_id": ws.get("workspace_id"),
                    "name": ws.get("name"),
                    "repo_hint": ws.get("repo_hint"),
                    "status": ws.get("status"),
                    "read_only": True,
                }
                for ws in workspaces
            ],
            "example_workspace_types": ["engineering", "operations", "sales", "support"],
            "operator_review_note_count": len(ws_notes),
            "read_only": True,
        }
    ]


def _project_registry(
    *,
    delivery_rows: list[dict[str, Any]],
    tenant_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    project_notes = [r for r in tenant_records if r.get("kind") == "project_registration_review_note"]
    projects = [
        {
            "project_id": row.get("repository"),
            "display_name": row.get("display_name") or row.get("repository"),
            "repository": row.get("repository"),
            "product_signal": row.get("program_visibility"),
            "initiative_stages": list(row.get("live_evidence_stages") or []),
            "read_only": True,
        }
        for row in delivery_rows
    ]
    return [
        {
            "registry_id": "project-registry",
            "project_count": len(projects),
            "projects": projects[:12],
            "operator_review_note_count": len(project_notes),
            "read_only": True,
        }
    ]


def _identity_registry(*, tenant_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    members = list_members(org_id=current_org.get("org_id"))
    membership_notes = [r for r in tenant_records if r.get("kind") == "membership_review_note"]
    return [
        {
            "registry_id": "identity-registry",
            "organization_id": current_org.get("org_id"),
            "user_count": len(members),
            "memberships": [
                {
                    "member_id": member.get("member_id"),
                    "user_id": member.get("user_id"),
                    "role": _map_role(str(member.get("role") or "viewer")),
                    "mapped_platform_role": str(member.get("role") or "viewer"),
                    "read_only": True,
                }
                for member in members
            ],
            "authentication_model": "session_scoped_with_org_context",
            "authorization_model": "rbac_with_governance_lanes",
            "invitation_flow": "human_review_required",
            "operator_review_note_count": len(membership_notes),
            "read_only": True,
        }
    ]


def _role_registry() -> list[dict[str, Any]]:
    return [
        {
            "registry_id": "role-registry",
            "roles": [
                {
                    "role_id": role.lower(),
                    "role_name": role,
                    "mapped_from_platform_roles": [
                        source for source, mapped in TENANT_ROLE_MAP if mapped == role
                    ],
                    "read_only": True,
                }
                for role in TENANT_ROLES
            ],
            "read_only": True,
        }
    ]


def _permission_registry() -> list[dict[str, Any]]:
    rows = []
    for role_source, mapped_role in TENANT_ROLE_MAP:
        perms = sorted(role_permissions(role_source))
        rows.append(
            {
                "role": mapped_role,
                "platform_role": role_source,
                "permissions": list(TENANT_PERMISSIONS),
                "granted_platform_permissions": perms,
                "permission_escalation_enabled": False,
                "read_only": True,
            }
        )
    return [
        {
            "registry_id": "permission-registry",
            "permission_model": list(TENANT_PERMISSIONS),
            "role_permission_matrix": rows,
            "capability_specific_permissions": "planned_post_foundation",
            "read_only": True,
        }
    ]


def _tenant_trust_registry(
    *,
    capability_sections: dict[str, Any],
    tenant_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trust_matrix = (capability_sections.get("repository_trust_matrix") or [{}])[0]
    repos = list(trust_matrix.get("repositories") or [])
    governance_notes = [r for r in tenant_records if r.get("kind") == "tenant_governance_review_note"]
    current_org = get_current_organization()
    return [
        {
            "registry_id": "tenant-trust-registry",
            "organization_id": current_org.get("org_id"),
            "trust_baseline_count": len(repos),
            "trust_reports": repos,
            "trust_decisions_required": True,
            "cross_tenant_trust_enabled": False,
            "evidence_scope": "organization_local",
            "operator_review_note_count": len(governance_notes),
            "read_only": True,
        }
    ]


def _tenant_governance_boundary_registry(
    *,
    organizations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundaries = [
        {
            "organization_id": org.get("org_id"),
            "isolated_assets": [
                "repositories",
                "evidence",
                "approvals",
                "trust_records",
                "operator_history",
            ],
            "cross_tenant_access_enabled": False,
            "read_only": True,
        }
        for org in organizations
    ]
    return [
        {
            "registry_id": "tenant-governance-boundary-registry",
            "boundary_count": len(boundaries),
            "boundaries": boundaries,
            "isolation_guarantee": (
                "Organization A cannot access Organization B repositories, evidence, approvals, or trust records."
            ),
            "read_only": True,
        }
    ]


def _tenant_onboarding_registry(
    *,
    capability_sections: dict[str, Any],
    provider_matrix: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    self_awareness = (capability_sections.get("self_awareness_report") or [{}])[0]
    return [
        {
            "registry_id": "tenant-onboarding-registry",
            "onboarding_steps": [
                "organization_setup",
                "workspace_setup",
                "provider_connection",
                "capability_discovery",
                "trust_explanation",
            ],
            "capability_discovery_source": "fix_295_self_awareness_report",
            "trust_explanation_source": "fix_295_repository_trust_matrix",
            "provider_connection_targets": [
                row.get("provider") for row in provider_matrix if row.get("readiness") != "planned"
            ],
            "sample_first_run_prompts": [
                "what can you do",
                "show capability registry",
                "show tenant dashboard",
            ],
            "what_can_you_do_preview": (self_awareness.get("what_can_you_do") or [])[:5],
            "automatic_provisioning_enabled": False,
            "read_only": True,
        }
    ]


def _channel_registry() -> list[dict[str, Any]]:
    settings = get_settings()
    channels = [
        {
            "channel": "web",
            "status": "OPERATIONAL",
            "ingress": "mission_control_core",
            "read_only": True,
        },
        {
            "channel": "telegram",
            "status": "OPERATIONAL" if settings.telegram_enabled else "EXPERIMENTAL",
            "configured": bool(settings.telegram_enabled and settings.telegram_bot_token.strip()),
            "ingress": "mission_control_core",
            "read_only": True,
        },
        {
            "channel": "slack",
            "status": "PLANNED",
            "configured": False,
            "ingress": "mission_control_core",
            "read_only": True,
        },
        {
            "channel": "email",
            "status": "PLANNED",
            "configured": False,
            "ingress": "mission_control_core",
            "read_only": True,
        },
        {
            "channel": "voice",
            "status": "PLANNED",
            "configured": False,
            "ingress": "mission_control_core",
            "read_only": True,
        },
    ]
    return [
        {
            "registry_id": "channel-registry",
            "channel_count": len(channels),
            "channels": [row for row in channels if row["channel"] in TENANT_CHANNELS],
            "common_ingress_model": "all_channels_route_to_mission_control_core",
            "read_only": True,
        }
    ]


def build_multi_tenant_platform_foundation(*, session_id: str) -> MultiTenantPlatformFoundationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    tenant_records = list_multi_tenant_platform_foundation_records()
    human_approved = has_human_tenant_decision_approve(session_id=sid)

    capability = build_autonomous_capability_registry(session_id=sid)
    capability_payload = capability.autonomous_capability_registry or {}
    capability_sections = capability_payload.get("sections") or {}
    provider_matrix = list(
        ((capability_sections.get("provider_capability_matrix") or [{}])[0]).get("providers") or []
    )

    engineering = build_multi_repository_engineering_intelligence(session_id=sid)
    delivery_rows = list(
        (engineering.multi_repository_engineering_intelligence.get("sections") or {}).get(
            "program_delivery_visibility"
        )
        or []
    )

    organizations = list_organizations()
    organization_registry = _organization_registry(tenant_records=tenant_records)
    workspace_registry = _workspace_registry(tenant_records=tenant_records)
    project_registry = _project_registry(delivery_rows=delivery_rows, tenant_records=tenant_records)
    identity_registry = _identity_registry(tenant_records=tenant_records)
    role_registry = _role_registry()
    permission_registry = _permission_registry()
    tenant_trust_registry = _tenant_trust_registry(
        capability_sections=capability_sections,
        tenant_records=tenant_records,
    )
    governance_boundary_registry = _tenant_governance_boundary_registry(organizations=organizations)
    onboarding_registry = _tenant_onboarding_registry(
        capability_sections=capability_sections,
        provider_matrix=provider_matrix,
    )
    channel_registry = _channel_registry()

    sections = {
        "organization_registry": organization_registry,
        "workspace_registry": workspace_registry,
        "project_registry": project_registry,
        "identity_registry": identity_registry,
        "role_registry": role_registry,
        "permission_registry": permission_registry,
        "tenant_trust_registry": tenant_trust_registry,
        "tenant_governance_boundary_registry": governance_boundary_registry,
        "tenant_onboarding_registry": onboarding_registry,
        "channel_registry": channel_registry,
        "tenant_dashboard": [
            {
                "dashboard_id": "tenant-dashboard",
                "tenant_domains": list(TENANT_DOMAINS),
                "organization_count": organization_registry[0]["organization_count"],
                "workspace_count": workspace_registry[0]["workspace_count"],
                "project_count": project_registry[0]["project_count"],
                "user_count": identity_registry[0]["user_count"],
                "trusted_repository_count": tenant_trust_registry[0]["trust_baseline_count"],
                "connected_provider_count": sum(
                    1 for row in provider_matrix if row.get("readiness") == "ready"
                ),
                "operational_channel_count": sum(
                    1
                    for row in channel_registry[0]["channels"]
                    if row.get("status") == "OPERATIONAL"
                ),
                "cross_tenant_access_enabled": False,
                "human_tenant_decision_approve": human_approved,
                "read_only": True,
            }
        ],
        "human_tenant_review": [
            {
                "review_id": "human-tenant-review",
                "decisions_supported": list(HUMAN_TENANT_DECISION_KINDS),
                "human_tenant_decision_approve": human_approved,
                "automatic_tenant_creation_enabled": False,
                "execution_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_tenant_platform_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_TENANT_PLATFORM_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION,
        "fix": MULTI_TENANT_PLATFORM_FOUNDATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_300,
        "execution_performed": EXECUTION_PERFORMED_FIX_300,
        "tenant_compose_artifacts_only": MULTI_TENANT_PLATFORM_COMPOSES_EVIDENCE_ONLY_FIX_300,
        "tenant_authority": TENANT_AUTHORITY_FIX_300,
        "automatic_tenant_creation_enabled": AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
        "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_300,
        "cross_tenant_trust_enabled": CROSS_TENANT_TRUST_ENABLED_FIX_300,
        "permission_escalation_enabled": PERMISSION_ESCALATION_ENABLED_FIX_300,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_300,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_300,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_300,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_300,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_300,
        "merge_authority": MERGE_AUTHORITY_FIX_300,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_300,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_300,
        "invariant": MULTI_TENANT_PLATFORM_FOUNDATION_INVARIANT,
        "session_id": sid,
        "tenant_domains": list(TENANT_DOMAINS),
        "sections": sections,
        "operator_record_count": len(tenant_records),
        "human_tenant_decision_approve": human_approved,
        "fix_300_certification_requirements": list(FIX_300_CERTIFICATION_REQUIREMENTS),
        "multi_tenant_platform_foundation_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in MULTI_TENANT_PLATFORM_FOUNDATION_PRINCIPLES
        ],
        "sources": {
            "composes_fix_295_capability_registry": True,
            "composes_fix_260_multi_repository_engineering_intelligence": True,
            "composes_existing_org_workspace_identity_stores": True,
            "composes_provider_and_channel_readiness": True,
            "pilot_reexecution_performed": False,
            "automatic_tenant_provisioning_performed": False,
            "cross_tenant_access_performed": False,
        },
    }

    return MultiTenantPlatformFoundationResult(
        ok=True,
        session_id=sid,
        multi_tenant_platform_foundation=payload,
        detail="Multi-tenant platform foundation composed from tenancy evidence (multi-tenant ≠ governance bypass).",
    )
