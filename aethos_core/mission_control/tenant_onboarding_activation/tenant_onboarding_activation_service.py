# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_301_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301,
    AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
    CROSS_TENANT_ACCESS_ENABLED_FIX_301,
    FORBIDDEN_ONBOARDING_ACTIONS,
    FUTURE_PROVIDER_CONNECTION_TARGETS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_301,
    ONBOARDING_STEP_LABELS,
    ONBOARDING_STEPS,
    ONBOARDING_AUTHORITY_FIX_301,
    PROVIDER_CONNECTION_TARGETS,
    PROVIDER_MUTATION_AUTHORITY_FIX_301,
    SECRET_COLLECTION_ENABLED_FIX_301,
    STEP_RECORD_KINDS,
    TENANT_ONBOARDING_ACTIVATION_FIX,
    TENANT_ONBOARDING_ACTIVATION_INVARIANT,
    TENANT_ONBOARDING_ACTIVATION_PRINCIPLES,
    TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION,
    TENANT_ONBOARDING_COMPOSES_EVIDENCE_ONLY_FIX_301,
    TRUST_MUTATION_AUTHORITY_FIX_301,
    EXECUTION_PERFORMED_FIX_301,
    MUTATION_PERFORMED_FIX_301,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    has_onboarding_decision_approve,
    has_onboarding_record_kind,
    list_tenant_onboarding_activation_records,
)


@dataclass(frozen=True)
class TenantOnboardingActivationResult:
    ok: bool
    session_id: str
    tenant_onboarding_activation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _step_status(*, step: str, session_id: str) -> str:
    if step in {"capability_discovery", "trust_explanation"}:
        return "ready"
    record_kind = dict(STEP_RECORD_KINDS).get(step)
    if record_kind and has_onboarding_record_kind(kind=record_kind, session_id=session_id):
        return "review_recorded"
    if step == "first_mission_control_session":
        setup_complete = all(
            has_onboarding_record_kind(kind=kind, session_id=session_id)
            for _, kind in STEP_RECORD_KINDS
        )
        if has_onboarding_decision_approve(session_id=session_id) and setup_complete:
            return "activation_ready"
        if setup_complete:
            return "awaiting_onboarding_decision"
        return "blocked"
    return "pending"


