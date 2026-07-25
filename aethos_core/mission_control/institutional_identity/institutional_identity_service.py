# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — institutional identity cognition from evolution + enduring constitutional intent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution
from aethos_core.mission_control.institutional_identity.institutional_identity_contract import (
    AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
    AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156,
    CONSTITUTIONAL_INTENT_LINEAGE,
    GOVERNANCE_MUTATION_PERFORMED_FIX_156,
    GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156,
    IDENTITY_COGNITION_PRINCIPLES,
    IDENTITY_RECOMMENDATION_EXECUTABLE,
    INSTITUTIONAL_IDENTITY_FIX,
    INSTITUTIONAL_IDENTITY_INVARIANT,
    INSTITUTIONAL_IDENTITY_SCHEMA_VERSION,
    INSTITUTIONAL_MISSION_IDENTITY,
    MUTATION_PERFORMED_FIX_156,
    OPERATIONAL_PHILOSOPHY,
    SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_store import (
    list_institutional_identity_records,
)


@dataclass(frozen=True)
class InstitutionalIdentityResult:
    ok: bool
    session_id: str
    identity: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _evolution_sections(evolution: dict[str, Any]) -> dict[str, Any]:
    return evolution.get("sections") or {}


def _institutional_mission_identity_records(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "mission_identity")]
    if stored:
        return stored
    return [
        {
            "identity_id": identity_id,
            "statement": statement,
            "enduring": True,
            "source": "FIX_156_default_mission_identity",
            "executable": IDENTITY_RECOMMENDATION_EXECUTABLE,
            "read_only": True,
        }
        for identity_id, statement in INSTITUTIONAL_MISSION_IDENTITY
    ]


def _constitutional_intent_lineage(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "constitutional_intent")]
    lineage = [
        {
            "intent_id": intent_id,
            "lineage_depth": idx + 1,
            "statement": statement,
            "source": "FIX_156_intent_lineage_catalog",
            "read_only": True,
        }
        for idx, (intent_id, statement) in enumerate(CONSTITUTIONAL_INTENT_LINEAGE)
    ]
    return stored + lineage


def _operational_philosophy_continuity(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "philosophy_record")]
    philosophy = [
        {
            "philosophy_id": pid,
            "statement": stmt,
            "continuity": "enduring",
            "source": "FIX_156_operational_philosophy_catalog",
            "read_only": True,
        }
        for pid, stmt in OPERATIONAL_PHILOSOPHY
    ]
    return stored + philosophy


def _governance_purpose_preservation(*, records: list[dict[str, Any]], evolution: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "purpose_preservation")]
    continuity_score = (
        (_evolution_sections(evolution).get("institutional_continuity_scoring") or {}).get("continuity_score") or 0
    )
    preserved = [
        {
            "purpose_id": "governed-operational-intelligence",
            "purpose": "Assist human operators with governed operational intelligence without autonomous authority.",
            "preserved": True,
            "read_only": True,
        },
        {
            "purpose_id": "constitutional-cognition-without-sovereignty",
            "purpose": "Reason about governance structure, doctrine, and evolution without governance sovereignty.",
            "preserved": True,
            "read_only": True,
        },
        {
            "purpose_id": "continuity-baseline",
            "purpose": f"Institutional continuity score baseline: {continuity_score} (advisory).",
            "preserved": continuity_score >= 0.5,
            "read_only": True,
        },
    ]
    return stored + preserved


def _institutional_value_drift_detection(*, evolution: dict[str, Any]) -> list[dict[str, Any]]:
    drift = _evolution_sections(evolution).get("long_horizon_drift_analysis") or []
    signals = [
        {
            "drift_id": d.get("drift_id"),
            "signal": d.get("signal"),
            "detail": d.get("detail"),
            "value_dimension": "institutional_identity",
            "recommendation_only": True,
            "read_only": True,
        }
        for d in drift
    ]
    if not signals:
        signals.append(
            {
                "drift_id": "no-value-drift",
                "detail": "No institutional value drift detected against enduring mission identity.",
                "read_only": True,
            }
        )
    return signals


def _constitutional_mission_alignment(*, evolution: dict[str, Any]) -> list[dict[str, Any]]:
    maturity = _evolution_sections(evolution).get("governance_maturity_progression") or []
    current = next((m for m in maturity if m.get("current")), {})
    return [
        {
            "alignment_id": "mission-constitutional-alignment",
            "current_maturity_stage": current.get("stage"),
            "aligned_with_mission_identity": current.get("stage") == "temporal_continuity"
            or current.get("achieved") is True,
            "detail": "Constitutional mission alignment is advisory — human governance ratifies alignment.",
            "recommendation_only": True,
            "read_only": True,
        }
    ]


