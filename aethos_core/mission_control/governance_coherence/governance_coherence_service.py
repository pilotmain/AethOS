# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — institutional constitutional coherence from topology, doctrine, and interpretation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_coherence.governance_coherence_contract import (
    AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
    AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153,
    COHERENCE_INTELLIGENCE_PRINCIPLES,
    COHERENCE_RECOMMENDATION_EXECUTABLE,
    CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153,
    GOVERNANCE_COHERENCE_FIX,
    GOVERNANCE_COHERENCE_INVARIANT,
    GOVERNANCE_COHERENCE_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_153,
    MUTATION_PERFORMED_FIX_153,
    SELF_HEALING_GOVERNANCE_ENABLED_FIX_153,
)
from aethos_core.mission_control.governance_coherence.governance_coherence_store import (
    list_governance_coherence_records,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import list_governance_doctrine_records
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
    build_governance_policy_interpretation,
)


@dataclass(frozen=True)
class GovernanceCoherenceResult:
    ok: bool
    session_id: str
    coherence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _interp_sections(interpretation: dict[str, Any]) -> dict[str, Any]:
    return interpretation.get("sections") or {}


def _doctrine_topology_consistency_analysis(*, interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    checks = _interp_sections(interpretation).get("constitutional_consistency_checks") or []
    linkage = _interp_sections(interpretation).get("doctrine_to_review_linkage") or []
    items: list[dict[str, Any]] = []
    for check in checks:
        items.append(
            {
                "analysis_id": f"topology-doctrine-{check.get('check_id', 'check')}",
                "status": check.get("status"),
                "detail": check.get("detail"),
                "scope": "doctrine_topology_consistency",
                "recommendation_only": True,
                "executable": COHERENCE_RECOMMENDATION_EXECUTABLE,
                "read_only": True,
            }
        )
    for link in linkage:
        items.append(
            {
                "analysis_id": "doctrine-readiness-topology-link",
                "status": "pass" if link.get("review_available") else "warn",
                "detail": (
                    f"Doctrine version `{link.get('doctrine_version')}` linked to readiness "
                    f"`{link.get('readiness_recommendation')}` — advisory coherence signal."
                ),
                "scope": "doctrine_topology_consistency",
                "recommendation_only": True,
                "read_only": True,
            }
        )
    if not items:
        items.append(
            {
                "analysis_id": "topology-doctrine-stable",
                "status": "pass",
                "detail": "No doctrine/topology consistency issues detected.",
                "read_only": True,
            }
        )
    return items


def _precedent_drift_detection(*, session_id: str, interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(list_governance_coherence_records(session_id=session_id), "drift_signal")]
    session_precedents = [
        r for r in list_governance_doctrine_records(session_id=session_id) if r.get("kind") == "governance_precedent"
    ]
    all_precedents = [
        r for r in list_governance_doctrine_records(session_id=None) if r.get("kind") == "governance_precedent"
    ]
    drift_signals: list[dict[str, Any]] = list(stored)
    if len(all_precedents) > len(session_precedents) and session_precedents:
        drift_signals.append(
            {
                "drift_id": "cross-session-precedent-divergence",
                "signal": "precedent_corpus_differs_across_sessions",
                "session_precedent_count": len(session_precedents),
                "global_precedent_count": len(all_precedents),
                "detail": "Session precedents differ from cross-session corpus — review for institutional drift.",
                "recommendation_only": True,
                "read_only": True,
            }
        )
    scores = _interp_sections(interpretation).get("precedent_confidence_scoring") or []
    low_confidence = [s for s in scores if float(s.get("confidence_score") or 0) < 0.6 and s.get("precedent_id") != "none"]
    for score in low_confidence:
        drift_signals.append(
            {
                "drift_id": f"low-confidence-{score.get('precedent_id')}",
                "signal": "low_precedent_confidence",
                "confidence_score": score.get("confidence_score"),
                "detail": "Low advisory confidence may indicate precedent drift or insufficient institutional weight.",
                "read_only": True,
            }
        )
    if not drift_signals:
        drift_signals.append(
            {
                "drift_id": "no-drift-detected",
                "signal": "stable",
                "detail": "No precedent drift signals detected.",
                "read_only": True,
            }
        )
    return drift_signals


def _governance_contradiction_surfacing(
    *, records: list[dict[str, Any]], interpretation: dict[str, Any]
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "contradiction_report")]
    conflicts = _interp_sections(interpretation).get("conflict_interpretation_guidance") or []
    competing = _interp_sections(interpretation).get("competing_interpretation_comparison") or []
    contradictions: list[dict[str, Any]] = list(stored)
    for conflict in conflicts:
        if conflict.get("severity") not in ("none", None):
            contradictions.append(
                {
                    "contradiction_id": conflict.get("guidance_id"),
                    "contradiction": conflict.get("conflict") or "doctrine_conflict",
                    "detail": conflict.get("guidance"),
                    "severity": conflict.get("severity"),
                    "recommendation_only": True,
                    "read_only": True,
                }
            )
    for comp in competing:
        if comp.get("interpretation_count", 0) >= 2:
            contradictions.append(
                {
                    "contradiction_id": comp.get("comparison_id"),
                    "contradiction": "competing_interpretations",
                    "detail": comp.get("detail"),
                    "interpretation_count": comp.get("interpretation_count"),
                    "read_only": True,
                }
            )
    if not contradictions:
        contradictions.append(
            {
                "contradiction_id": "none",
                "contradiction": "no_contradictions_surfaced",
                "detail": "No governance contradictions detected.",
                "read_only": True,
            }
        )
    return contradictions


