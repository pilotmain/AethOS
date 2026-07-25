# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection experience service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_303_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
    AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
    EXECUTION_PERFORMED_FIX_303,
    FORBIDDEN_PROVIDER_CONNECTION_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_303,
    HUMAN_PROVIDER_CONNECTION_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_303,
    PERMISSION_ESCALATION_ENABLED_FIX_303,
    PHASE_1_PROVIDERS,
    PHASE_2_PROVIDERS,
    PROVIDER_CAPABILITY_UNLOCKS,
    PROVIDER_CONNECTION_AUTHORITY_FIX_303,
    PROVIDER_CONNECTION_COMPOSES_EVIDENCE_ONLY_FIX_303,
    PROVIDER_CONNECTION_EXPERIENCE_FIX,
    PROVIDER_CONNECTION_EXPERIENCE_INVARIANT,
    PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION,
    PROVIDER_MUTATION_AUTHORITY_FIX_303,
    SECRET_COLLECTION_ENABLED_FIX_303,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_evaluator import (
    build_provider_connection_report,
    evaluate_provider_readiness,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    has_provider_connection_decision_approve,
    list_provider_connection_experience_records,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)


@dataclass(frozen=True)
class ProviderConnectionExperienceResult:
    ok: bool
    session_id: str
    provider_connection_experience: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _provider_matrix_rows(capability_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sections = capability_payload.get("sections") or {}
    matrix = (sections.get("provider_capability_matrix") or [{}])[0]
    rows = list(matrix.get("providers") or [])
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row.get("provider") or "").strip()
        if name:
            by_name[name] = row
            by_name[name.lower()] = row
    return by_name


