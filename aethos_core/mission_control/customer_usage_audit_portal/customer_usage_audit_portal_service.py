# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_307_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.approval_inbox.approval_audit_service import list_ui_approval_audits
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
    list_billing_entitlements_foundation_records,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
    list_channel_integration_foundation_records,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
    list_customer_administration_console_records,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
    AUDIT_AUTHORITY_FIX_307,
    AUDIT_MUTATION_ENABLED_FIX_307,
    AUDIT_PORTAL_DOMAINS,
    AUTHORIZATION_BYPASS_ENABLED_FIX_307,
    CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
    CUSTOMER_USAGE_AUDIT_COMPOSES_EVIDENCE_ONLY_FIX_307,
    CUSTOMER_USAGE_AUDIT_PORTAL_FIX,
    CUSTOMER_USAGE_AUDIT_PORTAL_INVARIANT,
    CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION,
    EVIDENCE_MUTATION_ENABLED_FIX_307,
    EXECUTION_PERFORMED_FIX_307,
    FORBIDDEN_AUDIT_PORTAL_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_307,
    HUMAN_AUDIT_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_307,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_evaluator import (
    evaluate_audit_portal_access,
    normalize_audit_entry,
    split_timelines,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
    has_audit_decision_approve,
    list_customer_usage_audit_portal_records,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    list_identity_access_hardening_records,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
    list_multi_tenant_platform_foundation_records,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    list_pilotos_ui_trust_report_freeze_records,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    list_provider_connection_experience_records,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    list_tenant_onboarding_activation_records,
)
from aethos_core.orgs.audit_attribution import list_attributions
from aethos_core.orgs.members import get_member_role, list_members
from aethos_core.orgs.organizations import get_current_organization
from aethos_core.orgs.workspaces import list_workspaces


@dataclass(frozen=True)
class CustomerUsageAuditPortalResult:
    ok: bool
    session_id: str
    customer_usage_audit_portal: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_user(*, session_id: str) -> str:
    sid = (session_id or "default").strip()[:64] or "default"
    return sid if sid != "default" else "default"


