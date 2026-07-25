# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — constitutional external-relations cognition from identity + boundary models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
    AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157,
    AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157,
    CONSTITUTIONAL_BOUNDARIES,
    EXTERNAL_PROVIDER_CATALOG,
    EXTERNAL_RELATIONS_PRINCIPLES,
    EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
    GOVERNANCE_MUTATION_PERFORMED_FIX_157,
    INSTITUTIONAL_EXTERNAL_RELATIONS_FIX,
    INSTITUTIONAL_EXTERNAL_RELATIONS_INVARIANT,
    INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_157,
    SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_157,
    TRUST_CLASSIFICATIONS,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_store import (
    list_institutional_external_relations_records,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_service import build_institutional_identity


@dataclass(frozen=True)
class InstitutionalExternalRelationsResult:
    ok: bool
    session_id: str
    external_relations: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _identity_sections(identity: dict[str, Any]) -> dict[str, Any]:
    return identity.get("sections") or {}


def _external_provider_relationship_models(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "provider_relationship")]
    catalog = [
        {
            "provider_id": pid,
            "lane": lane,
            "relationship_model": desc,
            "sovereignty_delegated": False,
            "source": "FIX_157_provider_catalog",
            "read_only": True,
        }
        for pid, lane, desc in EXTERNAL_PROVIDER_CATALOG
    ]
    return stored + catalog


def _constitutional_boundary_definitions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "boundary_definition")]
    boundaries = [
        {
            "boundary_id": bid,
            "definition": definition,
            "constitutional": True,
            "autonomous_negotiation": False,
            "source": "FIX_157_boundary_catalog",
            "read_only": True,
        }
        for bid, definition in CONSTITUTIONAL_BOUNDARIES
    ]
    return stored + boundaries


def _external_trust_classifications(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "trust_classification")]
    classifications = [
        {
            "classification_id": cid,
            "description": desc,
            "advisory_only": True,
            "sovereignty_impact": "none" if cid != "sovereign_internal" else "human_authority",
            "read_only": True,
        }
        for cid, desc in TRUST_CLASSIFICATIONS
    ]
    return stored + classifications


def _ecosystem_dependency_lineage(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "dependency_lineage")]
    lineage = [
        {
            "dependency_id": f"dep-{pid}",
            "provider": pid,
            "lane": lane,
            "lineage_depth": idx + 1,
            "dependency_type": "governed_external",
            "read_only": True,
        }
        for idx, (pid, lane, _) in enumerate(EXTERNAL_PROVIDER_CATALOG)
        if pid != "external_operators"
    ]
    return stored + lineage


def _external_governance_interaction_policies(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "interaction_policy")]
    policies = [
        {
            "policy_id": "chat_governed_provider_interaction",
            "policy": "All provider mutations flow through chat-governed approval — never direct UI mutation.",
            "executable": EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
            "read_only": True,
        },
        {
            "policy_id": "mission_control_observability_only",
            "policy": "Mission Control external-facing views remain read-only + governed approval.",
            "executable": EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
            "read_only": True,
        },
        {
            "policy_id": "no_autonomous_diplomacy",
            "policy": "External governance interaction is advisory — no autonomous institutional diplomacy.",
            "executable": EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
            "read_only": True,
        },
    ]
    return stored + policies


def _provider_sovereignty_boundaries(*, identity: dict[str, Any]) -> list[dict[str, Any]]:
    sovereignty_delegated = identity.get("governance_sovereignty_delegated", False)
    return [
        {
            "boundary_id": f"provider-{pid}",
            "provider": pid,
            "institutional_sovereignty_preserved": not sovereignty_delegated,
            "provider_authority_scope": "lane_governed_only" if pid != "external_operators" else "human_sovereign",
            "detail": "Provider sovereignty boundary — institutional constitutional integrity preserved.",
            "read_only": True,
        }
        for pid, _, _ in EXTERNAL_PROVIDER_CATALOG
    ]


