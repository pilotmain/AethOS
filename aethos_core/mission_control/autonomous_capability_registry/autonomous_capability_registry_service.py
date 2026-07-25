# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — autonomous capability registry service."""

from __future__ import annotations

import inspect
import re
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import aethos_core.governance.governance_friction_approval_contract as governance_contract
from aethos_core.credentials.provider_alias_resolution import env_token_for_canonical_provider
from aethos_core.governance.governance_friction_approval_contract import FIX_295_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
    AUTONOMOUS_CAPABILITY_REGISTRY_COMPOSES_EVIDENCE_ONLY_FIX_295,
    AUTONOMOUS_CAPABILITY_REGISTRY_FIX,
    AUTONOMOUS_CAPABILITY_REGISTRY_INVARIANT,
    AUTONOMOUS_CAPABILITY_REGISTRY_PRINCIPLES,
    AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION,
    CAPABILITY_AUTHORITY_FIX_295,
    CAPABILITY_DOMAINS,
    CAPABILITY_STATUSES,
    DEPLOYMENT_AUTHORITY_FIX_295,
    EXECUTION_PERFORMED_FIX_295,
    FORBIDDEN_CAPABILITY_REGISTRY_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_295,
    GOVERNANCE_MUTATION_PERFORMED_FIX_295,
    HUMAN_CAPABILITY_REVIEW_KINDS,
    MERGE_AUTHORITY_FIX_295,
    MUTATION_PERFORMED_FIX_295,
    PLATFORM_CAPABILITIES,
    PROVIDER_CAPABILITIES,
    PROVIDER_MUTATION_AUTHORITY_FIX_295,
    REPOSITORY_MUTATION_AUTHORITY_FIX_295,
    SELF_AUTHORITY_GRANTING_ENABLED_FIX_295,
    ROLLBACK_AUTHORITY_FIX_295,
    TRUST_MUTATION_AUTHORITY_FIX_295,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_store import (
    has_human_capability_review_approve,
    list_autonomous_capability_registry_records,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.mission_control_ui_freeze_contract import (
    ALLOWED_MC_OPERATOR_HTTP_ROUTES,
)
from aethos_core.provider.completion import provider_configured
from aethos_core.runtime.authority import authority

_FIX_CERT_RX = re.compile(r"^FIX_(\d+[A-Z]?)_CERTIFICATION_REQUIREMENTS$")
_STATUS_MATURITY: dict[str, float] = {
    "PLANNED": 20.0,
    "EXPERIMENTAL": 40.0,
    "IMPLEMENTED": 65.0,
    "PROVEN": 80.0,
    "CONDITIONALLY_TRUSTED": 85.0,
    "OPERATIONAL": 90.0,
    "DEPRECATED": 15.0,
    "BLOCKED": 10.0,
}


@dataclass(frozen=True)
class AutonomousCapabilityRegistryResult:
    ok: bool
    session_id: str
    autonomous_capability_registry: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _maturity_tier(score: float) -> str:
    if score >= 85:
        return "MATURE"
    if score >= 70:
        return "ESTABLISHED"
    if score >= 50:
        return "DEVELOPING"
    if score >= 30:
        return "EARLY"
    return "UNPROVEN"


def _discover_fix_certifications() -> dict[str, tuple[str, ...]]:
    discovered: dict[str, tuple[str, ...]] = {}
    for name, value in inspect.getmembers(governance_contract):
        match = _FIX_CERT_RX.match(name)
        if not match or not isinstance(value, tuple):
            continue
        fix_label = f"FIX {match.group(1)}"
        discovered[fix_label] = tuple(str(item) for item in value)
    return discovered


def _frozen_api_paths() -> set[str]:
    return {path for _method, path in ALLOWED_MC_OPERATOR_HTTP_ROUTES}


def _capability_route(path_fragment: str, *, frozen_paths: set[str]) -> str | None:
    for path in frozen_paths:
        if path_fragment in path:
            return path
    return None


def _derive_status(
    *,
    capability_id: str,
    fix_ref: str,
    certified_fixes: dict[str, tuple[str, ...]],
    frozen_paths: set[str],
    provider_ready: bool | None,
) -> str:
    if fix_ref == "PLANNED" or capability_id == "enterprise_operating_system":
        return "PLANNED"
    if fix_ref in certified_fixes:
        route = _capability_route(capability_id.replace("_", "-"), frozen_paths=frozen_paths)
        if route:
            if capability_id.startswith("provider_"):
                if provider_ready is True:
                    return "OPERATIONAL"
                if provider_ready is False:
                    return "EXPERIMENTAL"
            if "trust" in capability_id or fix_ref in {"FIX 186", "FIX 192", "FIX 193", "FIX 196"}:
                return "IMPLEMENTED"
            return "PROVEN"
        return "IMPLEMENTED"
    if capability_id.startswith("provider_"):
        return "EXPERIMENTAL" if provider_ready else "BLOCKED"
    return "EXPERIMENTAL"


def _provider_readiness_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for provider in PROVIDER_CAPABILITIES:
        token = env_token_for_canonical_provider(provider) if provider in {"railway", "github", "vercel"} else None
        cli_ready = provider == "vercel" and shutil.which("vercel") is not None
        configured = bool(token) or cli_ready
        if provider in {"aws", "gcp", "azure", "kubernetes"}:
            status = "PLANNED"
            readiness = "planned"
        elif configured:
            status = "OPERATIONAL"
            readiness = "ready"
        else:
            status = "EXPERIMENTAL"
            readiness = "not_configured"
        rows.append(
            {
                "provider": provider,
                "status": status,
                "readiness": readiness,
                "token_configured": bool(token),
                "cli_available": cli_ready,
                "authority_level": "human_gated_readonly",
                "read_only": True,
            }
        )
    return rows


def _repository_trust_matrix(
    *,
    validation_sections: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = list(validation_sections.get("cross_repository_validation_matrix") or [])
    if rows:
        return [
            {
                "repository": row.get("repository"),
                "display_name": row.get("display_name") or row.get("repository"),
                "trust_state": row.get("trust_state"),
                "validation_state": row.get("validation_state"),
                "pilot_arc_state": row.get("pilot_arc_state"),
                "read_only": True,
            }
            for row in rows
        ]
    return [
        {
            "repository": row.get("repository"),
            "display_name": row.get("display_name") or row.get("repository"),
            "trust_state": row.get("trust_state"),
            "validation_state": row.get("program_visibility"),
            "pilot_arc_state": row.get("pilot_arc_state"),
            "read_only": True,
        }
        for row in validation_sections.get("program_delivery_visibility") or []
    ]


def _build_capability_entries(
    *,
    certified_fixes: dict[str, tuple[str, ...]],
    frozen_paths: set[str],
    provider_matrix: list[dict[str, Any]],
    capability_records: list[dict[str, Any]],
    trust_matrix: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    provider_status = {row["provider"]: row["status"] for row in provider_matrix}
    trusted_repos = {
        str(row.get("repository") or ""): str(row.get("trust_state") or "")
        for row in trust_matrix
    }
    entries: list[dict[str, Any]] = []

    for cap_id, name, domain, fix_ref, description in PLATFORM_CAPABILITIES:
        provider_ready: bool | None = None
        if cap_id.startswith("provider_"):
            provider_key = cap_id.replace("provider_", "")
            provider_ready = provider_status.get(provider_key) in {"OPERATIONAL", "PROVEN"}

        status = _derive_status(
            capability_id=cap_id,
            fix_ref=fix_ref,
            certified_fixes=certified_fixes,
            frozen_paths=frozen_paths,
            provider_ready=provider_ready,
        )
        if status == "PROVEN" and any(
            trusted_repos.get(repo) == "CONDITIONALLY_TRUSTED"
            for repo in trusted_repos
            if "trust" in cap_id or "stewardship" in cap_id or "lifecycle" in cap_id
        ):
            status = "CONDITIONALLY_TRUSTED"

        evidence: list[str] = []
        if fix_ref in certified_fixes:
            evidence.append(f"fix_certification:{fix_ref}")
            evidence.extend(list(certified_fixes[fix_ref][:2]))
        route = _capability_route(cap_id.replace("_", "-"), frozen_paths=frozen_paths)
        if route:
            evidence.append(f"operator_api:{route}")
        note_count = sum(
            1
            for record in capability_records
            if record.get("capability_id") == cap_id or cap_id in str(record.get("content") or "")
        )
        if note_count:
            evidence.append(f"operator_notes:{note_count}")

        maturity_score = _STATUS_MATURITY.get(status, 30.0)
        entries.append(
            {
                "capability_id": cap_id,
                "name": name,
                "domain": domain,
                "description": description,
                "status": status,
                "maturity": _maturity_tier(maturity_score),
                "maturity_score": maturity_score,
                "evidence": evidence,
                "evidence_confidence_score": min(100.0, 35.0 + len(evidence) * 12),
                "trust_level": "CONDITIONALLY_TRUSTED" if status == "CONDITIONALLY_TRUSTED" else "ADVISORY",
                "authority_level": "none",
                "last_validation": fix_ref if fix_ref in certified_fixes else "operator_observation",
                "operator_note_count": note_count,
                "read_only": True,
            }
        )
    return entries


def _domain_report(
    *,
    domain: str,
    capabilities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_caps = [cap for cap in capabilities if cap.get("domain") == domain]
    proven = [cap for cap in domain_caps if cap.get("status") in {"PROVEN", "CONDITIONALLY_TRUSTED", "OPERATIONAL"}]
    return [
        {
            "report_id": f"{domain.replace('_', '-')}-capability-report",
            "domain": domain,
            "capability_count": len(domain_caps),
            "proven_count": len(proven),
            "top_capabilities": domain_caps[:8],
            "read_only": True,
        }
    ]


def _capability_evidence_registry(
    *,
    certified_fixes: dict[str, tuple[str, ...]],
    capabilities: list[dict[str, Any]],
    capability_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for fix_label, requirements in sorted(certified_fixes.items()):
        artifacts.append(
            {
                "artifact_id": f"cert-{fix_label.replace(' ', '-').lower()}",
                "artifact_type": "fix_certification",
                "source": fix_label,
                "requirement_count": len(requirements),
                "sample_requirements": list(requirements[:3]),
                "read_only": True,
            }
        )
    for cap in capabilities[:15]:
        if cap.get("evidence"):
            artifacts.append(
                {
                    "artifact_id": f"capability-evidence-{cap.get('capability_id')}",
                    "artifact_type": "capability_evidence",
                    "source": cap.get("capability_id"),
                    "status": cap.get("status"),
                    "evidence": cap.get("evidence"),
                    "read_only": True,
                }
            )
    for record in capability_records[-10:]:
        artifacts.append(
            {
                "artifact_id": f"operator-{record.get('recorded_at', 'note')}",
                "artifact_type": "human_decision" if str(record.get("kind", "")).startswith("human_") else "operator_note",
                "source": record.get("kind"),
                "content": record.get("content"),
                "read_only": True,
            }
        )
    return [
        {
            "registry_id": "capability-evidence-registry",
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "read_only": True,
        }
    ]


def _capability_maturity_dashboard(*, capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not capabilities:
        return []
    maturity_scores = [float(cap.get("maturity_score") or 0) for cap in capabilities]
    evidence_scores = [float(cap.get("evidence_confidence_score") or 0) for cap in capabilities]
    trust_scores = [
        85.0 if cap.get("trust_level") == "CONDITIONALLY_TRUSTED" else 55.0 for cap in capabilities
    ]
    operational_scores = [
        90.0 if cap.get("status") == "OPERATIONAL" else float(cap.get("maturity_score") or 0)
        for cap in capabilities
    ]
    overall_maturity = round(sum(maturity_scores) / len(maturity_scores), 1)
    return [
        {
            "dashboard_id": "capability-maturity-dashboard",
            "capability_maturity_score": overall_maturity,
            "capability_maturity_tier": _maturity_tier(overall_maturity),
            "evidence_confidence_score": round(sum(evidence_scores) / len(evidence_scores), 1),
            "trust_confidence_score": round(sum(trust_scores) / len(trust_scores), 1),
            "operational_readiness_score": round(sum(operational_scores) / len(operational_scores), 1),
            "capability_count": len(capabilities),
            "read_only": True,
        }
    ]


def _capability_drift_report(
    *,
    certified_fixes: dict[str, tuple[str, ...]],
    capabilities: list[dict[str, Any]],
    frozen_paths: set[str],
) -> list[dict[str, Any]]:
    catalog_fixes = {fix_ref for _cid, _name, _domain, fix_ref, _desc in PLATFORM_CAPABILITIES if fix_ref != "PLANNED"}
    certified = set(certified_fixes)
    implemented_without_route: list[str] = []
    certified_not_surfaced: list[str] = []
    planned_overstated: list[str] = []

    for cap in capabilities:
        cap_id = str(cap.get("capability_id") or "")
        status = str(cap.get("status") or "")
        route = _capability_route(cap_id.replace("_", "-"), frozen_paths=frozen_paths)
        if status in {"IMPLEMENTED", "PROVEN", "OPERATIONAL"} and not route and cap_id not in {
            "trust_systems",
            "approval_systems",
            "lane_systems",
        }:
            implemented_without_route.append(cap_id)
        if status == "PLANNED" and any(fix in str(cap.get("last_validation") or "") for fix in certified):
            planned_overstated.append(cap_id)

    for fix_label in sorted(certified):
        if fix_label not in catalog_fixes and fix_label not in {"FIX 135", "FIX 136"}:
            certified_not_surfaced.append(fix_label)

    drift_items = []
    for cap_id in implemented_without_route[:5]:
        drift_items.append(
            {
                "drift_id": f"implemented-not-surfaced-{cap_id}",
                "drift_type": "implemented_but_not_surfaced",
                "subject": cap_id,
                "detail": "Capability is implemented/certified but lacks a dedicated operator API route.",
                "read_only": True,
            }
        )
    for fix_label in certified_not_surfaced[:5]:
        drift_items.append(
            {
                "drift_id": f"certified-not-cataloged-{fix_label.replace(' ', '-')}",
                "drift_type": "certified_but_not_cataloged",
                "subject": fix_label,
                "detail": "FIX certification exists but capability is not represented in the platform catalog.",
                "read_only": True,
            }
        )
    for cap_id in planned_overstated[:5]:
        drift_items.append(
            {
                "drift_id": f"planned-overstated-{cap_id}",
                "drift_type": "planned_but_overstated",
                "subject": cap_id,
                "detail": "Capability marked planned despite existing certification evidence.",
                "read_only": True,
            }
        )

    return [
        {
            "report_id": "capability-drift-report",
            "drift_count": len(drift_items),
            "implemented_without_route_count": len(implemented_without_route),
            "certified_not_cataloged_count": len(certified_not_surfaced),
            "planned_overstated_count": len(planned_overstated),
            "drift_items": drift_items,
            "read_only": True,
        }
    ]


def _self_awareness_report(
    *,
    capabilities: list[dict[str, Any]],
    provider_matrix: list[dict[str, Any]],
    trust_matrix: list[dict[str, Any]],
    maturity_dashboard: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    can_do = [
        f"{cap.get('name')} ({cap.get('status')})"
        for cap in capabilities
        if cap.get("status") in {"IMPLEMENTED", "PROVEN", "CONDITIONALLY_TRUSTED", "OPERATIONAL"}
    ]
    cant_do = [
        action
        for action, _detail in FORBIDDEN_CAPABILITY_REGISTRY_ACTIONS[:6]
    ] + [
        f"{cap.get('name')} — not available ({cap.get('status')})"
        for cap in capabilities
        if cap.get("status") in {"PLANNED", "BLOCKED", "DEPRECATED"}
    ]
    proven = [cap.get("name") for cap in capabilities if cap.get("status") in {"PROVEN", "CONDITIONALLY_TRUSTED", "OPERATIONAL"}]
    experimental = [cap.get("name") for cap in capabilities if cap.get("status") == "EXPERIMENTAL"]
    trusted = [
        f"{row.get('display_name') or row.get('repository')} ({row.get('trust_state')})"
        for row in trust_matrix
        if row.get("trust_state") == "CONDITIONALLY_TRUSTED"
    ]
    planned = [cap.get("name") for cap in capabilities if cap.get("status") == "PLANNED"]
    providers = [
        f"{row.get('provider')} — {row.get('readiness')} ({row.get('status')})"
        for row in provider_matrix
    ]
    maturity = maturity_dashboard[0] if maturity_dashboard else {}

    return [
        {
            "report_id": "self-awareness-report",
            "what_can_you_do": can_do[:12],
            "what_cant_you_do": cant_do[:12],
            "what_is_proven": proven[:12],
            "what_is_experimental": experimental[:12],
            "what_is_trusted": trusted[:12],
            "what_is_planned": planned[:12],
            "supported_providers": providers,
            "trusted_repositories": trusted[:12],
            "capability_maturity_tier": maturity.get("capability_maturity_tier"),
            "answers_from_live_evidence": True,
            "read_only": True,
        }
    ]


def build_autonomous_capability_registry(*, session_id: str) -> AutonomousCapabilityRegistryResult:
    sid = (session_id or "default").strip()[:64] or "default"
    capability_records = list_autonomous_capability_registry_records()
    human_approved = has_human_capability_review_approve(session_id=sid)

    certified_fixes = _discover_fix_certifications()
    frozen_paths = _frozen_api_paths()
    provider_matrix = _provider_readiness_matrix()

    validation = build_cross_repository_multi_agent_delivery_validation(session_id=sid)
    validation_payload = validation.cross_repository_multi_agent_delivery_validation or {}
    validation_sections = validation_payload.get("sections") or {}

    trust_matrix = _repository_trust_matrix(validation_sections=validation_sections)
    if not trust_matrix:
        engineering = build_multi_repository_engineering_intelligence(session_id=sid)
        engineering_sections = engineering.multi_repository_engineering_intelligence.get("sections") or {}
        trust_matrix = [
            {
                "repository": row.get("repository"),
                "display_name": row.get("display_name") or row.get("repository"),
                "trust_state": row.get("trust_state"),
                "validation_state": row.get("program_visibility"),
                "read_only": True,
            }
            for row in engineering_sections.get("program_delivery_visibility") or []
        ]

    capabilities = _build_capability_entries(
        certified_fixes=certified_fixes,
        frozen_paths=frozen_paths,
        provider_matrix=provider_matrix,
        capability_records=capability_records,
        trust_matrix=trust_matrix,
    )
    evidence_registry = _capability_evidence_registry(
        certified_fixes=certified_fixes,
        capabilities=capabilities,
        capability_records=capability_records,
    )
    maturity_dashboard = _capability_maturity_dashboard(capabilities=capabilities)
    drift_report = _capability_drift_report(
        certified_fixes=certified_fixes,
        capabilities=capabilities,
        frozen_paths=frozen_paths,
    )
    self_awareness = _self_awareness_report(
        capabilities=capabilities,
        provider_matrix=provider_matrix,
        trust_matrix=trust_matrix,
        maturity_dashboard=maturity_dashboard,
    )

    domain_reports = {
        "governance_capability_report": _domain_report(domain="governance", capabilities=capabilities),
        "delivery_capability_report": _domain_report(domain="delivery", capabilities=capabilities),
        "operations_capability_report": _domain_report(domain="operations", capabilities=capabilities),
        "intelligence_capability_report": _domain_report(domain="intelligence", capabilities=capabilities),
        "provider_capability_report": _domain_report(domain="provider", capabilities=capabilities),
    }

    runtime_caps = authority.capabilities
    sections = {
        **domain_reports,
        "capability_registry": [
            {
                "registry_id": "capability-registry",
                "capability_count": len(capabilities),
                "status_values": list(CAPABILITY_STATUSES),
                "capabilities": capabilities,
                "read_only": True,
            }
        ],
        "capability_evidence_registry": evidence_registry,
        "capability_maturity_dashboard": maturity_dashboard,
        "capability_drift_report": drift_report,
        "self_awareness_report": self_awareness,
        "provider_capability_matrix": [
            {
                "matrix_id": "provider-capability-matrix",
                "provider_count": len(provider_matrix),
                "providers": provider_matrix,
                "generative_intelligence_ready": provider_configured(),
                "runtime_capabilities": {
                    **runtime_caps,
                    "generative_intelligence_ready": provider_configured(),
                },
                "read_only": True,
            }
        ],
        "repository_trust_matrix": [
            {
                "matrix_id": "repository-trust-matrix",
                "repository_count": len(trust_matrix),
                "repositories": trust_matrix,
                "read_only": True,
            }
        ],
        "capability_dashboard": [
            {
                "dashboard_id": "capability-dashboard",
                "capability_domains": list(CAPABILITY_DOMAINS),
                "top_capabilities": sorted(
                    capabilities,
                    key=lambda cap: float(cap.get("maturity_score") or 0),
                    reverse=True,
                )[:8],
                "overall_maturity": (maturity_dashboard[0] if maturity_dashboard else {}).get(
                    "capability_maturity_tier"
                ),
                "drift_count": (drift_report[0] if drift_report else {}).get("drift_count", 0),
                "trusted_repository_count": sum(
                    1 for row in trust_matrix if row.get("trust_state") == "CONDITIONALLY_TRUSTED"
                ),
                "provider_ready_count": sum(
                    1 for row in provider_matrix if row.get("readiness") == "ready"
                ),
                "human_capability_review_approve": human_approved,
                "read_only": True,
            }
        ],
        "human_capability_review": [
            {
                "review_id": "human-capability-review",
                "decisions_supported": list(HUMAN_CAPABILITY_REVIEW_KINDS),
                "human_capability_review_approve": human_approved,
                "execution_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_capability_registry_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_CAPABILITY_REGISTRY_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION,
        "fix": AUTONOMOUS_CAPABILITY_REGISTRY_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_295,
        "execution_performed": EXECUTION_PERFORMED_FIX_295,
        "capability_compose_artifacts_only": AUTONOMOUS_CAPABILITY_REGISTRY_COMPOSES_EVIDENCE_ONLY_FIX_295,
        "capability_authority": CAPABILITY_AUTHORITY_FIX_295,
        "self_authority_granting_enabled": SELF_AUTHORITY_GRANTING_ENABLED_FIX_295,
        "automatic_capability_promotion_enabled": AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_295,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_295,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_295,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_295,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_295,
        "merge_authority": MERGE_AUTHORITY_FIX_295,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_295,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_295,
        "invariant": AUTONOMOUS_CAPABILITY_REGISTRY_INVARIANT,
        "session_id": sid,
        "capability_domains": list(CAPABILITY_DOMAINS),
        "certified_fix_count": len(certified_fixes),
        "sections": sections,
        "operator_record_count": len(capability_records),
        "human_capability_review_approve": human_approved,
        "fix_295_certification_requirements": list(FIX_295_CERTIFICATION_REQUIREMENTS),
        "autonomous_capability_registry_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in AUTONOMOUS_CAPABILITY_REGISTRY_PRINCIPLES
        ],
        "sources": {
            "composes_fix_certifications_dynamically": True,
            "composes_fix_191_cross_repository_validation": True,
            "composes_fix_260_multi_repository_engineering_intelligence": True,
            "composes_frozen_operator_api_surface": True,
            "composes_provider_readiness": True,
            "pilot_reexecution_performed": False,
            "capability_self_modification_performed": False,
            "authority_escalation_performed": False,
        },
    }

    return AutonomousCapabilityRegistryResult(
        ok=True,
        session_id=sid,
        autonomous_capability_registry=payload,
        detail="Autonomous capability registry composed from live platform evidence (capability awareness ≠ authority).",
    )
