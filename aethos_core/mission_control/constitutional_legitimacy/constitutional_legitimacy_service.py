# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — constitutional legitimacy cognition from audit + institutional trust models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import build_constitutional_audit
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
    AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161,
    CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161,
    CONSTITUTIONAL_LEGITIMACY_FIX,
    CONSTITUTIONAL_LEGITIMACY_INVARIANT,
    CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION,
    GOVERNANCE_LEGITIMACY_INDICATORS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_161,
    LEGITIMACY_PRINCIPLES,
    LEGITIMACY_RECOMMENDATION_EXECUTABLE,
    MUTATION_PERFORMED_FIX_161,
    PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_161,
    STAKEHOLDER_CONFIDENCE_DIMENSIONS,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_store import (
    list_constitutional_legitimacy_records,
)


@dataclass(frozen=True)
class ConstitutionalLegitimacyResult:
    ok: bool
    session_id: str
    constitutional_legitimacy: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _audit_sections(constitutional_audit: dict[str, Any]) -> dict[str, Any]:
    return constitutional_audit.get("sections") or {}


def _institutional_trust_continuity_analysis(*, records: list[dict[str, Any]], constitutional_audit: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "trust_continuity_note")]
    integrity = _audit_sections(constitutional_audit).get("audit_trail_integrity_checks") or []
    label = integrity[0].get("integrity_label", "unknown") if integrity else "unknown"
    return stored + [
        {
            "continuity_id": "institutional-trust-continuity",
            "audit_integrity_label": label,
            "detail": "Institutional trust continuity spans bounded cognition and human governance stewardship.",
            "public_trust_manipulation": False,
            "read_only": True,
        }
    ]


def _governance_legitimacy_indicators(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "legitimacy_indicator")]
    indicators = [
        {
            "indicator_id": iid,
            "strength": strength,
            "description": desc,
            "autonomous_enforcement": False,
            "read_only": True,
        }
        for iid, strength, desc in GOVERNANCE_LEGITIMACY_INDICATORS
    ]
    return stored + indicators


def _stakeholder_confidence_reasoning(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "stakeholder_confidence_note")]
    dimensions = [
        {
            "dimension_id": did,
            "description": desc,
            "confidence_authored_autonomously": False,
            "read_only": True,
        }
        for did, desc in STAKEHOLDER_CONFIDENCE_DIMENSIONS
    ]
    return stored + dimensions


def _constitutional_credibility_drift_detection(*, records: list[dict[str, Any]], constitutional_audit: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "credibility_drift_signal")]
    transparency = _audit_sections(constitutional_audit).get("constitutional_transparency_scoring") or []
    label = transparency[0].get("transparency_label", "unknown") if transparency else "unknown"
    signals = list(stored)
    if label == "review_required":
        signals.append(
            {
                "drift_id": "transparency-credibility-drift",
                "source": "audit_transparency_scoring",
                "detail": "Constitutional transparency review may affect governance credibility — human stewardship required.",
                "auto_reconstructed": False,
                "read_only": True,
            }
        )
    if not signals:
        signals.append(
            {
                "drift_id": "no-credibility-drift",
                "detail": "No constitutional credibility drift detected against legitimacy baseline.",
                "read_only": True,
            }
        )
    return signals


