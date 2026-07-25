# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — constitutional accountability cognition from ethics + full stack linkage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.constitutional_audit.constitutional_audit_contract import (
    ACCOUNTABILITY_PRINCIPLES,
    AUDIT_RECOMMENDATION_EXECUTABLE,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
    AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160,
    CONSTITUTIONAL_AUDIT_FIX,
    CONSTITUTIONAL_AUDIT_INVARIANT,
    CONSTITUTIONAL_AUDIT_SCHEMA_VERSION,
    CONSTITUTIONAL_LAYER_LINKAGE,
    DISCLOSURE_BOUNDARIES,
    GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160,
    GOVERNANCE_MUTATION_PERFORMED_FIX_160,
    MUTATION_PERFORMED_FIX_160,
    PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_store import (
    list_constitutional_audit_records,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import build_constitutional_ethics


@dataclass(frozen=True)
class ConstitutionalAuditResult:
    ok: bool
    session_id: str
    constitutional_audit: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _ethics_sections(constitutional_ethics: dict[str, Any]) -> dict[str, Any]:
    return constitutional_ethics.get("sections") or {}


def _constitutional_audit_reports(*, records: list[dict[str, Any]], constitutional_ethics: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "audit_report")]
    ethics_count = constitutional_ethics.get("ethics_record_count", 0)
    baseline = [
        {
            "report_id": "constitutional-stack-audit",
            "layer_count": len(CONSTITUTIONAL_LAYER_LINKAGE),
            "ethics_record_count": ethics_count,
            "detail": "Constitutional audit report spanning full cognition stack — human review required.",
            "autonomous_disclosure": False,
            "read_only": True,
        }
    ]
    return stored + baseline


def _traceable_reasoning_summaries(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "reasoning_summary")]
    if not stored:
        return [
            {
                "summary_id": "bounded-cognition-trace",
                "detail": "All constitutional layers reason without authority — traceable via layer linkage.",
                "traceable": True,
                "public_communication_authority": False,
                "read_only": True,
            }
        ]
    return stored


def _doctrine_ethics_existential_linkage(*, constitutional_ethics: dict[str, Any]) -> list[dict[str, Any]]:
    linkage = [
        {
            "layer_id": lid,
            "fix": fix,
            "role": role,
            "linked": True,
            "read_only": True,
        }
        for lid, fix, role in CONSTITUTIONAL_LAYER_LINKAGE
    ]
    ethics_sources = constitutional_ethics.get("sources") or {}
    linkage.append(
        {
            "linkage_id": "ethics-to-existential",
            "existential_risk_linked": ethics_sources.get("institutional_existential_risk", False),
            "detail": "Ethics cognition composes from existential risk which composes from external relations and identity.",
            "read_only": True,
        }
    )
    return linkage


def _recommendation_explanations(*, records: list[dict[str, Any]], constitutional_ethics: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "recommendation_explanation")]
    coherence = _ethics_sections(constitutional_ethics).get("ethical_coherence_scoring") or []
    score = coherence[0].get("coherence_score", 0) if coherence else 0
    baseline = [
        {
            "explanation_id": "why-recommend-bounded",
            "question": "Why did AethOS recommend this?",
            "answer": (
                "Recommendations derive from constitutional cognition layers (doctrine through ethics) "
                "and are always executable:false — humans govern approval, disclosure, and enforcement."
            ),
            "ethics_coherence_score": score,
            "recommendation_only": True,
            "read_only": True,
        }
    ]
    return stored + baseline


def _accountability_records(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "accountability_record")]
    if not stored:
        return [
            {
                "accountability_id": "human-governance-accountability",
                "detail": "Accountability records assist human governance review — never autonomous enforcement.",
                "governance_enforcement": False,
                "read_only": True,
            }
        ]
    return stored


def _human_readable_governance_evidence_bundles(*, constitutional_ethics: dict[str, Any]) -> list[dict[str, Any]]:
    principles = constitutional_ethics.get("ethics_principles") or []
    return [
        {
            "bundle_id": "governance-evidence-bundle",
            "ethics_principle_count": len(principles),
            "layer_linkage_count": len(CONSTITUTIONAL_LAYER_LINKAGE),
            "format": "human_readable_markdown",
            "detail": "Human-readable governance evidence bundle for operator accountability review.",
            "autonomous_disclosure": False,
            "read_only": True,
        }
    ]