def build_provider_connection_experience(*, session_id: str) -> ProviderConnectionExperienceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_provider_connection_experience_records()

    capability = build_autonomous_capability_registry(session_id=sid)
    capability_payload = capability.autonomous_capability_registry or {}
    matrix_by_name = _provider_matrix_rows(capability_payload)

    build_tenant_onboarding_activation(session_id=sid)
    build_identity_access_hardening(session_id=sid)

    github_report = build_provider_connection_report(
        provider="GitHub",
        matrix_row=matrix_by_name.get("GitHub") or matrix_by_name.get("github"),
    )
    railway_report = build_provider_connection_report(
        provider="Railway",
        matrix_row=matrix_by_name.get("Railway") or matrix_by_name.get("railway"),
    )
    vercel_report = build_provider_connection_report(
        provider="Vercel",
        matrix_row=matrix_by_name.get("Vercel") or matrix_by_name.get("vercel"),
    )

    phase_1_readiness = [
        evaluate_provider_readiness(
            provider=provider,
            matrix_row=matrix_by_name.get(provider) or matrix_by_name.get(provider.lower()),
        )
        for provider in PHASE_1_PROVIDERS
    ]
    phase_2_planned = [
        {
            "provider": provider,
            "status": "PLANNED",
            "readiness": "planned",
            "connection_flow_available": False,
            "read_only": True,
        }
        for provider in PHASE_2_PROVIDERS
    ]

    unlock_matrix = [
        {
            "matrix_id": "provider-capability-unlock-matrix",
            "providers": [
                {
                    "provider": provider,
                    "capability_unlocks": list(unlocks),
                    "unlocks_after_manual_connection": True,
                    "read_only": True,
                }
                for provider, unlocks in PROVIDER_CAPABILITY_UNLOCKS
            ],
            "read_only": True,
        }
    ]

    permission_gaps = []
    for row in phase_1_readiness:
        if not row.get("permissions_sufficient"):
            permission_gaps.append(
                {
                    "provider": row.get("provider"),
                    "gap": "credentials_or_scopes_missing",
                    "setup_in": "Mission Control Mission Control → Advanced settings → Credentials",
                }
            )

    connected = [row for row in phase_1_readiness if row.get("provider_reachable")]
    dashboard = {
        "dashboard_id": "provider-connection-dashboard",
        "phase_1_providers": list(PHASE_1_PROVIDERS),
        "phase_2_providers": list(PHASE_2_PROVIDERS),
        "connected_provider_count": len(connected),
        "readiness_summary": [
            {
                "provider": row.get("provider"),
                "readiness": row.get("readiness"),
                "status": row.get("status"),
            }
            for row in phase_1_readiness
        ],
        "permission_gaps": permission_gaps,
        "trust_boundaries": [
            "All provider operations remain human-gated.",
            "Readonly visibility unlocks before any mutation path.",
            "Secrets are configured in Settings — never in chat.",
        ],
        "automatic_provider_connection_enabled": False,
        "read_only": True,
    }

    trust_explanation = [
        {
            "report_id": "provider-trust-explanation",
            "why_permissions_are_needed": [
                "Repository and deployment visibility require read-only provider scopes.",
                "Governed workflows need evidence from connected systems.",
            ],
            "what_aethos_can_access": [
                "Read-only inventory, logs, workflows, deployments, and environment metadata when connected.",
            ],
            "what_aethos_cannot_access": [
                "Automatic provisioning, hidden mutation, or secret collection in chat.",
                "Cross-tenant provider data or trust inheritance.",
            ],
            "human_approved_actions": [
                "Deploy, rollback, merge, restart, and credential mutation remain human-approved.",
            ],
            "secret_collection_in_chat_forbidden": True,
            "read_only": True,
        }
    ]

    sections = {
        "provider_connection_dashboard": [dashboard],
        "github_connection_report": [github_report],
        "railway_connection_report": [railway_report],
        "vercel_connection_report": [vercel_report],
        "provider_capability_unlock_matrix": unlock_matrix,
        "provider_connection_readiness_report": [
            {
                "report_id": "provider-connection-readiness-report",
                "phase_1": phase_1_readiness,
                "phase_2_planned": phase_2_planned,
                "evaluates": [
                    "credentials_present",
                    "permissions_sufficient",
                    "scopes_sufficient",
                    "provider_reachable",
                ],
                "read_only": True,
            }
        ],
        "provider_trust_explanation": trust_explanation,
        "human_provider_connection_review": [
            {
                "review_id": "human-provider-connection-review",
                "decisions_supported": list(HUMAN_PROVIDER_CONNECTION_DECISION_KINDS),
                "provider_connection_decision_approve": has_provider_connection_decision_approve(
                    session_id=sid
                ),
                "automatic_provider_connection_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_provider_connection_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PROVIDER_CONNECTION_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION,
        "fix": PROVIDER_CONNECTION_EXPERIENCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_303,
        "execution_performed": EXECUTION_PERFORMED_FIX_303,
        "provider_connection_compose_artifacts_only": PROVIDER_CONNECTION_COMPOSES_EVIDENCE_ONLY_FIX_303,
        "provider_connection_authority": PROVIDER_CONNECTION_AUTHORITY_FIX_303,
        "automatic_provider_connection_enabled": AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_303,
        "secret_collection_enabled": SECRET_COLLECTION_ENABLED_FIX_303,
        "permission_escalation_enabled": PERMISSION_ESCALATION_ENABLED_FIX_303,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_303,
        "invariant": PROVIDER_CONNECTION_EXPERIENCE_INVARIANT,
        "session_id": sid,
        "sections": sections,
        "operator_record_count": len(records),
        "provider_connection_decision_approve": has_provider_connection_decision_approve(session_id=sid),
        "fix_303_certification_requirements": list(FIX_303_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_295_provider_capability_matrix": True,
            "composes_fix_301_onboarding_provider_checklist": True,
            "composes_fix_302_authorization_context": True,
            "automatic_provider_connection_performed": False,
            "secret_collection_performed": False,
            "provider_mutation_performed": False,
        },
    }

    return ProviderConnectionExperienceResult(
        ok=True,
        session_id=sid,
        provider_connection_experience=payload,
        detail="Provider connection experience composed from live readiness evidence (guidance ≠ mutation).",
    )
