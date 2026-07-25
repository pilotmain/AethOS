# SPDX-License-Identifier: Apache-2.0
"""FIX 296 — capability registry runtime integration service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_296_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
    FORBIDDEN_CAPABILITY_REGISTRY_ACTIONS,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296,
    CAPABILITY_ANSWERING_AUTHORITY_FIX_296,
    CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX,
    CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_INVARIANT,
    EXPERIMENTAL_STATUSES,
    OPERATIONAL_STATUSES,
    PLANNED_STATUSES,
    PLATFORM_CAPABILITY_SECTIONS,
    PROVEN_STATUSES,
    PROVIDER_AUTHORITY_FIX_296,
    RUNTIME_ANSWER_SECTIONS,
    TRUST_MUTATION_AUTHORITY_FIX_296,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)


@dataclass(frozen=True)
class CapabilityRegistryRuntimeIntegrationResult:
    ok: bool
    session_id: str
    capability_registry_runtime_integration: dict[str, Any] = field(default_factory=dict)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _capability_lines(capabilities: list[dict[str, Any]], *, statuses: frozenset[str]) -> list[str]:
    lines: list[str] = []
    for cap in capabilities:
        if str(cap.get("status") or "") not in statuses:
            continue
        lines.append(f"{cap.get('name')} ({cap.get('status')})")
    return lines


def _platform_domain_sections(
    *,
    capabilities: list[dict[str, Any]],
    tenant_dashboard: dict[str, Any],
) -> dict[str, list[str]]:
    by_id = {str(cap.get("capability_id") or ""): cap for cap in capabilities}

    def _names(*cap_ids: str) -> list[str]:
        out: list[str] = []
        for cap_id in cap_ids:
            cap = by_id.get(cap_id)
            if cap:
                out.append(f"{cap.get('name')} ({cap.get('status')})")
        return out

    governance = _capability_lines(
        [cap for cap in capabilities if cap.get("domain") == "governance"],
        statuses=PROVEN_STATUSES | EXPERIMENTAL_STATUSES | OPERATIONAL_STATUSES | PLANNED_STATUSES,
    )
    delivery = _capability_lines(
        [cap for cap in capabilities if cap.get("domain") == "delivery"],
        statuses=PROVEN_STATUSES | EXPERIMENTAL_STATUSES | OPERATIONAL_STATUSES | PLANNED_STATUSES,
    )
    operations = _capability_lines(
        [cap for cap in capabilities if cap.get("domain") == "operations"],
        statuses=PROVEN_STATUSES | EXPERIMENTAL_STATUSES | OPERATIONAL_STATUSES | PLANNED_STATUSES,
    )

    return {
        "governance": governance[:8],
        "software_delivery": delivery[:8],
        "operations": operations[:8],
        "repository_intelligence": _names("repository_intelligence"),
        "product_intelligence": _names(
            "portfolio_intelligence",
            "product_evolution",
            "product_stewardship",
        ),
        "lifecycle_and_business_intelligence": _names(
            "lifecycle_management",
            "business_operating_system",
            "capability_registry",
        ),
        "multi_tenant_platform_readiness": [
            f"Organizations: {tenant_dashboard.get('organization_count', 0)}",
            f"Workspaces: {tenant_dashboard.get('workspace_count', 0)}",
            f"Projects: {tenant_dashboard.get('project_count', 0)}",
            f"Users: {tenant_dashboard.get('user_count', 0)}",
            "Multi-tenant foundation (FIX 300) composed read-only",
        ],
        "provider_readiness": _capability_lines(
            [cap for cap in capabilities if cap.get("domain") == "provider"],
            statuses=PROVEN_STATUSES | EXPERIMENTAL_STATUSES | OPERATIONAL_STATUSES | PLANNED_STATUSES,
        )[:8],
        "limitations": [],
    }


def build_capability_registry_runtime_integration(
    *, session_id: str
) -> CapabilityRegistryRuntimeIntegrationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    capability = build_autonomous_capability_registry(session_id=sid)
    capability_payload = capability.autonomous_capability_registry or {}
    capability_sections = capability_payload.get("sections") or {}
    registry = (capability_sections.get("capability_registry") or [{}])[0]
    capabilities = list(registry.get("capabilities") or [])
    self_awareness = (capability_sections.get("self_awareness_report") or [{}])[0]
    provider_matrix = (capability_sections.get("provider_capability_matrix") or [{}])[0]
    trust_matrix = (capability_sections.get("repository_trust_matrix") or [{}])[0]
    maturity = (capability_sections.get("capability_maturity_dashboard") or [{}])[0]

    tenant = build_multi_tenant_platform_foundation(session_id=sid)
    tenant_dashboard = (
        (tenant.multi_tenant_platform_foundation.get("sections") or {}).get("tenant_dashboard", [{}])[0]
    )

    platform_domains = _platform_domain_sections(
        capabilities=capabilities,
        tenant_dashboard=tenant_dashboard,
    )
    platform_domains["limitations"] = list(self_awareness.get("what_cant_you_do") or [])[:8]

    proven = _capability_lines(capabilities, statuses=PROVEN_STATUSES)
    operational = _capability_lines(capabilities, statuses=OPERATIONAL_STATUSES)
    experimental = _capability_lines(capabilities, statuses=EXPERIMENTAL_STATUSES)
    planned = _capability_lines(capabilities, statuses=PLANNED_STATUSES)

    authority_boundaries = [
        detail for _aid, detail in FORBIDDEN_CAPABILITY_REGISTRY_ACTIONS[:8]
    ] + [
        "Capability answering explains platform evidence only.",
        "No autonomous merge, deploy, rollback, billing, customer mutation, or tenant provisioning authority.",
    ]

    sections = {
        "capability_summary": [
            {
                "summary_id": "capability-summary",
                "overall_maturity_tier": maturity.get("capability_maturity_tier"),
                "capability_count": registry.get("capability_count", 0),
                "platform_domains": list(PLATFORM_CAPABILITY_SECTIONS),
                "answers_from_live_evidence": True,
                "provider_only_answer_forbidden": True,
                "read_only": True,
            }
        ],
        "platform_capability_domains": [
            {
                "section_id": "platform-capability-domains",
                "domains": platform_domains,
                "read_only": True,
            }
        ],
        "proven_capabilities": [
            {
                "section_id": "proven-capabilities",
                "items": proven[:12],
                "trusted_repositories": list(self_awareness.get("what_is_trusted") or [])[:12],
                "read_only": True,
            }
        ],
        "operational_capabilities": [
            {
                "section_id": "operational-capabilities",
                "items": operational[:12] or proven[:8],
                "runtime_capabilities": provider_matrix.get("runtime_capabilities") or {},
                "read_only": True,
            }
        ],
        "experimental_capabilities": [
            {
                "section_id": "experimental-capabilities",
                "items": experimental[:12] or list(self_awareness.get("what_is_experimental") or [])[:12],
                "read_only": True,
            }
        ],
        "planned_blocked_capabilities": [
            {
                "section_id": "planned-blocked-capabilities",
                "items": planned[:12] or list(self_awareness.get("what_is_planned") or [])[:12],
                "read_only": True,
            }
        ],
        "provider_capability_matrix": [provider_matrix],
        "repository_trust_matrix": [trust_matrix],
        "authority_boundaries": [
            {
                "section_id": "authority-boundaries",
                "boundaries": authority_boundaries,
                "capability_authority": CAPABILITY_ANSWERING_AUTHORITY_FIX_296,
                "automatic_capability_promotion_enabled": AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296,
                "read_only": True,
            }
        ],
    }

    payload: dict[str, Any] = {
        "fix": CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "capability_answering_authority": CAPABILITY_ANSWERING_AUTHORITY_FIX_296,
        "automatic_capability_promotion_enabled": AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_296,
        "provider_authority": PROVIDER_AUTHORITY_FIX_296,
        "mutation_performed": False,
        "execution_performed": False,
        "invariant": CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_INVARIANT,
        "session_id": sid,
        "runtime_answer_sections": list(RUNTIME_ANSWER_SECTIONS),
        "sections": sections,
        "self_awareness_report": self_awareness,
        "fix_296_certification_requirements": list(FIX_296_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_295_capability_registry": True,
            "composes_fix_300_multi_tenant_platform_foundation": True,
            "static_provider_only_answer_forbidden": True,
            "provider_only_answer_forbidden": True,
        },
    }

    return CapabilityRegistryRuntimeIntegrationResult(
        ok=True,
        session_id=sid,
        capability_registry_runtime_integration=payload,
        detail="Capability registry runtime integration composed from FIX 295 evidence (answering ≠ authority).",
    )


def compose_capability_runtime_reply(*, session_id: str = "default") -> str:
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_renderer import (
        render_capability_registry_runtime_integration,
    )

    result = build_capability_registry_runtime_integration(session_id=session_id)
    return render_capability_registry_runtime_integration(result.capability_registry_runtime_integration)
