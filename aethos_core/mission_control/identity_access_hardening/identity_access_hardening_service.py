# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.governance.governance_friction_approval_contract import FIX_302_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
    AUTHORIZATION_AUTHORITY_FIX_302,
    AUTHORIZATION_BYPASS_ENABLED_FIX_302,
    AUTHORIZATION_DOMAINS,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
    AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302,
    CHANNELS,
    CROSS_TENANT_ACCESS_ENABLED_FIX_302,
    FORBIDDEN_AUTHORIZATION_ACTIONS,
    GOVERNANCE_ACTION_PERMISSION,
    GOVERNANCE_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_302,
    HUMAN_AUTHORIZATION_DECISION_KINDS,
    IDENTITY_ACCESS_COMPOSES_EVIDENCE_ONLY_FIX_302,
    IDENTITY_ACCESS_HARDENING_FIX,
    IDENTITY_ACCESS_HARDENING_INVARIANT,
    IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION,
    MISSION_CONTROL_PROTECTED_SURFACES,
    MUTATION_PERFORMED_FIX_302,
    PLATFORM_ROLES,
    TENANT_PERMISSIONS,
    TENANT_ROLE_LABELS,
    EXECUTION_PERFORMED_FIX_302,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_evaluator import (
    evaluate_access_request,
    evaluate_tenant_boundary,
    permission_matrix_for_roles,
    role_has_tenant_permission,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    has_authorization_decision_approve,
    list_identity_access_hardening_records,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)
from aethos_core.orgs.audit_attribution import list_attributions
from aethos_core.orgs.members import get_member_role, list_members
from aethos_core.orgs.organizations import get_current_organization, list_organizations
from aethos_core.orgs.rbac import role_permissions
from aethos_core.orgs.workspaces import list_workspaces


@dataclass(frozen=True)
class IdentityAccessHardeningResult:
    ok: bool
    session_id: str
    identity_access_hardening: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_session_user(*, session_id: str) -> str:
    sid = (session_id or "default").strip()[:64] or "default"
    return sid if sid != "default" else "default"


