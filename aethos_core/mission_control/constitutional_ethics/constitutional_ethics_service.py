# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — constitutional ethical cognition from existential risk + institutional values."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
    AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159,
    CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159,
    CONSTITUTIONAL_VALUE_CATALOG,
    CONSTITUTIONAL_ETHICS_FIX,
    CONSTITUTIONAL_ETHICS_INVARIANT,
    CONSTITUTIONAL_ETHICS_SCHEMA_VERSION,
    ETHICS_PRINCIPLES,
    ETHICS_RECOMMENDATION_EXECUTABLE,
    GOVERNANCE_MUTATION_PERFORMED_FIX_159,
    MORAL_PRECEDENT_CATALOG,
    MUTATION_PERFORMED_FIX_159,
    SELF_AUTHORED_ETHICS_ENABLED_FIX_159,
    VALUE_CONFLICT_PATTERNS,
    VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_store import (
    list_constitutional_ethics_records,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
    build_institutional_existential_risk,
)


@dataclass(frozen=True)
class ConstitutionalEthicsResult:
    ok: bool
    session_id: str
    constitutional_ethics: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _existential_sections(existential_risk: dict[str, Any]) -> dict[str, Any]:
    return existential_risk.get("sections") or {}


def _constitutional_ethics_records(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "ethics_record")]
    catalog = [
        {
            "value_id": vid,
            "statement": stmt,
            "self_authored": False,
            "source": "FIX_159_value_catalog",
            "read_only": True,
        }
        for vid, stmt in CONSTITUTIONAL_VALUE_CATALOG
    ]
    return stored + catalog


def _value_conflict_reasoning(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "value_conflict_note")]
    patterns = [
        {
            "conflict_id": cid,
            "severity": severity,
            "description": desc,
            "autonomous_resolution": False,
            "read_only": True,
        }
        for cid, severity, desc in VALUE_CONFLICT_PATTERNS
    ]
    return stored + patterns


def _institutional_moral_tradeoff_analysis(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "moral_tradeoff")]
    if not stored:
        return [
            {
                "tradeoff_id": "governance_safety_vs_mission_urgency",
                "dimension_a": "governance_safety",
                "dimension_b": "mission_urgency",
                "detail": "Moral tradeoff between governance safety and mission urgency — human resolution required.",
                "recommendation_only": True,
                "read_only": True,
            }
        ]
    return stored


def _mission_vs_risk_ethical_tension_analysis(*, records: list[dict[str, Any]], existential_risk: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "ethical_tension_observation")]
    preservation = _existential_sections(existential_risk).get("institutional_preservation_scoring") or []
    score = preservation[0].get("preservation_score", 100) if preservation else 100
    tension_level = "elevated" if score < 80 else "moderate" if score < 95 else "low"
    baseline = [
        {
            "tension_id": "mission-vs-existential-risk",
            "tension_level": tension_level,
            "preservation_score": score,
            "detail": "Mission-vs-risk ethical tension under constitutional intent — advisory only.",
            "value_enforcement": False,
            "read_only": True,
        }
    ]
    return stored + baseline


def _constitutional_ethics_continuity(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ethics_count = len(_by_kind(records, "ethics_record"))
    precedent_count = len(_by_kind(records, "moral_precedent"))
    return [
        {
            "continuity_id": "constitutional-ethics-continuity",
            "ethics_record_count": ethics_count,
            "moral_precedent_count": precedent_count,
            "catalog_value_count": len(CONSTITUTIONAL_VALUE_CATALOG),
            "detail": "Constitutional ethics continuity spans recorded values and institutional moral precedent.",
            "read_only": True,
        }
    ]


def _long_horizon_value_preservation(*, records: list[dict[str, Any]], existential_risk: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "value_preservation_note")]
    fragility = _existential_sections(existential_risk).get("long_horizon_institutional_fragility_indicators") or []
    return stored + [
        {
            "preservation_id": "long-horizon-value-preservation",
            "fragility_indicator_count": len(fragility),
            "value_preservation_note_count": len(stored),
            "detail": "Long-horizon value preservation requires human institutional stewardship.",
            "autonomous_enforcement": False,
            "read_only": True,
        }
    ]


def _ethical_ambiguity_surfacing(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflict_count = len(_by_kind(records, "value_conflict_note"))
    tradeoff_count = len(_by_kind(records, "moral_tradeoff"))
    ambiguities = [
        {
            "ambiguity_id": "unresolved-value-conflicts",
            "conflict_count": conflict_count,
            "tradeoff_count": tradeoff_count,
            "detail": "Ethical ambiguities are surfaced for human deliberation — never collapsed autonomously.",
            "read_only": True,
        }
    ]
    if conflict_count == 0 and tradeoff_count == 0:
        ambiguities.append(
            {
                "ambiguity_id": "baseline-ethical-ambiguity",
                "detail": "Constitutional value conflicts may arise under mission pressure — monitor via human governance.",
                "read_only": True,
            }
        )
    return ambiguities


def _institutional_moral_precedent_analysis(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "moral_precedent")]
    catalog = [
        {
            "precedent_id": pid,
            "precedent": stmt,
            "enforcement_authority": False,
            "source": "FIX_159_precedent_catalog",
            "read_only": True,
        }
        for pid, stmt in MORAL_PRECEDENT_CATALOG
    ]
    return stored + catalog