def _organizational_identity_continuity(*, records: list[dict[str, Any]], evolution: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "identity_continuity")]
    narrative = (_evolution_sections(evolution).get("historical_governance_narrative_reconstruction") or [{}])[0]
    derived = [
        {
            "continuity_id": "organizational-identity",
            "epoch_count": narrative.get("epoch_count"),
            "identity_record_count": len(records),
            "detail": "Organizational identity continuity spans constitutional epochs with human stewardship.",
            "autonomous_redirection": False,
            "read_only": True,
        }
    ]
    return stored + derived


def _doctrine_purpose_consistency(*, evolution: dict[str, Any]) -> list[dict[str, Any]]:
    eras = _evolution_sections(evolution).get("doctrine_era_tracking") or []
    constitutional_eras = [e for e in eras if e.get("epoch_id", "").startswith("epoch_constitutional")]
    return [
        {
            "consistency_id": "doctrine-purpose-alignment",
            "constitutional_era_count": len(constitutional_eras),
            "consistent": len(constitutional_eras) >= 3,
            "detail": (
                "Doctrine eras align with enduring governance purpose — constitutional cognition without sovereign authority."
                if len(constitutional_eras) >= 3
                else "Insufficient doctrine era coverage for purpose consistency analysis."
            ),
            "read_only": True,
        }
    ]


def _constitutional_intent_reconstruction(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    intents = _by_kind(records, "constitutional_intent")
    if intents:
        return [{**r, "reconstructed": False, "read_only": True} for r in intents]
    return [
        {
            "reconstruction_id": "default-constitutional-intent",
            "intent_chain": [intent_id for intent_id, _ in CONSTITUTIONAL_INTENT_LINEAGE],
            "detail": "Constitutional intent reconstructed from enduring lineage catalog and evolution context.",
            "reconstructed": True,
            "read_only": True,
        }
    ]


def _institutional_narrative_continuity(*, records: list[dict[str, Any]], evolution: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "narrative_continuity")]
    historical = _evolution_sections(evolution).get("historical_governance_narrative_reconstruction") or []
    if stored:
        return stored
    if historical and historical[0].get("timeline"):
        return [
            {
                "narrative_continuity_id": "evolution-derived-narrative",
                "epoch_count": historical[0].get("epoch_count"),
                "detail": historical[0].get("detail"),
                "source": "FIX_155_historical_narrative",
                "read_only": True,
            }
        ]
    return [
        {
            "narrative_continuity_id": "default-narrative",
            "detail": "Institutional narrative continuity begins with operator-authored identity records.",
            "read_only": True,
        }
    ]


def build_institutional_identity(*, session_id: str) -> InstitutionalIdentityResult:
    sid = (session_id or "default").strip()[:64] or "default"

    evolution_result = build_governance_evolution(session_id=sid)
    evolution = evolution_result.evolution if evolution_result.ok else {}
    plan_id = str(evolution.get("plan_id") or "") or None
    correlation_id = str(evolution.get("correlation_id") or "") or None

    records = list_institutional_identity_records(session_id=sid, plan_id=plan_id)

    sections = {
        "institutional_mission_identity_records": _institutional_mission_identity_records(records=records),
        "constitutional_intent_lineage": _constitutional_intent_lineage(records=records),
        "operational_philosophy_continuity": _operational_philosophy_continuity(records=records),
        "governance_purpose_preservation": _governance_purpose_preservation(records=records, evolution=evolution),
        "institutional_value_drift_detection": _institutional_value_drift_detection(evolution=evolution),
        "constitutional_mission_alignment": _constitutional_mission_alignment(evolution=evolution),
        "organizational_identity_continuity": _organizational_identity_continuity(records=records, evolution=evolution),
        "doctrine_purpose_consistency": _doctrine_purpose_consistency(evolution=evolution),
        "constitutional_intent_reconstruction": _constitutional_intent_reconstruction(records=records),
        "institutional_narrative_continuity": _institutional_narrative_continuity(records=records, evolution=evolution),
    }

    identity: dict[str, Any] = {
        "schema_version": INSTITUTIONAL_IDENTITY_SCHEMA_VERSION,
        "fix": INSTITUTIONAL_IDENTITY_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_156,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_156,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
        "autonomous_institutional_redirection_enabled": AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156,
        "self_authored_mission_changes_enabled": SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156,
        "automatic_constitutional_rewriting_enabled": AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156,
        "governance_sovereignty_delegated": GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156,
        "invariant": INSTITUTIONAL_IDENTITY_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "identity_record_count": len(records),
        "all_recommendations_executable": False,
        "institutional_identity_cognition": True,
        "identity_cognition_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in IDENTITY_COGNITION_PRINCIPLES
        ],
        "sources": {
            "governance_evolution": evolution_result.ok,
            "identity_records": len(records),
        },
    }
    return InstitutionalIdentityResult(
        ok=True,
        session_id=sid,
        identity=identity,
        detail="Institutional identity assembled (recommendation-only — no autonomous redirection or constitutional rewriting).",
    )