def _governance_trust_fragmentation_analysis(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflict_kinds = len({str(r.get("kind") or "") for r in records})
    fragmentation = "low" if conflict_kinds <= 2 else "moderate" if conflict_kinds <= 4 else "elevated"
    return [
        {
            "fragmentation_id": "governance-trust-fragmentation",
            "fragmentation_level": fragmentation,
            "record_kind_diversity": conflict_kinds,
            "detail": "Trust fragmentation analysis is advisory — healing remains human institutional work.",
            "autonomous_healing": False,
            "read_only": True,
        }
    ]


def _institutional_confidence_scoring(*, records: list[dict[str, Any]], constitutional_audit: dict[str, Any]) -> list[dict[str, Any]]:
    transparency = _audit_sections(constitutional_audit).get("constitutional_transparency_scoring") or []
    base = transparency[0].get("transparency_score", 80) if transparency else 80
    density = min(len(records) * 2, 10)
    score = max(0, min(100, base - 3 + density))
    label = "high" if score >= 80 else "moderate" if score >= 50 else "fragile"
    return [
        {
            "score_id": "institutional-confidence",
            "confidence_score": score,
            "confidence_label": label,
            "trust_manipulation": False,
            "detail": "Institutional confidence scoring is advisory — humans govern legitimacy continuity.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _legitimacy_continuity_tracking(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "legitimacy_tracking_record")]
    return stored + [
        {
            "tracking_id": "legitimacy-continuity",
            "tracking_record_count": len(stored),
            "legitimacy_record_count": len(records),
            "detail": "Legitimacy continuity tracking spans operator and stakeholder trust over long horizons.",
            "read_only": True,
        }
    ]


def _constitutional_participation_health(*, constitutional_audit: dict[str, Any]) -> list[dict[str, Any]]:
    linkage = _audit_sections(constitutional_audit).get("doctrine_ethics_existential_linkage") or []
    layer_count = len([l for l in linkage if l.get("layer_id")])
    return [
        {
            "health_id": "constitutional-participation",
            "linked_layer_count": layer_count,
            "participation_label": "healthy" if layer_count >= 8 else "developing",
            "authority_expansion": False,
            "detail": "Constitutional participation health reflects bounded cognition layer engagement.",
            "read_only": True,
        }
    ]


def _governance_transparency_trust_analysis(*, constitutional_audit: dict[str, Any]) -> list[dict[str, Any]]:
    transparency = _audit_sections(constitutional_audit).get("constitutional_transparency_scoring") or []
    disclosure = _audit_sections(constitutional_audit).get("internal_vs_external_disclosure_boundaries") or []
    score = transparency[0].get("transparency_score", 0) if transparency else 0
    return [
        {
            "analysis_id": "governance-transparency-trust",
            "transparency_score": score,
            "disclosure_boundary_count": len(disclosure),
            "detail": "Governance transparency-trust linkage assists credibility without mandating disclosure.",
            "disclosure_mandate": False,
            "read_only": True,
        }
    ]


def _institutional_credibility_reconstruction(*, records: list[dict[str, Any]], constitutional_audit: dict[str, Any]) -> list[dict[str, Any]]:
    accountability = _audit_sections(constitutional_audit).get("accountability_records") or []
    audit_count = constitutional_audit.get("audit_record_count", 0)
    return [
        {
            "reconstruction_id": "institutional-credibility",
            "audit_record_count": audit_count,
            "accountability_signal_count": len(accountability),
            "legitimacy_record_count": len(records),
            "detail": "Credibility reconstruction assists human governance review — never autonomous trust manipulation.",
            "public_trust_manipulation": False,
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def build_constitutional_legitimacy(*, session_id: str) -> ConstitutionalLegitimacyResult:
    sid = (session_id or "default").strip()[:64] or "default"

    audit_result = build_constitutional_audit(session_id=sid)
    constitutional_audit = audit_result.constitutional_audit if audit_result.ok else {}
    plan_id = str(constitutional_audit.get("plan_id") or "") or None
    correlation_id = str(constitutional_audit.get("correlation_id") or "") or None

    records = list_constitutional_legitimacy_records(session_id=sid, plan_id=plan_id)

    sections = {
        "institutional_trust_continuity_analysis": _institutional_trust_continuity_analysis(
            records=records, constitutional_audit=constitutional_audit
        ),
        "governance_legitimacy_indicators": _governance_legitimacy_indicators(records=records),
        "stakeholder_confidence_reasoning": _stakeholder_confidence_reasoning(records=records),
        "constitutional_credibility_drift_detection": _constitutional_credibility_drift_detection(
            records=records, constitutional_audit=constitutional_audit
        ),
        "governance_trust_fragmentation_analysis": _governance_trust_fragmentation_analysis(records=records),
        "institutional_confidence_scoring": _institutional_confidence_scoring(
            records=records, constitutional_audit=constitutional_audit
        ),
        "legitimacy_continuity_tracking": _legitimacy_continuity_tracking(records=records),
        "constitutional_participation_health": _constitutional_participation_health(
            constitutional_audit=constitutional_audit
        ),
        "governance_transparency_trust_analysis": _governance_transparency_trust_analysis(
            constitutional_audit=constitutional_audit
        ),
        "institutional_credibility_reconstruction": _institutional_credibility_reconstruction(
            records=records, constitutional_audit=constitutional_audit
        ),
    }

    constitutional_legitimacy: dict[str, Any] = {
        "schema_version": CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION,
        "fix": CONSTITUTIONAL_LEGITIMACY_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_161,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_161,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
        "autonomous_legitimacy_enforcement_enabled": AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161,
        "public_trust_manipulation_enabled": PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161,
        "constitutional_authority_expansion_enabled": CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_161,
        "invariant": CONSTITUTIONAL_LEGITIMACY_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "legitimacy_record_count": len(records),
        "all_recommendations_executable": False,
        "constitutional_legitimacy_cognition": True,
        "legitimacy_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in LEGITIMACY_PRINCIPLES
        ],
        "sources": {
            "constitutional_audit": audit_result.ok,
            "legitimacy_records": len(records),
        },
    }
    return ConstitutionalLegitimacyResult(
        ok=True,
        session_id=sid,
        constitutional_legitimacy=constitutional_legitimacy,
        detail="Constitutional legitimacy assembled (recommendation-only — no autonomous legitimacy enforcement or public trust manipulation).",
    )