def _constitutional_value_drift_detection(*, existential_risk: dict[str, Any]) -> list[dict[str, Any]]:
    erosion = _existential_sections(existential_risk).get("mission_identity_erosion_detection") or []
    drift_signals = [
        {
            "drift_id": f"value-drift-{e.get('erosion_id', 'unknown')}",
            "source": "mission_identity_erosion",
            "detail": f"Potential constitutional value drift: {e.get('detail')}",
            "auto_corrected": False,
            "read_only": True,
        }
        for e in erosion
        if e.get("erosion_id") != "no-identity-erosion"
    ]
    if not drift_signals:
        drift_signals.append(
            {
                "drift_id": "no-value-drift",
                "detail": "No constitutional value drift detected against institutional ethical baseline.",
                "read_only": True,
            }
        )
    return drift_signals


def _ethical_coherence_scoring(*, records: list[dict[str, Any]], existential_risk: dict[str, Any]) -> list[dict[str, Any]]:
    preservation = _existential_sections(existential_risk).get("institutional_preservation_scoring") or []
    base_score = preservation[0].get("preservation_score", 100) if preservation else 100
    ethics_density = min(len(records) * 2, 10)
    score = max(0, min(100, base_score - 5 + ethics_density))
    label = "coherent" if score >= 80 else "review_required" if score >= 50 else "fragmented"
    return [
        {
            "score_id": "ethical-coherence",
            "coherence_score": score,
            "coherence_label": label,
            "value_enforcement_authority": False,
            "detail": "Ethical coherence scoring is advisory — humans govern moral resolution.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def build_constitutional_ethics(*, session_id: str) -> ConstitutionalEthicsResult:
    sid = (session_id or "default").strip()[:64] or "default"

    existential_result = build_institutional_existential_risk(session_id=sid)
    existential_risk = existential_result.existential_risk if existential_result.ok else {}
    plan_id = str(existential_risk.get("plan_id") or "") or None
    correlation_id = str(existential_risk.get("correlation_id") or "") or None

    records = list_constitutional_ethics_records(session_id=sid, plan_id=plan_id)

    sections = {
        "constitutional_ethics_records": _constitutional_ethics_records(records=records),
        "value_conflict_reasoning": _value_conflict_reasoning(records=records),
        "institutional_moral_tradeoff_analysis": _institutional_moral_tradeoff_analysis(records=records),
        "mission_vs_risk_ethical_tension_analysis": _mission_vs_risk_ethical_tension_analysis(
            records=records, existential_risk=existential_risk
        ),
        "constitutional_ethics_continuity": _constitutional_ethics_continuity(records=records),
        "long_horizon_value_preservation": _long_horizon_value_preservation(
            records=records, existential_risk=existential_risk
        ),
        "ethical_ambiguity_surfacing": _ethical_ambiguity_surfacing(records=records),
        "institutional_moral_precedent_analysis": _institutional_moral_precedent_analysis(records=records),
        "constitutional_value_drift_detection": _constitutional_value_drift_detection(existential_risk=existential_risk),
        "ethical_coherence_scoring": _ethical_coherence_scoring(records=records, existential_risk=existential_risk),
    }

    constitutional_ethics: dict[str, Any] = {
        "schema_version": CONSTITUTIONAL_ETHICS_SCHEMA_VERSION,
        "fix": CONSTITUTIONAL_ETHICS_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_159,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_159,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
        "autonomous_moral_authority_enabled": AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159,
        "self_authored_ethics_enabled": SELF_AUTHORED_ETHICS_ENABLED_FIX_159,
        "constitutional_override_authority_enabled": CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159,
        "value_enforcement_authority_enabled": VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159,
        "invariant": CONSTITUTIONAL_ETHICS_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "ethics_record_count": len(records),
        "all_recommendations_executable": False,
        "constitutional_ethical_cognition": True,
        "ethics_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in ETHICS_PRINCIPLES
        ],
        "sources": {
            "institutional_existential_risk": existential_result.ok,
            "ethics_records": len(records),
        },
    }
    return ConstitutionalEthicsResult(
        ok=True,
        session_id=sid,
        constitutional_ethics=constitutional_ethics,
        detail="Constitutional ethics assembled (recommendation-only — no autonomous moral authority or value enforcement).",
    )