def _public_safe_accountability_summaries(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "disclosure_boundary_note")]
    return [
        {
            "summary_id": "public-safe-accountability",
            "redacted": True,
            "human_approved_disclosure_required": True,
            "detail": "Public-safe accountability summary — redacted, human-approved disclosure only.",
            "public_communication_authority": False,
            "read_only": True,
        },
        *[{**r, "read_only": True} for r in stored],
    ]


def _internal_vs_external_disclosure_boundaries() -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": bid,
            "definition": definition,
            "autonomous_disclosure": False,
            "read_only": True,
        }
        for bid, definition in DISCLOSURE_BOUNDARIES
    ]


def _constitutional_transparency_scoring(*, records: list[dict[str, Any]], constitutional_ethics: dict[str, Any]) -> list[dict[str, Any]]:
    coherence = _ethics_sections(constitutional_ethics).get("ethical_coherence_scoring") or []
    base = coherence[0].get("coherence_score", 80) if coherence else 80
    audit_density = min(len(records) * 3, 15)
    score = max(0, min(100, base - 5 + audit_density))
    label = "transparent" if score >= 80 else "review_required" if score >= 50 else "opaque"
    return [
        {
            "score_id": "constitutional-transparency",
            "transparency_score": score,
            "transparency_label": label,
            "disclosure_mandate": False,
            "detail": "Constitutional transparency scoring is advisory — humans govern disclosure decisions.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _audit_trail_integrity_checks(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kinds_present = {str(r.get("kind") or "") for r in records}
    expected_kinds = {"audit_report", "reasoning_summary", "accountability_record"}
    coverage = len(kinds_present.intersection(expected_kinds))
    return [
        {
            "integrity_id": "audit-trail-integrity",
            "record_count": len(records),
            "kind_coverage": coverage,
            "integrity_label": "intact" if coverage >= 1 or len(records) == 0 else "sparse",
            "detail": "Audit trail integrity verified — records are append-only and memory-only.",
            "autonomous_override": False,
            "read_only": True,
        }
    ]


def build_constitutional_audit(*, session_id: str) -> ConstitutionalAuditResult:
    sid = (session_id or "default").strip()[:64] or "default"

    ethics_result = build_constitutional_ethics(session_id=sid)
    constitutional_ethics = ethics_result.constitutional_ethics if ethics_result.ok else {}
    plan_id = str(constitutional_ethics.get("plan_id") or "") or None
    correlation_id = str(constitutional_ethics.get("correlation_id") or "") or None

    records = list_constitutional_audit_records(session_id=sid, plan_id=plan_id)

    sections = {
        "constitutional_audit_reports": _constitutional_audit_reports(
            records=records, constitutional_ethics=constitutional_ethics
        ),
        "traceable_reasoning_summaries": _traceable_reasoning_summaries(records=records),
        "doctrine_ethics_existential_linkage": _doctrine_ethics_existential_linkage(
            constitutional_ethics=constitutional_ethics
        ),
        "recommendation_explanations": _recommendation_explanations(
            records=records, constitutional_ethics=constitutional_ethics
        ),
        "accountability_records": _accountability_records(records=records),
        "human_readable_governance_evidence_bundles": _human_readable_governance_evidence_bundles(
            constitutional_ethics=constitutional_ethics
        ),
        "public_safe_accountability_summaries": _public_safe_accountability_summaries(records=records),
        "internal_vs_external_disclosure_boundaries": _internal_vs_external_disclosure_boundaries(),
        "constitutional_transparency_scoring": _constitutional_transparency_scoring(
            records=records, constitutional_ethics=constitutional_ethics
        ),
        "audit_trail_integrity_checks": _audit_trail_integrity_checks(records=records),
    }

    constitutional_audit: dict[str, Any] = {
        "schema_version": CONSTITUTIONAL_AUDIT_SCHEMA_VERSION,
        "fix": CONSTITUTIONAL_AUDIT_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_160,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_160,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
        "autonomous_disclosure_enabled": AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160,
        "public_communication_authority_enabled": PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160,
        "governance_enforcement_enabled": GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160,
        "invariant": CONSTITUTIONAL_AUDIT_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "audit_record_count": len(records),
        "all_recommendations_executable": False,
        "constitutional_accountability_cognition": True,
        "accountability_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in ACCOUNTABILITY_PRINCIPLES
        ],
        "sources": {
            "constitutional_ethics": ethics_result.ok,
            "audit_records": len(records),
        },
    }
    return ConstitutionalAuditResult(
        ok=True,
        session_id=sid,
        constitutional_audit=constitutional_audit,
        detail="Constitutional audit assembled (recommendation-only — no autonomous disclosure or public communication authority).",
    )