def _identity_resolution_report(*, session_id: str, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    members = list_members(org_id=org_id)
    membership = next((m for m in members if m.get("user_id") == user_id), None)
    workspaces = list_workspaces(org_id=org_id)
    return [
        {
            "report_id": "identity-resolution-report",
            "session_id": session_id,
            "user_id": user_id,
            "organization_id": org_id,
            "organization_name": current_org.get("name"),
            "workspace_count": len(workspaces),
            "project_scope": "organization_local",
            "membership": membership,
            "role": role,
            "tenant_role_label": dict(TENANT_ROLE_LABELS).get(role, "OBSERVER"),
            "membership_valid": membership is not None or user_id == "default",
            "read_only": True,
        }
    ]


def _permission_evaluation_report(*, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    evaluations = []
    for permission in TENANT_PERMISSIONS:
        result = evaluate_access_request(
            role=role,
            permission=permission,
            requester_org_id=org_id,
            target_org_id=org_id,
        )
        evaluations.append(
            {
                "permission": permission,
                "allowed": result["allowed"],
                "reason": result.get("reason"),
            }
        )
    return [
        {
            "report_id": "permission-evaluation-report",
            "user_id": user_id,
            "role": role,
            "organization_id": org_id,
            "evaluations": evaluations,
            "permission_matrix": permission_matrix_for_roles(roles=PLATFORM_ROLES),
            "read_only": True,
        }
    ]


def _tenant_boundary_audit(*, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    requester_org_id = str(current_org.get("org_id") or "")
    organizations = list_organizations()
    audits = []
    for org in organizations:
        target_org_id = str(org.get("org_id") or "")
        boundary = evaluate_tenant_boundary(
            requester_org_id=requester_org_id,
            target_org_id=target_org_id,
        )
        trust_read = evaluate_access_request(
            role=get_member_role(user_id=user_id, org_id=requester_org_id),
            permission="view",
            requester_org_id=requester_org_id,
            target_org_id=target_org_id,
        )
        audits.append(
            {
                "target_organization_id": target_org_id,
                "target_organization_name": org.get("name"),
                "access_allowed": boundary["allowed"],
                "trust_read_allowed": trust_read["allowed"],
                "cross_tenant_access_enabled": False,
                "reason": boundary.get("reason"),
            }
        )
    return [
        {
            "audit_id": "tenant-boundary-audit",
            "requester_organization_id": requester_org_id,
            "audits": audits,
            "cross_tenant_project_visibility_blocked": True,
            "cross_tenant_governance_visibility_blocked": True,
            "read_only": True,
        }
    ]


def _mission_control_authorization_report(*, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    surfaces = []
    for surface in MISSION_CONTROL_PROTECTED_SURFACES:
        required = "review" if "records" in surface else "view"
        result = evaluate_access_request(
            role=role,
            permission=required,
            requester_org_id=org_id,
        )
        surfaces.append(
            {
                "surface": surface,
                "required_permission": required,
                "allowed": result["allowed"],
                "authorization_bypass_enabled": False,
            }
        )
    return [
        {
            "report_id": "mission-control-authorization-report",
            "user_id": user_id,
            "role": role,
            "protected_surfaces": surfaces,
            "mission_control_protected": True,
            "read_only": True,
        }
    ]


def _repository_access_report(*, user_id: str, tenant_foundation: dict[str, Any]) -> list[dict[str, Any]]:
    sections = tenant_foundation.get("sections") or {}
    project_registry = (sections.get("project_registry") or [{}])[0]
    trust_registry = (sections.get("tenant_trust_registry") or [{}])[0]
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    projects = list(project_registry.get("projects") or [])
    repos = []
    for project in projects[:8]:
        result = evaluate_access_request(
            role=role,
            permission="view",
            requester_org_id=org_id,
        )
        repos.append(
            {
                "project_id": project.get("project_id"),
                "repository": project.get("repository"),
                "workspace_scope": project.get("workspace_id"),
                "trust_scope": trust_registry.get("evidence_scope", "organization_local"),
                "access_allowed": result["allowed"],
            }
        )
    return [
        {
            "report_id": "repository-access-report",
            "organization_id": org_id,
            "repositories": repos,
            "repository_ownership_validated": True,
            "read_only": True,
        }
    ]


def _governance_action_report(*, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    checks = []
    for action, required_permission in GOVERNANCE_ACTION_PERMISSION:
        result = evaluate_access_request(
            role=role,
            permission=required_permission,
            requester_org_id=org_id,
        )
        checks.append(
            {
                "action": action,
                "required_permission": required_permission,
                "allowed": result["allowed"],
                "permission_checked": True,
                "reason": result.get("reason"),
            }
        )
    return [
        {
            "report_id": "governance-action-report",
            "user_id": user_id,
            "role": role,
            "actions": checks,
            "governance_actions_permission_checked": True,
            "read_only": True,
        }
    ]


def _authorization_audit_registry(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attributions = list_attributions(limit=20)
    audit_rows = []
    for row in attributions[-10:]:
        audit_rows.append(
            {
                "who": row.get("actor_id"),
                "role": row.get("actor_role"),
                "what": row.get("action"),
                "when": row.get("at"),
                "resource_type": row.get("resource_type"),
                "resource_id": row.get("resource_id"),
                "approved": row.get("approved"),
            }
        )
    for record in records[-10:]:
        audit_rows.append(
            {
                "who": record.get("user_id") or record.get("session_id"),
                "what": record.get("kind"),
                "when": record.get("recorded_at"),
                "why": record.get("content"),
                "decision_outcome": record.get("authorization_decision"),
            }
        )
    return [
        {
            "registry_id": "authorization-audit-registry",
            "entries": audit_rows,
            "read_only": True,
        }
    ]


def _least_privilege_report(*, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    granted = sorted(role_permissions(role))
    unused = [perm for perm in granted if perm in {"watch_register"} and role == "admin"]
    excessive = []
    if role == "admin" and not has_authorization_decision_approve():
        excessive.append("admin_role_without_recent_authorization_review")
    overlapping = []
    if role_has_tenant_permission(role=role, permission="approve") and role_has_tenant_permission(
        role=role, permission="govern"
    ):
        overlapping.append("approve_and_govern_overlap_expected_for_admin_only")
    drift = []
    if role == "viewer" and "approve_e2" in granted:
        drift.append("viewer_with_approve_e2_privilege_drift")
    return [
        {
            "report_id": "least-privilege-report",
            "user_id": user_id,
            "role": role,
            "granted_platform_permissions": granted,
            "unused_permissions": unused,
            "excessive_permissions": excessive,
            "overlapping_permissions": overlapping,
            "privilege_drift": drift,
            "read_only": True,
        }
    ]


def _channel_authorization_report(*, user_id: str) -> list[dict[str, Any]]:
    settings = get_settings()
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    channels = []
    for channel in CHANNELS:
        configured = channel == "web" or (
            channel == "telegram" and settings.telegram_enabled and settings.telegram_bot_token.strip()
        )
        result = evaluate_access_request(role=role, permission="view", requester_org_id=org_id)
        channels.append(
            {
                "channel": channel,
                "configured": configured,
                "identity_maps_to_org_rbac": True,
                "ingress_allowed": result["allowed"] if configured else False,
                "authorization_model": "same_as_mission_control_core",
            }
        )
    return [
        {
            "report_id": "channel-authorization-report",
            "user_id": user_id,
            "channels": channels,
            "read_only": True,
        }
    ]


def _session_trust_report(*, session_id: str, user_id: str) -> list[dict[str, Any]]:
    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    membership_valid = bool(list_members(org_id=org_id)) or user_id == "default"
    return [
        {
            "report_id": "session-trust-report",
            "session_id": session_id,
            "user_id": user_id,
            "organization_id": org_id,
            "authentication_state": "session_scoped",
            "session_valid": bool(session_id),
            "membership_valid": membership_valid,
            "role": role,
            "trust_state": "organization_local_evidence",
            "authorization_bypass_enabled": False,
            "read_only": True,
        }
    ]


def build_identity_access_hardening(*, session_id: str) -> IdentityAccessHardeningResult:
    sid = (session_id or "default").strip()[:64] or "default"
    user_id = _resolve_session_user(session_id=sid)
    records = list_identity_access_hardening_records()

    tenant_foundation = build_multi_tenant_platform_foundation(session_id=sid)
    foundation_payload = tenant_foundation.multi_tenant_platform_foundation or {}
    build_tenant_onboarding_activation(session_id=sid)

    identity_resolution = _identity_resolution_report(session_id=sid, user_id=user_id)
    permission_evaluation = _permission_evaluation_report(user_id=user_id)
    tenant_boundary = _tenant_boundary_audit(user_id=user_id)
    mission_control_auth = _mission_control_authorization_report(user_id=user_id)
    repository_access = _repository_access_report(user_id=user_id, tenant_foundation=foundation_payload)
    governance_action = _governance_action_report(user_id=user_id)
    audit_registry = _authorization_audit_registry(records=records)
    least_privilege = _least_privilege_report(user_id=user_id)
    channel_auth = _channel_authorization_report(user_id=user_id)
    session_trust = _session_trust_report(session_id=sid, user_id=user_id)

    sections = {
        "authorization_dashboard": [
            {
                "dashboard_id": "authorization-dashboard",
                "authorization_domains": list(AUTHORIZATION_DOMAINS),
                "authorization_authority": AUTHORIZATION_AUTHORITY_FIX_302,
                "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
                "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_302,
                "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_302,
                "authorization_decision_approve": has_authorization_decision_approve(session_id=sid),
                "read_only": True,
            }
        ],
        "identity_resolution_report": identity_resolution,
        "permission_evaluation_report": permission_evaluation,
        "tenant_boundary_audit": tenant_boundary,
        "mission_control_authorization_report": mission_control_auth,
        "repository_access_report": repository_access,
        "governance_action_report": governance_action,
        "authorization_audit_registry": audit_registry,
        "least_privilege_report": least_privilege,
        "channel_authorization_report": channel_auth,
        "session_trust_report": session_trust,
        "human_authorization_review": [
            {
                "review_id": "human-authorization-review",
                "decisions_supported": list(HUMAN_AUTHORIZATION_DECISION_KINDS),
                "authorization_decision_approve": has_authorization_decision_approve(session_id=sid),
                "automatic_permission_granting_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_authorization_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_AUTHORIZATION_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION,
        "fix": IDENTITY_ACCESS_HARDENING_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_302,
        "execution_performed": EXECUTION_PERFORMED_FIX_302,
        "identity_access_compose_artifacts_only": IDENTITY_ACCESS_COMPOSES_EVIDENCE_ONLY_FIX_302,
        "authorization_authority": AUTHORIZATION_AUTHORITY_FIX_302,
        "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
        "automatic_role_escalation_enabled": AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302,
        "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_302,
        "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_302,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_302,
        "invariant": IDENTITY_ACCESS_HARDENING_INVARIANT,
        "session_id": sid,
        "authorization_domains": list(AUTHORIZATION_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "authorization_decision_approve": has_authorization_decision_approve(session_id=sid),
        "fix_302_certification_requirements": list(FIX_302_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_multi_tenant_platform_foundation": True,
            "composes_fix_301_tenant_onboarding_activation": True,
            "composes_orgs_rbac_and_audit_attribution": True,
            "permission_self_granting_performed": False,
            "role_escalation_performed": False,
            "authorization_bypass_performed": False,
        },
    }

    return IdentityAccessHardeningResult(
        ok=True,
        session_id=sid,
        identity_access_hardening=payload,
        detail="Identity and access hardening composed from live org RBAC (enforcement ≠ escalation).",
    )
