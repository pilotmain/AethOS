# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — institutional existential continuity cognition from external relations + identity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
    AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158,
    AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158,
    CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158,
    EXISTENTIAL_RISK_PRINCIPLES,
    EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
    EXTINCTION_PATH_CATALOG,
    FRAGILITY_INDICATORS,
    GOVERNANCE_COLLAPSE_SCENARIOS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_158,
    INSTITUTIONAL_EXISTENTIAL_RISK_FIX,
    INSTITUTIONAL_EXISTENTIAL_RISK_INVARIANT,
    INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION,
    INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158,
    MUTATION_PERFORMED_FIX_158,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_store import (
    list_institutional_existential_risk_records,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
    build_institutional_external_relations,
)


@dataclass(frozen=True)
class InstitutionalExistentialRiskResult:
    ok: bool
    session_id: str
    existential_risk: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _external_sections(external_relations: dict[str, Any]) -> dict[str, Any]:
    return external_relations.get("sections") or {}


def _constitutional_continuity_risk_analysis(
    *, records: list[dict[str, Any]], external_relations: dict[str, Any]
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "continuity_risk_observation")]
    dependency_risk = _external_sections(external_relations).get("institutional_dependency_risk_analysis") or []
    risk_level = dependency_risk[0].get("risk_level", "unknown") if dependency_risk else "unknown"
    baseline = [
        {
            "risk_id": "constitutional-continuity-risk",
            "risk_level": risk_level,
            "external_boundary_count": len(
                _external_sections(external_relations).get("constitutional_boundary_definitions") or []
            ),
            "detail": "Constitutional continuity risk analysis — advisory only, no autonomous mitigation.",
            "autonomous_self_preservation": False,
            "read_only": True,
        }
    ]
    return stored + baseline


def _institutional_dependency_concentration_analysis(
    *, records: list[dict[str, Any]], external_relations: dict[str, Any]
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "dependency_concentration_note")]
    providers = _external_sections(external_relations).get("external_provider_relationship_models") or []
    provider_count = len([p for p in providers if p.get("source") == "FIX_157_provider_catalog"])
    concentration = "elevated" if provider_count >= 3 else "moderate" if provider_count >= 2 else "low"
    return stored + [
        {
            "concentration_id": "provider-dependency-concentration",
            "provider_count": provider_count,
            "concentration_level": concentration,
            "detail": "Institutional dependency concentration requires human governance diversification review.",
            "autonomous_rebalancing": False,
            "read_only": True,
        }
    ]


def _governance_collapse_scenario_modeling(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "collapse_scenario")]
    scenarios = [
        {
            "scenario_id": sid,
            "severity": severity,
            "description": desc,
            "simulation_only": True,
            "autonomous_mitigation": False,
            "read_only": True,
        }
        for sid, severity, desc in GOVERNANCE_COLLAPSE_SCENARIOS
    ]
    return stored + scenarios


def _mission_identity_erosion_detection(
    *, records: list[dict[str, Any]], external_relations: dict[str, Any]
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "identity_erosion_signal")]
    influence = _external_sections(external_relations).get("external_influence_drift_detection") or []
    drift_signals = [i for i in influence if i.get("influence_id") != "no-influence-drift"]
    signals = list(stored)
    for drift in drift_signals:
        signals.append(
            {
                "erosion_id": f"identity-erosion-{drift.get('influence_id')}",
                "source": "external_influence_drift",
                "detail": f"Potential mission identity erosion signal: {drift.get('detail')}",
                "recommendation_only": True,
                "read_only": True,
            }
        )
    if not signals:
        signals.append(
            {
                "erosion_id": "no-identity-erosion",
                "detail": "No mission identity erosion detected against constitutional intent.",
                "read_only": True,
            }
        )
    return signals


def _sovereignty_degradation_analysis(*, records: list[dict[str, Any]], external_relations: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "sovereignty_degradation_note")]
    sovereignty_delegated = external_relations.get("sovereignty_delegation_enabled", False)
    boundaries = _external_sections(external_relations).get("provider_sovereignty_boundaries") or []
    preserved_count = sum(1 for b in boundaries if b.get("institutional_sovereignty_preserved"))
    degradation_level = "none" if not sovereignty_delegated and preserved_count >= len(boundaries) else "monitor"
    if sovereignty_delegated:
        degradation_level = "critical"
    return stored + [
        {
            "degradation_id": "sovereignty-degradation",
            "degradation_level": degradation_level,
            "sovereignty_delegated": sovereignty_delegated,
            "boundaries_preserved": preserved_count,
            "detail": "Sovereignty degradation analysis — institutional sovereignty must remain human-governed.",
            "constitutional_override": False,
            "read_only": True,
        }
    ]