def _collect_audit_entries(*, org_id: str, session_id: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    sources = [
        ("attribution", list_attributions(limit=100)),
        ("ui_approval", list_ui_approval_audits(session_id=session_id, limit=50)),
        ("fix_300", list_multi_tenant_platform_foundation_records()),
        ("fix_301", list_tenant_onboarding_activation_records()),
        ("fix_302", list_identity_access_hardening_records()),
        ("fix_303", list_provider_connection_experience_records()),
        ("fix_304", list_channel_integration_foundation_records()),
        ("fix_305", list_billing_entitlements_foundation_records()),
        ("fix_306", list_customer_administration_console_records()),
        ("fix_307", list_customer_usage_audit_portal_records()),
    ]
    for source, rows in sources:
        for row in rows:
            normalized = normalize_audit_entry(entry=row, source=source, org_id=org_id)
            if normalized:
                entries.append(normalized)
    entries.sort(key=lambda row: str(row.get("when") or ""), reverse=True)
    return entries


def build_customer_usage_audit_portal(*, session_id: str) -> CustomerUsageAuditPortalResult:
    sid = (session_id or "default").strip()[:64] or "default"
    user_id = _resolve_user(session_id=sid)
    records = list_customer_usage_audit_portal_records()

    billing = build_billing_entitlements_foundation(session_id=sid)
    provider = build_provider_connection_experience(session_id=sid)

    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    members = list_members(org_id=org_id)
    workspaces = list_workspaces(org_id=org_id)

    audit_access = evaluate_audit_portal_access(role=role, requester_org_id=org_id)
    audit_entries = _collect_audit_entries(org_id=org_id, session_id=sid)
    timelines = split_timelines(audit_entries)

    billing_sections = (billing.billing_entitlements_foundation.get("sections") or {})
    billing_dashboard = (billing_sections.get("billing_dashboard") or [{}])[0]
    usage_registry = (billing_sections.get("usage_registry") or [{}])[0]
    provider_sections = (provider.provider_connection_experience.get("sections") or {})
    provider_dashboard = (provider_sections.get("provider_connection_dashboard") or [{}])[0]

    trust_freeze_records = list_pilotos_ui_trust_report_freeze_records(limit=20)

    activity_timeline = [
        {
            "timeline_id": "activity-timeline",
            "organization_id": org_id,
            "entry_count": len(timelines["activity_timeline"]),
            "entries": timelines["activity_timeline"][:50],
            "immutable": True,
            "read_only": True,
        }
    ]

    governance_timeline = [
        {
            "timeline_id": "governance-timeline",
            "organization_id": org_id,
            "entry_count": len(timelines["governance_timeline"]),
            "entries": timelines["governance_timeline"][:50],
            "actions_tracked": [
                "trust_decision",
                "merge_decision",
                "deploy_decision",
                "rollback_decision",
                "lifecycle_decision",
            ],
            "immutable": True,
            "read_only": True,
        }
    ]

    usage_timeline = [
        {
            "timeline_id": "usage-timeline",
            "organization_id": org_id,
            "entry_count": len(timelines["usage_timeline"]),
            "entries": timelines["usage_timeline"][:50],
            "usage_snapshot": usage_registry.get("usage") or billing_dashboard.get("usage") or {},
            "channels_tracked": True,
            "provider_usage_tracked": True,
            "immutable": True,
            "read_only": True,
        }
    ]

    audit_registry = [
        {
            "registry_id": "audit-registry",
            "organization_id": org_id,
            "entry_count": len(audit_entries),
            "entries": audit_entries[:100],
            "sources_composed": [
                "fix_300_multi_tenant",
                "fix_301_onboarding",
                "fix_302_authorization",
                "fix_303_provider_connection",
                "fix_304_channel_integration",
                "fix_305_billing_entitlements",
                "fix_306_administration",
                "fix_307_audit_portal",
                "ui_approval_audit",
                "audit_attribution",
            ],
            "audit_mutation_enabled": False,
            "immutable": True,
            "read_only": True,
        }
    ]

    repository_activity = [
        {
            "report_id": "repository-activity-report",
            "organization_id": org_id,
            "repositories": [
                {
                    "repository": ws.get("repo_hint"),
                    "workspace_id": ws.get("workspace_id"),
                    "trust_state_history": ["governed_evidence_first"],
                    "lifecycle_status": ws.get("status", "active"),
                    "actions": [],
                }
                for ws in workspaces
            ],
            "repository_count": len({w.get("repo_hint") for w in workspaces if w.get("repo_hint")}),
            "read_only": True,
        }
    ]

    user_activity = [
        {
            "report_id": "user-activity-report",
            "organization_id": org_id,
            "users": [
                {
                    "user_id": member.get("user_id"),
                    "role": member.get("role"),
                    "participation": [
                        entry
                        for entry in audit_entries
                        if str(entry.get("who") or "") == str(member.get("user_id") or "")
                    ][:10],
                }
                for member in members
            ],
            "read_only": True,
        }
    ]

    provider_activity = [
        {
            "report_id": "provider-activity-report",
            "composed_from_fix_303": True,
            "organization_id": org_id,
            "interactions": [
                entry
                for entry in audit_entries
                if "provider" in str(entry.get("kind") or "").lower()
                or entry.get("source") == "fix_303"
            ][:20],
            "readiness_summary": provider_dashboard.get("readiness_summary") or [],
            "capability_unlock_changes": (
                (provider_sections.get("provider_capability_unlock_matrix") or [{}])[0].get("providers") or []
            ),
            "read_only": True,
        }
    ]

    billing_usage_history = [
        {
            "report_id": "billing-usage-history-report",
            "composed_from_fix_305": True,
            "organization_id": org_id,
            "plan": billing_dashboard.get("plan"),
            "usage_history": [entry for entry in audit_entries if entry.get("category") == "usage"][:20],
            "limit_consumption": billing_dashboard.get("limit_consumption") or {},
            "entitlement_history": (
                (billing_sections.get("entitlement_registry") or [{}])[0].get("features") or []
            ),
            "plan_changes": [],
            "billing_mutation_enabled": False,
            "read_only": True,
        }
    ]

    evidence_explorer = [
        {
            "explorer_id": "evidence-explorer",
            "organization_id": org_id,
            "trust_freezes": [
                {
                    "artifact_id": row.get("record_id") or row.get("kind"),
                    "kind": row.get("kind"),
                    "recorded_at": row.get("recorded_at"),
                    "content_preview": str(row.get("content") or "")[:120],
                    "immutable": True,
                }
                for row in trust_freeze_records[:10]
            ],
            "pilot_evidence": [
                entry
                for entry in audit_entries
                if "pilot" in str(entry.get("kind") or "").lower()
                or "trust" in str(entry.get("kind") or "").lower()
            ][:10],
            "lifecycle_evidence": [
                entry
                for entry in audit_entries
                if "lifecycle" in str(entry.get("kind") or "").lower()
            ][:10],
            "governance_evidence": timelines["governance_timeline"][:10],
            "operational_evidence": timelines["activity_timeline"][:10],
            "evidence_mutation_enabled": False,
            "read_only": True,
        }
    ]

    customer_audit_dashboard = [
        {
            "dashboard_id": "customer-audit-dashboard",
            "organization_id": org_id,
            "requester_role": role,
            "audit_access_allowed": audit_access["allowed"],
            "activity_entry_count": len(timelines["activity_timeline"]),
            "governance_entry_count": len(timelines["governance_timeline"]),
            "usage_entry_count": len(timelines["usage_timeline"]),
            "audit_registry_entry_count": len(audit_entries),
            "evidence_artifact_count": len(trust_freeze_records) + len(timelines["governance_timeline"]),
            "billing_plan": billing_dashboard.get("plan"),
            "audit_health": "tenant_scoped_immutable_visibility",
            "cross_tenant_audit_access_blocked": not CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
            "read_only": True,
        }
    ]

    sections = {
        "activity_timeline": activity_timeline,
        "governance_timeline": governance_timeline,
        "usage_timeline": usage_timeline,
        "audit_registry": audit_registry,
        "repository_activity_report": repository_activity,
        "user_activity_report": user_activity,
        "provider_activity_report": provider_activity,
        "billing_usage_history_report": billing_usage_history,
        "evidence_explorer": evidence_explorer,
        "customer_audit_dashboard": customer_audit_dashboard,
        "human_audit_review": [
            {
                "review_id": "human-audit-review",
                "decisions_supported": list(HUMAN_AUDIT_DECISION_KINDS),
                "audit_decision_approve": has_audit_decision_approve(session_id=sid),
                "audit_mutation_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_audit_portal_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_AUDIT_PORTAL_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION,
        "fix": CUSTOMER_USAGE_AUDIT_PORTAL_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_307,
        "execution_performed": EXECUTION_PERFORMED_FIX_307,
        "customer_usage_audit_compose_artifacts_only": CUSTOMER_USAGE_AUDIT_COMPOSES_EVIDENCE_ONLY_FIX_307,
        "audit_authority": AUDIT_AUTHORITY_FIX_307,
        "audit_mutation_enabled": AUDIT_MUTATION_ENABLED_FIX_307,
        "evidence_mutation_enabled": EVIDENCE_MUTATION_ENABLED_FIX_307,
        "cross_tenant_audit_access_enabled": CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
        "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_307,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_307,
        "invariant": CUSTOMER_USAGE_AUDIT_PORTAL_INVARIANT,
        "session_id": sid,
        "requester_user_id": user_id,
        "requester_role": role,
        "audit_portal_access": audit_access,
        "audit_portal_domains": list(AUDIT_PORTAL_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "audit_decision_approve": has_audit_decision_approve(session_id=sid),
        "fix_307_certification_requirements": list(FIX_307_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_303_provider_activity": bool(provider.ok),
            "composes_fix_305_billing_history": bool(billing.ok),
            "composes_mission_control_records": True,
            "audit_mutation_performed": False,
            "evidence_mutation_performed": False,
            "cross_tenant_audit_access_performed": False,
        },
    }

    return CustomerUsageAuditPortalResult(
        ok=True,
        session_id=sid,
        customer_usage_audit_portal=payload,
        detail="Customer usage & audit portal composed (visibility ≠ authority, immutable audit records).",
    )
