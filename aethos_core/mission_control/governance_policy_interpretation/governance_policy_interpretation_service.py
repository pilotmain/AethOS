# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — institutional constitutional reasoning from doctrine + interpretation records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_contract import (
    AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
    AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152,
    GOVERNANCE_MUTATION_PERFORMED_FIX_152,
    GOVERNANCE_POLICY_INTERPRETATION_FIX,
    GOVERNANCE_POLICY_INTERPRETATION_INVARIANT,
    GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION,
    INTERPRETATION_ASSISTANCE_PRINCIPLES,
    INTERPRETATION_EXECUTABLE,
    MUTATION_PERFORMED_FIX_152,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    list_governance_policy_interpretation_records,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)


@dataclass(frozen=True)
class GovernancePolicyInterpretationResult:
    ok: bool
    session_id: str
    interpretation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _doctrine_sections(doctrine: dict[str, Any]) -> dict[str, Any]:
    return doctrine.get("sections") or {}


def _doctrine_interpretation_records(*, records: list[dict[str, Any]], doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "executable": INTERPRETATION_EXECUTABLE, "read_only": True} for r in _by_kind(records, "doctrine_interpretation")]
    if stored:
        return stored
    principles = _doctrine_sections(doctrine).get("governance_principle_registry") or []
    return [
        {
            "interpretation_id": "default-doctrine-interpretation",
            "principle_id": p.get("principle_id"),
            "interpretation": f"Advisory reading of principle: {p.get('statement')}",
            "source": "FIX_152_derived_from_doctrine",
            "executable": INTERPRETATION_EXECUTABLE,
            "read_only": True,
        }
        for p in principles[:5]
    ]


def _precedent_application_references(
    *, records: list[dict[str, Any]], doctrine: dict[str, Any]
) -> list[dict[str, Any]]:
    stored = [{**r, "executable": INTERPRETATION_EXECUTABLE, "read_only": True} for r in _by_kind(records, "precedent_application")]
    precedents = _doctrine_sections(doctrine).get("governance_precedent_tracking") or []
    derived = [
        {
            "application_id": f"app-{p.get('record_id', idx)}",
            "precedent_record_id": p.get("record_id"),
            "precedent_content": p.get("content"),
            "application_note": "Advisory precedent reference — not an automatic ruling.",
            "source": "FIX_152_derived_from_doctrine_precedent",
            "executable": INTERPRETATION_EXECUTABLE,
            "read_only": True,
        }
        for idx, p in enumerate(precedents)
    ]
    return stored + derived


def _conflict_interpretation_guidance(*, records: list[dict[str, Any]], doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "interpretation_guidance")]
    conflicts = _doctrine_sections(doctrine).get("doctrine_conflict_detection") or []
    derived = [
        {
            "guidance_id": f"guidance-{c.get('conflict_id', idx)}",
            "conflict": c.get("conflict"),
            "guidance": (
                "Surface conflict to governance deliberation; do not auto-resolve or enforce. "
                f"Detail: {c.get('detail', '')}"
            ),
            "severity": c.get("severity"),
            "source": "FIX_152_derived_from_doctrine_conflict",
            "executable": INTERPRETATION_EXECUTABLE,
            "read_only": True,
        }
        for idx, c in enumerate(conflicts)
        if c.get("severity") not in ("none", None)
    ]
    if not stored and not derived:
        return [
            {
                "guidance_id": "no-conflicts",
                "guidance": "No doctrine conflicts requiring interpretation guidance.",
                "read_only": True,
            }
        ]
    return stored + derived


def _governance_rationale_mapping(*, records: list[dict[str, Any]], doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "rationale_mapping")]
    rationales = _doctrine_sections(doctrine).get("policy_rationale_history") or []
    derived = [
        {
            "mapping_id": f"rationale-{idx + 1}",
            "rationale_kind": r.get("kind", "recorded"),
            "rationale": r.get("rationale") or r.get("content") or r.get("policy"),
            "interpretation_link": "Advisory mapping to governance deliberation context.",
            "source": "FIX_152_derived_from_doctrine_rationale",
            "read_only": True,
        }
        for idx, r in enumerate(rationales[:10])
    ]
    return stored + derived


