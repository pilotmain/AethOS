# SPDX-License-Identifier: Apache-2.0
"""FIX 162 — constitutional pluralism cognition from legitimacy + perspective models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
    build_constitutional_legitimacy,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
    AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162,
    AUTONOMOUS_CONSTITUTIONAL_ARBITRATION_ENABLED_FIX_162,
    CONSTITUTIONAL_PLURALISM_FIX,
    CONSTITUTIONAL_PLURALISM_INVARIANT,
    CONSTITUTIONAL_PLURALISM_SCHEMA_VERSION,
    ENFORCED_IDEOLOGICAL_ALIGNMENT_ENABLED_FIX_162,
    GOVERNANCE_MUTATION_PERFORMED_FIX_162,
    GOVERNANCE_PERSPECTIVE_CATALOG,
    INSTITUTIONAL_PHILOSOPHY_CATALOG,
    MUTATION_PERFORMED_FIX_162,
    PLURALISM_PRINCIPLES,
    PLURALISM_RECOMMENDATION_EXECUTABLE,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_162,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
    list_constitutional_pluralism_records,
)


@dataclass(frozen=True)
class ConstitutionalPluralismResult:
    ok: bool
    session_id: str
    constitutional_pluralism: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _legitimacy_sections(constitutional_legitimacy: dict[str, Any]) -> dict[str, Any]:
    return constitutional_legitimacy.get("sections") or {}


def _governance_perspective_mapping(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "perspective_mapping_note")]
    catalog = [
        {
            "perspective_id": pid,
            "orientation": orientation,
            "description": desc,
            "authoritative_selection": False,
            "source": "FIX_162_perspective_catalog",
            "read_only": True,
        }
        for pid, orientation, desc in GOVERNANCE_PERSPECTIVE_CATALOG
    ]
    return stored + catalog


def _constitutional_worldview_coexistence_analysis(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "worldview_coexistence_note")]
    perspective_count = len(GOVERNANCE_PERSPECTIVE_CATALOG)
    return stored + [
        {
            "coexistence_id": "constitutional-worldview-coexistence",
            "perspective_count": perspective_count,
            "coexistence_label": "pluralistic" if perspective_count >= 3 else "developing",
            "autonomous_arbitration": False,
            "detail": "Multiple constitutional worldviews coexist under bounded human governance.",
            "read_only": True,
        }
    ]


def _institutional_philosophy_comparison(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "philosophy_comparison_note")]
    philosophies = [
        {
            "philosophy_id": pid,
            "statement": stmt,
            "ideological_alignment_enforced": False,
            "source": "FIX_162_philosophy_catalog",
            "read_only": True,
        }
        for pid, stmt in INSTITUTIONAL_PHILOSOPHY_CATALOG
    ]
    return stored + philosophies


def _stakeholder_perspective_continuity(*, records: list[dict[str, Any]], constitutional_legitimacy: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "stakeholder_perspective_note")]
    confidence = _legitimacy_sections(constitutional_legitimacy).get("stakeholder_confidence_reasoning") or []
    return stored + [
        {
            "continuity_id": "stakeholder-perspective-continuity",
            "confidence_dimension_count": len(confidence),
            "stakeholder_note_count": len(stored),
            "detail": "Stakeholder perspective continuity spans multiple governance viewpoints over time.",
            "read_only": True,
        }
    ]


def _constitutional_pluralism_tracking(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "pluralism_tracking_record")]
    kind_diversity = len({str(r.get("kind") or "") for r in records})
    return stored + [
        {
            "tracking_id": "constitutional-pluralism",
            "pluralism_record_count": len(records),
            "record_kind_diversity": kind_diversity,
            "worldview_collapsed": False,
            "detail": "Constitutional pluralism tracking preserves multiple perspectives without collapse.",
            "read_only": True,
        }
    ]


def _competing_legitimacy_interpretation_analysis(*, constitutional_legitimacy: dict[str, Any]) -> list[dict[str, Any]]:
    indicators = _legitimacy_sections(constitutional_legitimacy).get("governance_legitimacy_indicators") or []
    strong_count = sum(1 for i in indicators if i.get("strength") == "strong")
    return [
        {
            "interpretation_id": "competing-legitimacy-interpretations",
            "indicator_count": len(indicators),
            "strong_indicator_count": strong_count,
            "authoritative_ruling": False,
            "detail": "Competing legitimacy interpretations are surfaced; humans govern constitutional resolution.",
            "read_only": True,
        }
    ]


def _governance_culture_drift_detection(*, records: list[dict[str, Any]], constitutional_legitimacy: dict[str, Any]) -> list[dict[str, Any]]:
    drift = _legitimacy_sections(constitutional_legitimacy).get("constitutional_credibility_drift_detection") or []
    disagreement_count = len(_by_kind(records, "disagreement_mapping_note"))
    signals = [
        {
            "drift_id": "governance-culture-drift",
            "credibility_drift_signals": len(drift),
            "disagreement_note_count": disagreement_count,
            "ideological_alignment_enforced": False,
            "detail": "Governance culture drift detected — perspective diversity preserved, not auto-aligned.",
            "read_only": True,
        }
    ]
    for d in drift:
        if d.get("drift_id") != "no-credibility-drift":
            signals.append(
                {
                    "drift_id": f"culture-drift-{d.get('drift_id')}",
                    "source": "legitimacy_credibility_drift",
                    "detail": f"Culture drift signal from legitimacy layer: {d.get('detail')}",
                    "read_only": True,
                }
            )
    return signals


def _institutional_perspective_lineage(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "lineage_id": "institutional-perspective-lineage",
            "perspective_note_count": len(_by_kind(records, "perspective_mapping_note")),
            "philosophy_note_count": len(_by_kind(records, "philosophy_comparison_note")),
            "lineage_depth": len(GOVERNANCE_PERSPECTIVE_CATALOG) + len(INSTITUTIONAL_PHILOSOPHY_CATALOG),
            "detail": "Institutional perspective lineage spans governance cultures and constitutional philosophies.",
            "read_only": True,
        }
    ]


def _constitutional_disagreement_mapping(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "disagreement_mapping_note")]
    if not stored:
        return [
            {
                "disagreement_id": "baseline-constitutional-disagreement",
                "detail": "Constitutional disagreement may arise across perspectives — map via human governance deliberation.",
                "autonomous_arbitration": False,
                "read_only": True,
            }
        ]
    return stored


def _pluralistic_coherence_scoring(*, records: list[dict[str, Any]], constitutional_legitimacy: dict[str, Any]) -> list[dict[str, Any]]:
    confidence = _legitimacy_sections(constitutional_legitimacy).get("institutional_confidence_scoring") or []
    base = confidence[0].get("confidence_score", 80) if confidence else 80
    diversity = min(len({str(r.get("kind") or "") for r in records}) * 3, 12)
    score = max(0, min(100, base - 2 + diversity))
    label = "coherent_pluralism" if score >= 75 else "review_required" if score >= 50 else "fragmented"
    return [
        {
            "score_id": "pluralistic-coherence",
            "coherence_score": score,
            "coherence_label": label,
            "worldview_selection_authority": False,
            "detail": "Pluralistic coherence scoring is advisory — no authoritative worldview selection.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def build_constitutional_pluralism(*, session_id: str) -> ConstitutionalPluralismResult:
    sid = (session_id or "default").strip()[:64] or "default"

    legitimacy_result = build_constitutional_legitimacy(session_id=sid)
    constitutional_legitimacy = legitimacy_result.constitutional_legitimacy if legitimacy_result.ok else {}
    plan_id = str(constitutional_legitimacy.get("plan_id") or "") or None
    correlation_id = str(constitutional_legitimacy.get("correlation_id") or "") or None

    records = list_constitutional_pluralism_records(session_id=sid, plan_id=plan_id)

    sections = {
        "governance_perspective_mapping": _governance_perspective_mapping(records=records),
        "constitutional_worldview_coexistence_analysis": _constitutional_worldview_coexistence_analysis(records=records),
        "institutional_philosophy_comparison": _institutional_philosophy_comparison(records=records),
        "stakeholder_perspective_continuity": _stakeholder_perspective_continuity(
            records=records, constitutional_legitimacy=constitutional_legitimacy
        ),
        "constitutional_pluralism_tracking": _constitutional_pluralism_tracking(records=records),
        "competing_legitimacy_interpretation_analysis": _competing_legitimacy_interpretation_analysis(
            constitutional_legitimacy=constitutional_legitimacy
        ),
        "governance_culture_drift_detection": _governance_culture_drift_detection(
            records=records, constitutional_legitimacy=constitutional_legitimacy
        ),
        "institutional_perspective_lineage": _institutional_perspective_lineage(records=records),
        "constitutional_disagreement_mapping": _constitutional_disagreement_mapping(records=records),
        "pluralistic_coherence_scoring": _pluralistic_coherence_scoring(
            records=records, constitutional_legitimacy=constitutional_legitimacy
        ),
    }

    constitutional_pluralism: dict[str, Any] = {
        "schema_version": CONSTITUTIONAL_PLURALISM_SCHEMA_VERSION,
        "fix": CONSTITUTIONAL_PLURALISM_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_162,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_162,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
        "authoritative_worldview_selection_enabled": AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162,
        "autonomous_constitutional_arbitration_enabled": AUTONOMOUS_CONSTITUTIONAL_ARBITRATION_ENABLED_FIX_162,
        "enforced_ideological_alignment_enabled": ENFORCED_IDEOLOGICAL_ALIGNMENT_ENABLED_FIX_162,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_162,
        "invariant": CONSTITUTIONAL_PLURALISM_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "pluralism_record_count": len(records),
        "all_recommendations_executable": False,
        "constitutional_pluralism_cognition": True,
        "pluralism_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in PLURALISM_PRINCIPLES
        ],
        "sources": {
            "constitutional_legitimacy": legitimacy_result.ok,
            "pluralism_records": len(records),
        },
    }
    return ConstitutionalPluralismResult(
        ok=True,
        session_id=sid,
        constitutional_pluralism=constitutional_pluralism,
        detail="Constitutional pluralism assembled (recommendation-only — no authoritative worldview selection or autonomous arbitration).",
    )