def _constitutional_interoperability_analysis(*, identity: dict[str, Any]) -> list[dict[str, Any]]:
    purpose = _identity_sections(identity).get("governance_purpose_preservation") or []
    preserved_count = sum(1 for p in purpose if p.get("preserved"))
    return [
        {
            "analysis_id": "constitutional-interoperability",
            "internal_purpose_preserved": preserved_count,
            "external_boundary_count": len(CONSTITUTIONAL_BOUNDARIES),
            "interoperability_label": "aligned" if preserved_count >= 2 else "review_required",
            "detail": "Constitutional interoperability with external systems is advisory — human boundary decisions required.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _institutional_dependency_risk_analysis(*, identity: dict[str, Any]) -> list[dict[str, Any]]:
    drift = _identity_sections(identity).get("institutional_value_drift_detection") or []
    provider_count = len([p for p in EXTERNAL_PROVIDER_CATALOG if p[0] != "external_operators"])
    risk_level = "moderate" if provider_count >= 2 else "low"
    if any(d.get("signal") not in (None, "stable", "no-value-drift") for d in drift):
        risk_level = "elevated"
    return [
        {
            "risk_id": "ecosystem-dependency-risk",
            "provider_dependency_count": provider_count,
            "risk_level": risk_level,
            "detail": "Institutional dependency on external providers requires human governance oversight.",
            "autonomous_alignment": False,
            "read_only": True,
        }
    ]


def _external_influence_drift_detection(*, records: list[dict[str, Any]], identity: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "influence_observation")]
    value_drift = _identity_sections(identity).get("institutional_value_drift_detection") or []
    signals = list(stored)
    for drift in value_drift:
        if drift.get("drift_id") != "no-value-drift":
            signals.append(
                {
                    "influence_id": f"external-influence-{drift.get('drift_id')}",
                    "source": "identity_value_drift",
                    "detail": f"Potential external influence on institutional values: {drift.get('detail')}",
                    "recommendation_only": True,
                    "read_only": True,
                }
            )
    if not signals:
        signals.append(
            {
                "influence_id": "no-influence-drift",
                "detail": "No external influence drift detected against constitutional boundaries.",
                "read_only": True,
            }
        )
    return signals


def _cross_system_trust_continuity(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trust_records = _by_kind(records, "trust_classification")
    return [
        {
            "continuity_id": "cross-system-trust",
            "recorded_trust_classifications": len(trust_records),
            "catalog_classifications": len(TRUST_CLASSIFICATIONS),
            "sovereignty_delegated": False,
            "detail": "Cross-system trust continuity spans governed providers under constitutional boundary definitions.",
            "read_only": True,
        }
    ]


def build_institutional_external_relations(*, session_id: str) -> InstitutionalExternalRelationsResult:
    sid = (session_id or "default").strip()[:64] or "default"

    identity_result = build_institutional_identity(session_id=sid)
    identity = identity_result.identity if identity_result.ok else {}
    plan_id = str(identity.get("plan_id") or "") or None
    correlation_id = str(identity.get("correlation_id") or "") or None

    records = list_institutional_external_relations_records(session_id=sid, plan_id=plan_id)

    sections = {
        "external_provider_relationship_models": _external_provider_relationship_models(records=records),
        "constitutional_boundary_definitions": _constitutional_boundary_definitions(records=records),
        "external_trust_classifications": _external_trust_classifications(records=records),
        "ecosystem_dependency_lineage": _ecosystem_dependency_lineage(records=records),
        "external_governance_interaction_policies": _external_governance_interaction_policies(records=records),
        "provider_sovereignty_boundaries": _provider_sovereignty_boundaries(identity=identity),
        "constitutional_interoperability_analysis": _constitutional_interoperability_analysis(identity=identity),
        "institutional_dependency_risk_analysis": _institutional_dependency_risk_analysis(identity=identity),
        "external_influence_drift_detection": _external_influence_drift_detection(records=records, identity=identity),
        "cross_system_trust_continuity": _cross_system_trust_continuity(records=records),
    }

    external_relations: dict[str, Any] = {
        "schema_version": INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION,
        "fix": INSTITUTIONAL_EXTERNAL_RELATIONS_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_157,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_157,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
        "autonomous_external_negotiation_enabled": AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157,
        "autonomous_provider_alignment_enabled": AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157,
        "self_directed_institutional_diplomacy_enabled": SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_157,
        "invariant": INSTITUTIONAL_EXTERNAL_RELATIONS_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "external_relations_record_count": len(records),
        "all_recommendations_executable": False,
        "constitutional_external_relations_cognition": True,
        "external_relations_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in EXTERNAL_RELATIONS_PRINCIPLES
        ],
        "sources": {
            "institutional_identity": identity_result.ok,
            "external_relations_records": len(records),
        },
    }
    return InstitutionalExternalRelationsResult(
        ok=True,
        session_id=sid,
        external_relations=external_relations,
        detail="Institutional external relations assembled (recommendation-only — no autonomous negotiation or sovereignty delegation).",
    )