def _institutional_integrity_scoring(*, interpretation: dict[str, Any]) -> dict[str, Any]:
    checks = _interp_sections(interpretation).get("constitutional_consistency_checks") or []
    pass_count = sum(1 for c in checks if c.get("status") == "pass")
    fail_count = sum(1 for c in checks if c.get("status") == "fail")
    warn_count = sum(1 for c in checks if c.get("status") == "warn")
    total = max(len(checks), 1)
    base = pass_count / total
    score = round(max(0.0, min(0.95, base - (fail_count * 0.15) - (warn_count * 0.05))), 2)
    label = "strong" if score >= 0.8 else "moderate" if score >= 0.6 else "at_risk"
    return {
        "integrity_score": score,
        "integrity_label": label,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "scoring_note": "Advisory institutional integrity score — not enforcement authority.",
        "recommendation_only": True,
        "executable": COHERENCE_RECOMMENDATION_EXECUTABLE,
        "read_only": True,
    }


def _policy_fragmentation_analysis(*, interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    ambiguities = _interp_sections(interpretation).get("governance_ambiguity_surfacing") or []
    amendments = (interpretation.get("sources") or {}).get("governance_doctrine")
    fragmentation: list[dict[str, Any]] = []
    ambiguity_count = len([a for a in ambiguities if a.get("ambiguous_terms")])
    if ambiguity_count:
        fragmentation.append(
            {
                "fragmentation_id": "amendment-ambiguity-fragmentation",
                "fragmentation_level": "moderate" if ambiguity_count < 3 else "high",
                "ambiguous_amendment_count": ambiguity_count,
                "detail": "Conditional language in amendments may fragment institutional policy coherence.",
                "read_only": True,
            }
        )
    lineage_count = len(_interp_sections(interpretation).get("governance_rationale_mapping") or [])
    if lineage_count > 8:
        fragmentation.append(
            {
                "fragmentation_id": "rationale-sprawl",
                "fragmentation_level": "moderate",
                "rationale_count": lineage_count,
                "detail": "High rationale cardinality may indicate policy fragmentation across governance layers.",
                "read_only": True,
            }
        )
    if not fragmentation:
        fragmentation.append(
            {
                "fragmentation_id": "coherent",
                "fragmentation_level": "low",
                "detail": "No significant policy fragmentation detected.",
                "doctrine_available": bool(amendments),
                "read_only": True,
            }
        )
    return fragmentation


def _governance_principle_alignment_checks(*, interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    principles = interpretation.get("interpretation_assistance_principles") or []
    doctrine_interp = _interp_sections(interpretation).get("doctrine_interpretation_records") or []
    checks: list[dict[str, Any]] = []
    for principle in principles:
        pid = principle.get("principle_id")
        aligned = True
        for record in doctrine_interp:
            text = str(record.get("content") or record.get("interpretation") or "").lower()
            if pid == "no_autonomous_policy_mutation" and any(t in text for t in ("auto enforce", "self-modify")):
                aligned = False
        checks.append(
            {
                "principle_id": pid,
                "aligned": aligned,
                "statement": principle.get("statement"),
                "status": "pass" if aligned else "fail",
                "recommendation_only": True,
                "read_only": True,
            }
        )
    return checks


def _cross_session_doctrine_coherence(*, session_id: str) -> list[dict[str, Any]]:
    session_records = list_governance_doctrine_records(session_id=session_id)
    all_records = list_governance_doctrine_records(session_id=None)
    sessions = {str(r.get("session_id") or "") for r in all_records if r.get("session_id")}
    session_kinds = {str(r.get("kind") or "") for r in session_records}
    global_kinds = {str(r.get("kind") or "") for r in all_records}
    missing_kinds = global_kinds - session_kinds
    return [
        {
            "coherence_id": "cross-session-doctrine",
            "session_id": session_id,
            "distinct_sessions_with_doctrine": len(sessions),
            "session_record_count": len(session_records),
            "global_record_count": len(all_records),
            "missing_kind_coverage": sorted(missing_kinds) if missing_kinds else [],
            "status": "warn" if missing_kinds else "pass",
            "detail": (
                "Session doctrine corpus differs from cross-session institutional corpus."
                if missing_kinds
                else "Session doctrine aligns with cross-session institutional coverage."
            ),
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _conflicting_precedent_clustering(*, session_id: str) -> list[dict[str, Any]]:
    precedents = [
        r for r in list_governance_doctrine_records(session_id=session_id) if r.get("kind") == "governance_precedent"
    ]
    if len(precedents) < 2:
        return [
            {
                "cluster_id": "insufficient-precedents",
                "cluster_count": 0,
                "detail": "Insufficient precedents for clustering analysis.",
                "read_only": True,
            }
        ]
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    keywords = ("hold", "approve", "quorum", "delegation", "review", "incident")
    for p in precedents:
        text = str(p.get("content") or "").lower()
        matched = next((kw for kw in keywords if kw in text), "general")
        buckets[matched].append(p)
    clusters = [
        {
            "cluster_id": f"cluster-{topic}",
            "topic": topic,
            "precedent_count": len(items),
            "precedent_ids": [i.get("record_id") for i in items],
            "potential_conflict": len(items) > 1 and topic != "general",
            "detail": (
                f"{len(items)} precedents share topic `{topic}` — review for conflicting readings."
                if len(items) > 1
                else f"Single precedent under topic `{topic}`."
            ),
            "read_only": True,
        }
        for topic, items in buckets.items()
    ]
    return clusters


def _trust_boundary_consistency_analysis(*, interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    stored_obs = _by_kind(list_governance_coherence_records(), "coherence_observation")
    consistency_checks = _interp_sections(interpretation).get("constitutional_consistency_checks") or []
    delegation_conflicts = [c for c in consistency_checks if "delegation" in str(c.get("check_id", "")).lower()]
    items: list[dict[str, Any]] = [{**r, "read_only": True} for r in stored_obs[:3]]
    for check in delegation_conflicts:
        items.append(
            {
                "analysis_id": check.get("check_id"),
                "boundary": "delegation",
                "status": check.get("status"),
                "detail": check.get("detail"),
                "recommendation_only": True,
                "read_only": True,
            }
        )
    if not items:
        items.append(
            {
                "analysis_id": "trust-boundary-stable",
                "boundary": "topology",
                "status": "pass",
                "detail": "Trust boundary consistency with doctrine and topology — no violations detected.",
                "read_only": True,
            }
        )
    return items


def _governance_stability_indicators(
    *, records: list[dict[str, Any]], interpretation: dict[str, Any], integrity: dict[str, Any]
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "stability_note")]
    contradictions = _governance_contradiction_surfacing(records=records, interpretation=interpretation)
    active_contradictions = [c for c in contradictions if c.get("contradiction") != "no_contradictions_surfaced"]
    integrity_score = float(integrity.get("integrity_score") or 0)
    stability_label = "stable" if integrity_score >= 0.8 and not active_contradictions else "monitoring"
    if integrity_score < 0.6 or len(active_contradictions) > 2:
        stability_label = "at_risk"
    indicators = list(stored)
    indicators.append(
        {
            "indicator_id": "composite-stability",
            "stability_label": stability_label,
            "integrity_score": integrity_score,
            "active_contradiction_count": len(active_contradictions),
            "self_healing_enabled": False,
            "detail": "Governance stability indicator — advisory only, no self-healing.",
            "recommendation_only": True,
            "read_only": True,
        }
    )
    return indicators


def build_governance_coherence(*, session_id: str) -> GovernanceCoherenceResult:
    sid = (session_id or "default").strip()[:64] or "default"

    interpretation_result = build_governance_policy_interpretation(session_id=sid)
    interpretation = interpretation_result.interpretation if interpretation_result.ok else {}
    plan_id = str(interpretation.get("plan_id") or "") or None
    correlation_id = str(interpretation.get("correlation_id") or "") or None

    records = list_governance_coherence_records(session_id=sid, plan_id=plan_id)
    integrity = _institutional_integrity_scoring(interpretation=interpretation)

    sections = {
        "doctrine_topology_consistency_analysis": _doctrine_topology_consistency_analysis(interpretation=interpretation),
        "precedent_drift_detection": _precedent_drift_detection(session_id=sid, interpretation=interpretation),
        "governance_contradiction_surfacing": _governance_contradiction_surfacing(
            records=records, interpretation=interpretation
        ),
        "institutional_integrity_scoring": integrity,
        "policy_fragmentation_analysis": _policy_fragmentation_analysis(interpretation=interpretation),
        "governance_principle_alignment_checks": _governance_principle_alignment_checks(interpretation=interpretation),
        "cross_session_doctrine_coherence": _cross_session_doctrine_coherence(session_id=sid),
        "conflicting_precedent_clustering": _conflicting_precedent_clustering(session_id=sid),
        "trust_boundary_consistency_analysis": _trust_boundary_consistency_analysis(interpretation=interpretation),
        "governance_stability_indicators": _governance_stability_indicators(
            records=records, interpretation=interpretation, integrity=integrity
        ),
    }

    coherence: dict[str, Any] = {
        "schema_version": GOVERNANCE_COHERENCE_SCHEMA_VERSION,
        "fix": GOVERNANCE_COHERENCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_153,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_153,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
        "automatic_doctrine_enforcement_enabled": AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153,
        "autonomous_governance_correction_enabled": AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153,
        "self_healing_governance_enabled": SELF_HEALING_GOVERNANCE_ENABLED_FIX_153,
        "constitutional_override_authority_enabled": CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153,
        "invariant": GOVERNANCE_COHERENCE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "coherence_record_count": len(records),
        "all_recommendations_executable": False,
        "institutional_constitutional_coherence_intelligence": True,
        "coherence_intelligence_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in COHERENCE_INTELLIGENCE_PRINCIPLES
        ],
        "sources": {
            "governance_policy_interpretation": interpretation_result.ok,
            "coherence_records": len(records),
        },
    }
    return GovernanceCoherenceResult(
        ok=True,
        session_id=sid,
        coherence=coherence,
        detail="Governance coherence assembled (recommendation-only — no autonomous correction or override).",
    )
