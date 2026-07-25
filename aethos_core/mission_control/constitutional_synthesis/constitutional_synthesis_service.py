# SPDX-License-Identifier: Apache-2.0
"""FIX 163 — constitutional synthesis + institutional wisdom across all constitutional dimensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import build_constitutional_audit
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
    build_constitutional_pluralism,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
    AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163,
    CONSTITUTIONAL_LAYER_STACK,
    CONSTITUTIONAL_SYNTHESIS_FIX,
    CONSTITUTIONAL_SYNTHESIS_INVARIANT,
    CONSTITUTIONAL_SYNTHESIS_SCHEMA_VERSION,
    CONSTITUTIONAL_TENSION_CATALOG,
    CONSTITUTIONAL_TRADEOFF_CATALOG,
    DOCTRINE_ENFORCEMENT_ENABLED_FIX_163,
    GOVERNANCE_MUTATION_PERFORMED_FIX_163,
    LEGITIMACY_ARBITRATION_ENABLED_FIX_163,
    MUTATION_PERFORMED_FIX_163,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_163,
    SYNTHESIS_PRINCIPLES,
    SYNTHESIS_RECOMMENDATION_EXECUTABLE,
    WORLDVIEW_SELECTION_ENABLED_FIX_163,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_store import (
    list_constitutional_synthesis_records,
)


@dataclass(frozen=True)
class ConstitutionalSynthesisResult:
    ok: bool
    session_id: str
    constitutional_synthesis: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _score_from(payload: dict[str, Any], section_key: str, score_key: str) -> int | None:
    items = _sections(payload).get(section_key) or []
    if not items:
        return None
    val = items[0].get(score_key)
    return int(val) if isinstance(val, int) else None


def _constitutional_tension_analysis(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "tension_analysis_note")]
    catalog = [
        {
            "tension_id": tid,
            "dimension_a": dim_a,
            "dimension_b": dim_b,
            "description": desc,
            "autonomous_resolution": False,
            "source": "FIX_163_tension_catalog",
            "read_only": True,
        }
        for tid, dim_a, dim_b, desc in CONSTITUTIONAL_TENSION_CATALOG
    ]
    return stored + catalog


def _constitutional_tradeoff_maps(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "tradeoff_map_note")]
    maps = [
        {
            "tradeoff_id": tid,
            "preserve_a": dim_a,
            "preserve_b": dim_b,
            "detail": f"Constitutional tradeoff: preserve {dim_a} vs preserve {dim_b} — human resolution required.",
            "autonomous_decision": False,
            "read_only": True,
        }
        for tid, dim_a, dim_b in CONSTITUTIONAL_TRADEOFF_CATALOG
    ]
    return stored + maps


def _cross_dimensional_synthesis(
    *,
    records: list[dict[str, Any]],
    pluralism: dict[str, Any],
    audit: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "cross_dimensional_synthesis_note")]
    linkage = _sections(audit).get("doctrine_ethics_existential_linkage") or []
    layer_count = len([l for l in linkage if l.get("layer_id")])
    pluralism_score = _score_from(pluralism, "pluralistic_coherence_scoring", "coherence_score")
    transparency = _score_from(audit, "constitutional_transparency_scoring", "transparency_score")
    synthesis = [
        {
            "synthesis_id": "cross-dimensional-constitutional",
            "linked_layer_count": layer_count,
            "pluralism_coherence_score": pluralism_score,
            "transparency_score": transparency,
            "dimensions_engaged": ["doctrine", "legitimacy", "ethics", "pluralism", "accountability"],
            "detail": "Cross-dimensional synthesis spans constitutional stack — recurring tension possible across layers.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]
    return stored + synthesis


def _institutional_wisdom_signals(*, records: list[dict[str, Any]], pluralism: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "wisdom_signal")]
    integrity = _sections(audit).get("audit_trail_integrity_checks") or []
    from_legitimacy_proxy = _sections(pluralism).get("competing_legitimacy_interpretation_analysis") or []
    signals = list(stored)
    if integrity:
        signals.append(
            {
                "wisdom_id": "audit-trail-wisdom",
                "source": "accountability",
                "detail": "Audit trail integrity supports institutional wisdom through replay-safe accountability.",
                "read_only": True,
            }
        )
    if from_legitimacy_proxy:
        signals.append(
            {
                "wisdom_id": "pluralistic-legitimacy-wisdom",
                "source": "pluralism",
                "detail": "Competing legitimacy interpretations require human constitutional stewardship.",
                "read_only": True,
            }
        )
    if not signals:
        signals.append(
            {
                "wisdom_id": "bounded-cognition-wisdom",
                "detail": "Institutional wisdom: cognition without authority across all constitutional dimensions.",
                "read_only": True,
            }
        )
    return signals


def _inter_dimensional_disagreement_analysis(*, pluralism: dict[str, Any]) -> list[dict[str, Any]]:
    disagreements = _sections(pluralism).get("constitutional_disagreement_mapping") or []
    drift = _sections(pluralism).get("governance_culture_drift_detection") or []
    return [
        {
            "disagreement_id": "inter-dimensional-disagreement",
            "pluralism_disagreement_count": len(disagreements),
            "culture_drift_signal_count": len(drift),
            "detail": "Inter-dimensional disagreement may span ethics, legitimacy, and pluralism — surfaced not arbitrated.",
            "read_only": True,
        }
    ]


def _recurring_constitutional_tension_tracking(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "recurring_pattern_note")]
    tension_notes = _by_kind(records, "tension_analysis_note")
    return stored + [
        {
            "tracking_id": "recurring-constitutional-tensions",
            "tension_note_count": len(tension_notes),
            "catalog_tension_count": len(CONSTITUTIONAL_TENSION_CATALOG),
            "detail": "Recurring constitutional tensions tracked across dimensions — patterns observed not enforced.",
            "read_only": True,
        }
    ]


def _recurring_institutional_strength_signals(*, audit: dict[str, Any]) -> list[dict[str, Any]]:
    linkage = _sections(audit).get("doctrine_ethics_existential_linkage") or []
    layer_count = len([l for l in linkage if l.get("layer_id")])
    return [
        {
            "strength_id": "constitutional-stack-completeness",
            "linked_layer_count": layer_count,
            "stack_depth": len(CONSTITUTIONAL_LAYER_STACK),
            "detail": "Institutional strength: full constitutional cognition stack from topology through synthesis.",
            "read_only": True,
        },
        {
            "strength_id": "cognition-without-authority",
            "detail": "Recurring strength: every layer reasons without granting autonomous constitutional authority.",
            "read_only": True,
        },
    ]


def _constitutional_layer_interaction_map() -> list[dict[str, Any]]:
    return [
        {
            "layer_id": lid,
            "fix": fix,
            "interacts_with": "full_constitutional_stack",
            "synthesis_visible": True,
            "read_only": True,
        }
        for lid, fix in CONSTITUTIONAL_LAYER_STACK
    ]


def _synthesis_coherence_scoring(*, records: list[dict[str, Any]], pluralism: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    pluralism_score = _score_from(pluralism, "pluralistic_coherence_scoring", "coherence_score") or 75
    transparency = _score_from(audit, "constitutional_transparency_scoring", "transparency_score") or 75
    density = min(len(records) * 2, 10)
    score = max(0, min(100, (pluralism_score + transparency) // 2 - 2 + density))
    label = "synthesized" if score >= 80 else "review_required" if score >= 50 else "fragmented"
    return [
        {
            "score_id": "synthesis-coherence",
            "coherence_score": score,
            "coherence_label": label,
            "constitutional_decision_authority": False,
            "detail": "Synthesis coherence scoring is advisory — no autonomous constitutional decisions.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _institutional_wisdom_continuity(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wisdom_count = len(_by_kind(records, "wisdom_signal"))
    return [
        {
            "continuity_id": "institutional-wisdom-continuity",
            "wisdom_signal_count": wisdom_count,
            "synthesis_record_count": len(records),
            "detail": "Institutional wisdom continuity spans cross-dimensional synthesis over long horizons.",
            "read_only": True,
        }
    ]


def build_constitutional_synthesis(*, session_id: str) -> ConstitutionalSynthesisResult:
    sid = (session_id or "default").strip()[:64] or "default"

    pluralism_result = build_constitutional_pluralism(session_id=sid)
    audit_result = build_constitutional_audit(session_id=sid)
    pluralism = pluralism_result.constitutional_pluralism if pluralism_result.ok else {}
    audit = audit_result.constitutional_audit if audit_result.ok else {}
    plan_id = str(pluralism.get("plan_id") or audit.get("plan_id") or "") or None
    correlation_id = str(pluralism.get("correlation_id") or audit.get("correlation_id") or "") or None

    records = list_constitutional_synthesis_records(session_id=sid, plan_id=plan_id)

    sections = {
        "constitutional_tension_analysis": _constitutional_tension_analysis(records=records),
        "constitutional_tradeoff_maps": _constitutional_tradeoff_maps(records=records),
        "cross_dimensional_synthesis": _cross_dimensional_synthesis(records=records, pluralism=pluralism, audit=audit),
        "institutional_wisdom_signals": _institutional_wisdom_signals(records=records, pluralism=pluralism, audit=audit),
        "inter_dimensional_disagreement_analysis": _inter_dimensional_disagreement_analysis(pluralism=pluralism),
        "recurring_constitutional_tension_tracking": _recurring_constitutional_tension_tracking(records=records),
        "recurring_institutional_strength_signals": _recurring_institutional_strength_signals(audit=audit),
        "constitutional_layer_interaction_map": _constitutional_layer_interaction_map(),
        "synthesis_coherence_scoring": _synthesis_coherence_scoring(records=records, pluralism=pluralism, audit=audit),
        "institutional_wisdom_continuity": _institutional_wisdom_continuity(records=records),
    }

    constitutional_synthesis: dict[str, Any] = {
        "schema_version": CONSTITUTIONAL_SYNTHESIS_SCHEMA_VERSION,
        "fix": CONSTITUTIONAL_SYNTHESIS_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_163,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_163,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
        "autonomous_constitutional_decisions_enabled": AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163,
        "doctrine_enforcement_enabled": DOCTRINE_ENFORCEMENT_ENABLED_FIX_163,
        "legitimacy_arbitration_enabled": LEGITIMACY_ARBITRATION_ENABLED_FIX_163,
        "worldview_selection_enabled": WORLDVIEW_SELECTION_ENABLED_FIX_163,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_163,
        "invariant": CONSTITUTIONAL_SYNTHESIS_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "synthesis_record_count": len(records),
        "all_recommendations_executable": False,
        "constitutional_synthesis_cognition": True,
        "institutional_wisdom_cognition": True,
        "synthesis_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in SYNTHESIS_PRINCIPLES
        ],
        "sources": {
            "constitutional_pluralism": pluralism_result.ok,
            "constitutional_audit": audit_result.ok,
            "constitutional_layer_count": len(CONSTITUTIONAL_LAYER_STACK),
            "synthesis_records": len(records),
        },
    }
    return ConstitutionalSynthesisResult(
        ok=True,
        session_id=sid,
        constitutional_synthesis=constitutional_synthesis,
        detail="Constitutional synthesis assembled (recommendation-only — no autonomous constitutional decisions or authority).",
    )