def _onboarding_progress_registry(*, session_id: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    completed = 0
    for step, label in ONBOARDING_STEP_LABELS:
        status = _step_status(step=step, session_id=session_id)
        if status in {"review_recorded", "ready", "activation_ready", "awaiting_onboarding_decision"}:
            completed += 1
        steps.append(
            {
                "step_id": step,
                "label": label,
                "status": status,
                "read_only": True,
            }
        )
    return [
        {
            "registry_id": "onboarding-progress-registry",
            "steps": steps,
            "completed_step_count": completed,
            "total_step_count": len(ONBOARDING_STEPS),
            "automatic_provisioning_enabled": False,
            "read_only": True,
        }
    ]


def _organization_setup_review(*, records: list[dict[str, Any]], session_id: str) -> list[dict[str, Any]]:
    notes = [
        row
        for row in records
        if str(row.get("kind") or "") == "organization_setup_review_note"
        and (not session_id or str(row.get("session_id") or "") == session_id)
    ]
    return [
        {
            "review_id": "organization-setup-review",
            "status": _step_status(step="organization_setup", session_id=session_id),
            "collects": [
                "organization_name",
                "primary_operator",
                "intended_use_case",
                "governance_preference",
            ],
            "operator_notes": notes[-3:],
            "automatic_provisioning_enabled": False,
            "read_only": True,
        }
    ]


def _workspace_setup_review(*, records: list[dict[str, Any]], session_id: str) -> list[dict[str, Any]]:
    notes = [
        row
        for row in records
        if str(row.get("kind") or "") == "workspace_setup_review_note"
        and (not session_id or str(row.get("session_id") or "") == session_id)
    ]
    return [
        {
            "review_id": "workspace-setup-review",
            "status": _step_status(step="workspace_setup", session_id=session_id),
            "collects": ["workspace_name", "workspace_purpose", "team_function", "initial_visibility"],
            "operator_notes": notes[-3:],
            "automatic_provisioning_enabled": False,
            "read_only": True,
        }
    ]


def _project_registration_review(*, records: list[dict[str, Any]], session_id: str) -> list[dict[str, Any]]:
    notes = [
        row
        for row in records
        if str(row.get("kind") or "") == "project_registration_review_note"
        and (not session_id or str(row.get("session_id") or "") == session_id)
    ]
    return [
        {
            "review_id": "project-registration-review",
            "status": _step_status(step="project_registration", session_id=session_id),
            "collects": [
                "project_name",
                "repository_url",
                "provider",
                "environment_type",
                "intended_first_workflow",
            ],
            "operator_notes": notes[-3:],
            "automatic_provisioning_enabled": False,
            "read_only": True,
        }
    ]


def _provider_connection_checklist(*, provider_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {str(row.get("provider") or ""): row for row in provider_matrix}
    targets: list[dict[str, Any]] = []
    for provider in PROVIDER_CONNECTION_TARGETS:
        row = by_name.get(provider, {})
        targets.append(
            {
                "provider": provider,
                "status": row.get("status", "PLANNED"),
                "readiness": row.get("readiness", "unknown"),
                "setup_guidance": (
                    f"Configure {provider} credentials in Mission Control Mission Control → Advanced settings → Credentials. "
                    "Never paste secrets into chat."
                ),
                "secret_collection_in_chat_forbidden": True,
                "provider_mutation_authority": False,
                "read_only": True,
            }
        )
    return [
        {
            "checklist_id": "provider-connection-checklist",
            "targets": targets,
            "future_targets": list(FUTURE_PROVIDER_CONNECTION_TARGETS),
            "manual_connection_only": True,
            "secret_collection_enabled": False,
            "provider_mutation_authority": False,
            "read_only": True,
        }
    ]


def _capability_discovery_report(
    *,
    capability_runtime: dict[str, Any],
) -> list[dict[str, Any]]:
    runtime_sections = capability_runtime.get("sections") or {}
    self_awareness = capability_runtime.get("self_awareness_report") or {}
    proven = (runtime_sections.get("proven_capabilities") or [{}])[0]
    experimental = (runtime_sections.get("experimental_capabilities") or [{}])[0]
    authority = (runtime_sections.get("authority_boundaries") or [{}])[0]
    provider_matrix = (runtime_sections.get("provider_capability_matrix") or [{}])[0]
    return [
        {
            "report_id": "capability-discovery-report",
            "source": "fix_295_capability_registry_and_fix_296_runtime_integration",
            "what_can_you_do": list(self_awareness.get("what_can_you_do") or [])[:12],
            "what_cannot_you_do": list(self_awareness.get("what_cant_you_do") or [])[:12],
            "proven_capabilities": list(proven.get("items") or [])[:12],
            "experimental_capabilities": list(experimental.get("items") or [])[:12],
            "supported_providers": [
                row.get("provider") for row in (provider_matrix.get("providers") or [])[:8]
            ],
            "authority_boundaries": list(authority.get("boundaries") or [])[:8],
            "read_only": True,
        }
    ]


def _trust_explanation_report(
    *,
    tenant_foundation: dict[str, Any],
    capability_runtime: dict[str, Any],
) -> list[dict[str, Any]]:
    foundation_sections = tenant_foundation.get("sections") or {}
    tenant_trust = (foundation_sections.get("tenant_trust_registry") or [{}])[0]
    governance_boundary = (foundation_sections.get("tenant_governance_boundary_registry") or [{}])[0]
    runtime_sections = capability_runtime.get("sections") or {}
    trust_matrix = (runtime_sections.get("repository_trust_matrix") or [{}])[0]
    provider_matrix = (runtime_sections.get("provider_capability_matrix") or [{}])[0]
    return [
        {
            "report_id": "trust-explanation-report",
            "human_approval_model": [
                "Human approval is required at governance gates.",
                "Onboarding records decisions — it does not grant authority.",
                "Approve, hold, reject, or defer without automatic provisioning.",
            ],
            "governance_boundaries": list(governance_boundary.get("boundaries") or [])[:6],
            "trust_baselines": list(tenant_trust.get("trust_baselines") or [])[:8],
            "repository_trust": list(trust_matrix.get("repositories") or [])[:8],
            "provider_readiness": list(provider_matrix.get("providers") or [])[:8],
            "evidence_first_operation": [
                "Capabilities are explained from live certifications and trust evidence.",
                "Provider readiness is one section, not the whole answer.",
                "Evidence first → capability second → authority last.",
            ],
            "read_only": True,
        }
    ]


def _first_mission_control_activation_packet(*, session_id: str) -> list[dict[str, Any]]:
    status = _step_status(step="first_mission_control_session", session_id=session_id)
    return [
        {
            "packet_id": "first-mission-control-activation-packet",
            "status": status,
            "guided_actions": [
                "Register project repository in Mission Control.",
                "Run readiness checks for the selected provider.",
                "View capability discovery and trust explanation reports.",
                "Start first governed workflow with explicit human approval at each gate.",
            ],
            "sample_first_run_prompts": [
                "show tenant onboarding",
                "what can you do?",
                "show capability registry",
                "show tenant dashboard",
            ],
            "automatic_provisioning_enabled": False,
            "onboarding_authority": False,
            "read_only": True,
        }
    ]


def build_tenant_onboarding_activation(*, session_id: str) -> TenantOnboardingActivationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    tenant_foundation = build_multi_tenant_platform_foundation(session_id=sid)
    foundation_payload = tenant_foundation.multi_tenant_platform_foundation or {}
    foundation_sections = foundation_payload.get("sections") or {}

    capability_runtime = build_capability_registry_runtime_integration(session_id=sid)
    capability_payload = capability_runtime.capability_registry_runtime_integration or {}
    capability_sections = capability_payload.get("sections") or {}
    provider_matrix = list(
        ((capability_sections.get("provider_capability_matrix") or [{}])[0]).get("providers") or []
    )

    records = list_tenant_onboarding_activation_records()
    progress = _onboarding_progress_registry(session_id=sid)
    organization_review = _organization_setup_review(records=records, session_id=sid)
    workspace_review = _workspace_setup_review(records=records, session_id=sid)
    project_review = _project_registration_review(records=records, session_id=sid)
    provider_checklist = _provider_connection_checklist(provider_matrix=provider_matrix)
    capability_report = _capability_discovery_report(capability_runtime=capability_payload)
    trust_report = _trust_explanation_report(
        tenant_foundation=foundation_payload,
        capability_runtime=capability_payload,
    )
    activation_packet = _first_mission_control_activation_packet(session_id=sid)

    dashboard = {
        "dashboard_id": "tenant-onboarding-dashboard",
        "onboarding_steps": list(ONBOARDING_STEPS),
        "progress": progress[0],
        "onboarding_authority": ONBOARDING_AUTHORITY_FIX_301,
        "automatic_provisioning_enabled": AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
        "secret_collection_enabled": SECRET_COLLECTION_ENABLED_FIX_301,
        "organization_count": (
            (foundation_sections.get("organization_registry") or [{}])[0].get("organization_count", 0)
        ),
        "read_only": True,
    }

    sections = {
        "tenant_onboarding_dashboard": [dashboard],
        "organization_setup_review": organization_review,
        "workspace_setup_review": workspace_review,
        "project_registration_review": project_review,
        "provider_connection_checklist": provider_checklist,
        "capability_discovery_report": capability_report,
        "trust_explanation_report": trust_report,
        "first_mission_control_activation_packet": activation_packet,
        "onboarding_progress_registry": progress,
        "human_onboarding_review": [
            {
                "review_id": "human-onboarding-review",
                "decisions_supported": [
                    "onboarding_decision_approve",
                    "onboarding_decision_hold",
                    "onboarding_decision_reject",
                    "onboarding_decision_defer",
                ],
                "onboarding_decision_approve": has_onboarding_decision_approve(session_id=sid),
                "automatic_provisioning_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_onboarding_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_ONBOARDING_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION,
        "fix": TENANT_ONBOARDING_ACTIVATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_301,
        "execution_performed": EXECUTION_PERFORMED_FIX_301,
        "onboarding_compose_artifacts_only": TENANT_ONBOARDING_COMPOSES_EVIDENCE_ONLY_FIX_301,
        "onboarding_authority": ONBOARDING_AUTHORITY_FIX_301,
        "automatic_provisioning_enabled": AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
        "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301,
        "secret_collection_enabled": SECRET_COLLECTION_ENABLED_FIX_301,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_301,
        "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_301,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_301,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_301,
        "invariant": TENANT_ONBOARDING_ACTIVATION_INVARIANT,
        "session_id": sid,
        "onboarding_steps": list(ONBOARDING_STEPS),
        "sections": sections,
        "operator_record_count": len(records),
        "onboarding_decision_approve": has_onboarding_decision_approve(session_id=sid),
        "fix_301_certification_requirements": list(FIX_301_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_multi_tenant_platform_foundation": True,
            "composes_fix_295_capability_registry": True,
            "composes_fix_296_runtime_capability_integration": True,
            "automatic_provisioning_performed": False,
            "secret_collection_performed": False,
            "provider_mutation_performed": False,
            "trust_mutation_performed": False,
        },
    }

    return TenantOnboardingActivationResult(
        ok=True,
        session_id=sid,
        tenant_onboarding_activation=payload,
        detail="Tenant onboarding activation composed from FIX 300 tenancy and FIX 295/296 capability evidence (guidance ≠ authority).",
    )