def _doctrine_to_review_linkage(*, records: list[dict[str, Any]], session_id: str, doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "doctrine_review_linkage")]
    review_result = build_mission_readiness_review(session_id=session_id)
    review = review_result.review if review_result.ok else {}
    recommendation = review.get("overall_recommendation") or review.get("recommendation") or "unknown"
    derived = [
        {
            "linkage_id": "doctrine-readiness-link",
            "doctrine_version": (_doctrine_sections(doctrine).get("doctrine_versioning") or {}).get("current_version"),
            "readiness_recommendation": recommendation,
            "linkage_note": "Advisory doctrine-to-readiness linkage — not an execution gate.",
            "review_available": review_result.ok,
            "source": "FIX_152_doctrine_to_readiness_review",
            "executable": INTERPRETATION_EXECUTABLE,
            "read_only": True,
        }
    ]
    return stored + derived


def _precedent_confidence_scoring(*, doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    precedents = _doctrine_sections(doctrine).get("governance_precedent_tracking") or []
    scores: list[dict[str, Any]] = []
    for idx, p in enumerate(precedents):
        content = str(p.get("content") or "")
        score = 0.5
        if p.get("record_id"):
            score += 0.15
        if p.get("precedent_weight") == "institutional":
            score += 0.15
        if len(content) > 40:
            score += 0.1
        if p.get("author") and p.get("author") != "operator":
            score += 0.05
        scores.append(
            {
                "precedent_id": p.get("record_id") or f"precedent-{idx + 1}",
                "confidence_score": round(min(score, 0.95), 2),
                "confidence_label": "advisory",
                "scoring_note": "Advisory confidence only — not enforcement weight.",
                "read_only": True,
            }
        )
    if not scores:
        scores.append(
            {
                "precedent_id": "none",
                "confidence_score": 0.0,
                "confidence_label": "no_precedents",
                "scoring_note": "No precedents recorded for confidence scoring.",
                "read_only": True,
            }
        )
    return scores


def _competing_interpretation_comparison(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    competing = _by_kind(records, "competing_interpretation")
    if len(competing) < 2:
        items = [{**r, "read_only": True} for r in competing]
        if not items:
            items.append(
                {
                    "comparison_id": "none",
                    "detail": "No competing interpretations recorded — surface multiple views during deliberation.",
                    "read_only": True,
                }
            )
        return items
    return [
        {
            "comparison_id": "competing-interpretations",
            "interpretation_count": len(competing),
            "interpretations": [
                {"record_id": r.get("record_id"), "content": r.get("content"), "author": r.get("author")}
                for r in competing
            ],
            "resolution": "none_autonomous",
            "detail": "Competing views preserved — human governance must reconcile.",
            "read_only": True,
        }
    ]


def _governance_ambiguity_surfacing(*, records: list[dict[str, Any]], doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "ambiguity_surfacing")]
    ambiguities: list[dict[str, Any]] = list(stored)
    amendments = _doctrine_sections(doctrine).get("policy_amendment_proposals") or []
    ambiguous_terms = ("may", "should", "when appropriate", "as needed", "generally")
    for amendment in amendments:
        text = str(amendment.get("content") or "").lower()
        hits = [term for term in ambiguous_terms if term in text]
        if hits:
            ambiguities.append(
                {
                    "ambiguity_id": f"ambiguity-{amendment.get('record_id')}",
                    "source_record_id": amendment.get("record_id"),
                    "ambiguous_terms": hits,
                    "detail": "Amendment language contains advisory/conditional phrasing requiring human interpretation.",
                    "source": "FIX_152_derived_from_amendment_language",
                    "read_only": True,
                }
            )
    if not ambiguities:
        ambiguities.append(
            {
                "ambiguity_id": "none-detected",
                "detail": "No governance ambiguities surfaced from doctrine or records.",
                "read_only": True,
            }
        )
    return ambiguities


def _historical_interpretation_continuity(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    history = _by_kind(records, "historical_interpretation")
    doctrine_interp = _by_kind(records, "doctrine_interpretation")
    combined = sorted(history + doctrine_interp, key=lambda r: str(r.get("recorded_at") or ""))
    if not combined:
        return [
            {
                "continuity_id": "empty-history",
                "detail": "No historical interpretation records — continuity begins with operator-authored records.",
                "read_only": True,
            }
        ]
    return [
        {
            "continuity_id": "interpretation-timeline",
            "record_count": len(combined),
            "timeline": [
                {
                    "record_id": r.get("record_id"),
                    "kind": r.get("kind"),
                    "recorded_at": r.get("recorded_at"),
                    "author": r.get("author"),
                    "content_preview": str(r.get("content") or "")[:120],
                }
                for r in combined[-10:]
            ],
            "read_only": True,
        }
    ]


def _constitutional_consistency_checks(*, records: list[dict[str, Any]], doctrine: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    principles = _doctrine_sections(doctrine).get("governance_principle_registry") or []
    conflicts = _doctrine_sections(doctrine).get("doctrine_conflict_detection") or []
    high_conflicts = [c for c in conflicts if c.get("severity") in ("high", "critical")]

    checks.append(
        {
            "check_id": "principle-coverage",
            "status": "pass" if len(principles) >= 7 else "warn",
            "detail": f"{len(principles)} constitutional principles registered.",
            "read_only": True,
        }
    )
    checks.append(
        {
            "check_id": "doctrine-conflict-scan",
            "status": "fail" if high_conflicts else "pass",
            "detail": (
                f"{len(high_conflicts)} high-severity doctrine conflicts detected."
                if high_conflicts
                else "No high-severity doctrine conflicts against constitutional principles."
            ),
            "read_only": True,
        }
    )

    for record in _by_kind(records, "doctrine_interpretation"):
        text = str(record.get("content") or "").lower()
        if any(term in text for term in ("auto enforce", "autonomous ruling", "self-modify")):
            checks.append(
                {
                    "check_id": f"consistency-{record.get('record_id')}",
                    "status": "fail",
                    "detail": "Interpretation record language suggests autonomous enforcement — constitutionally incompatible.",
                    "record_id": record.get("record_id"),
                    "read_only": True,
                }
            )

    if len(checks) == 2:
        checks.append(
            {
                "check_id": "interpretation-records-clean",
                "status": "pass",
                "detail": "No constitutional inconsistencies detected in interpretation records.",
                "read_only": True,
            }
        )
    return checks


def build_governance_policy_interpretation(*, session_id: str) -> GovernancePolicyInterpretationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    doctrine_result = build_governance_doctrine(session_id=sid)
    doctrine = doctrine_result.doctrine if doctrine_result.ok else {}
    plan_id = str(doctrine.get("plan_id") or "") or None
    correlation_id = str(doctrine.get("correlation_id") or "") or None

    records = list_governance_policy_interpretation_records(session_id=sid, plan_id=plan_id)

    sections = {
        "doctrine_interpretation_records": _doctrine_interpretation_records(records=records, doctrine=doctrine),
        "precedent_application_references": _precedent_application_references(records=records, doctrine=doctrine),
        "conflict_interpretation_guidance": _conflict_interpretation_guidance(records=records, doctrine=doctrine),
        "governance_rationale_mapping": _governance_rationale_mapping(records=records, doctrine=doctrine),
        "doctrine_to_review_linkage": _doctrine_to_review_linkage(records=records, session_id=sid, doctrine=doctrine),
        "precedent_confidence_scoring": _precedent_confidence_scoring(doctrine=doctrine),
        "competing_interpretation_comparison": _competing_interpretation_comparison(records=records),
        "governance_ambiguity_surfacing": _governance_ambiguity_surfacing(records=records, doctrine=doctrine),
        "historical_interpretation_continuity": _historical_interpretation_continuity(records=records),
        "constitutional_consistency_checks": _constitutional_consistency_checks(records=records, doctrine=doctrine),
    }

    interpretation: dict[str, Any] = {
        "schema_version": GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION,
        "fix": GOVERNANCE_POLICY_INTERPRETATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_152,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_152,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
        "automatic_doctrine_enforcement_enabled": AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152,
        "autonomous_governance_rulings_enabled": AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152,
        "invariant": GOVERNANCE_POLICY_INTERPRETATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "interpretation_record_count": len(records),
        "all_interpretations_executable": False,
        "institutional_constitutional_reasoning": True,
        "interpretation_assistance_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in INTERPRETATION_ASSISTANCE_PRINCIPLES
        ],
        "sources": {
            "governance_doctrine": doctrine_result.ok,
            "interpretation_records": len(records),
        },
    }
    return GovernancePolicyInterpretationResult(
        ok=True,
        session_id=sid,
        interpretation=interpretation,
        detail="Governance policy interpretation assembled (assistance only — no autonomous enforcement or rulings).",
    )