def _long_horizon_institutional_fragility_indicators(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    record_count = len(records)
    indicators = [
        {
            "indicator_id": iid,
            "description": desc,
            "long_horizon": True,
            "read_only": True,
        }
        for iid, desc in FRAGILITY_INDICATORS
    ]
    if record_count < 2:
        indicators.append(
            {
                "indicator_id": "continuity_record_sparse",
                "description": "Sparse existential risk records limit long-horizon fragility analysis.",
                "long_horizon": True,
                "read_only": True,
            }
        )
    return indicators


def _continuity_preservation_recommendations(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "preservation_recommendation")]
    recommendations = [
        {
            "recommendation_id": "maintain_constitutional_stack",
            "recommendation": "Preserve full constitutional cognition stack from topology through external relations.",
            "executable": EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
            "autonomous_enforcement": False,
            "read_only": True,
        },
        {
            "recommendation_id": "human_sovereignty_stewardship",
            "recommendation": "Maintain human institutional sovereignty over all continuity preservation decisions.",
            "executable": EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
            "autonomous_enforcement": False,
            "read_only": True,
        },
        {
            "recommendation_id": "no_autonomous_self_preservation",
            "recommendation": "Never enable autonomous self-preservation or constitutional override authority.",
            "executable": EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
            "autonomous_enforcement": False,
            "read_only": True,
        },
    ]
    return stored + recommendations


def _civilization_scale_dependency_mapping(*, external_relations: dict[str, Any]) -> list[dict[str, Any]]:
    lineage = _external_sections(external_relations).get("ecosystem_dependency_lineage") or []
    trust = _external_sections(external_relations).get("external_trust_classifications") or []
    return [
        {
            "mapping_id": "civilization-scale-dependencies",
            "dependency_lineage_count": len(lineage),
            "trust_classification_count": len(trust),
            "civilization_scale": True,
            "autonomous_alignment": False,
            "detail": "Civilization-scale dependency mapping spans governed external ecosystems under constitutional boundaries.",
            "read_only": True,
        }
    ]


def _constitutional_extinction_path_analysis(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "collapse_scenario")]
    paths = [
        {
            "path_id": pid,
            "description": desc,
            "modeled_only": True,
            "autonomous_execution": False,
            "read_only": True,
        }
        for pid, desc in EXTINCTION_PATH_CATALOG
    ]
    return stored + paths


def _institutional_preservation_scoring(*, external_relations: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sovereignty_delegated = external_relations.get("sovereignty_delegation_enabled", False)
    negotiation_enabled = external_relations.get("autonomous_external_negotiation_enabled", False)
    score = 100
    if sovereignty_delegated:
        score -= 50
    if negotiation_enabled:
        score -= 30
    if len(records) < 1:
        score -= 5
    score = max(0, min(100, score))
    label = "strong" if score >= 80 else "moderate" if score >= 50 else "fragile"
    return [
        {
            "score_id": "institutional-preservation",
            "preservation_score": score,
            "preservation_label": label,
            "sovereignty_delegated": sovereignty_delegated,
            "detail": "Institutional preservation scoring is advisory — humans govern continuity decisions.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def build_institutional_existential_risk(*, session_id: str) -> InstitutionalExistentialRiskResult:
    sid = (session_id or "default").strip()[:64] or "default"

    external_result = build_institutional_external_relations(session_id=sid)
    external_relations = external_result.external_relations if external_result.ok else {}
    plan_id = str(external_relations.get("plan_id") or "") or None
    correlation_id = str(external_relations.get("correlation_id") or "") or None

    records = list_institutional_existential_risk_records(session_id=sid, plan_id=plan_id)

    sections = {
        "constitutional_continuity_risk_analysis": _constitutional_continuity_risk_analysis(
            records=records, external_relations=external_relations
        ),
        "institutional_dependency_concentration_analysis": _institutional_dependency_concentration_analysis(
            records=records, external_relations=external_relations
        ),
        "governance_collapse_scenario_modeling": _governance_collapse_scenario_modeling(records=records),
        "mission_identity_erosion_detection": _mission_identity_erosion_detection(
            records=records, external_relations=external_relations
        ),
        "sovereignty_degradation_analysis": _sovereignty_degradation_analysis(
            records=records, external_relations=external_relations
        ),
        "long_horizon_institutional_fragility_indicators": _long_horizon_institutional_fragility_indicators(
            records=records
        ),
        "continuity_preservation_recommendations": _continuity_preservation_recommendations(records=records),
        "civilization_scale_dependency_mapping": _civilization_scale_dependency_mapping(
            external_relations=external_relations
        ),
        "constitutional_extinction_path_analysis": _constitutional_extinction_path_analysis(records=records),
        "institutional_preservation_scoring": _institutional_preservation_scoring(
            external_relations=external_relations, records=records
        ),
    }

    existential_risk: dict[str, Any] = {
        "schema_version": INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION,
        "fix": INSTITUTIONAL_EXISTENTIAL_RISK_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_158,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_158,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
        "autonomous_self_preservation_enabled": AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158,
        "autonomous_continuity_enforcement_enabled": AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158,
        "constitutional_override_authority_enabled": CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158,
        "institutional_self_defense_authority_enabled": INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158,
        "invariant": INSTITUTIONAL_EXISTENTIAL_RISK_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "existential_risk_record_count": len(records),
        "all_recommendations_executable": False,
        "institutional_existential_continuity_cognition": True,
        "existential_risk_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in EXISTENTIAL_RISK_PRINCIPLES
        ],
        "sources": {
            "institutional_external_relations": external_result.ok,
            "existential_risk_records": len(records),
        },
    }
    return InstitutionalExistentialRiskResult(
        ok=True,
        session_id=sid,
        existential_risk=existential_risk,
        detail="Institutional existential risk assembled (recommendation-only — no autonomous self-preservation or constitutional override).",
    )
