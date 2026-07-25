# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — institutional temporal governance cognition from resilience across eras."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import list_governance_doctrine_records
from aethos_core.mission_control.governance_evolution.governance_evolution_contract import (
    AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
    AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155,
    CONSTITUTIONAL_EPOCHS,
    EVOLUTION_RECOMMENDATION_EXECUTABLE,
    GOVERNANCE_EVOLUTION_FIX,
    GOVERNANCE_EVOLUTION_INVARIANT,
    GOVERNANCE_EVOLUTION_SCHEMA_VERSION,
    GOVERNANCE_GENERATIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_155,
    MATURITY_STAGES,
    MUTATION_PERFORMED_FIX_155,
    POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155,
    SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155,
    TEMPORAL_COGNITION_PRINCIPLES,
)
from aethos_core.mission_control.governance_evolution.governance_evolution_store import (
    list_governance_evolution_records,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_service import build_governance_resilience
from aethos_core.mission_control.mission_control_ui_freeze_contract import MISSION_CONTROL_SHIPPED_FIXES


@dataclass(frozen=True)
class GovernanceEvolutionResult:
    ok: bool
    session_id: str
    evolution: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _resilience_sections(resilience: dict[str, Any]) -> dict[str, Any]:
    return resilience.get("sections") or {}


def _doctrine_era_tracking(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "doctrine_era")]
    doctrine_versions = [
        r for r in list_governance_doctrine_records(session_id=None) if r.get("kind") == "doctrine_version"
    ]
    derived = [
        {
            "era_id": f"era-{epoch_id}",
            "epoch_id": epoch_id,
            "fix_range": fix_range,
            "description": desc,
            "current": epoch_id == "epoch_temporal_continuity",
            "source": "FIX_155_constitutional_epoch_catalog",
            "read_only": True,
        }
        for epoch_id, fix_range, desc in CONSTITUTIONAL_EPOCHS
    ]
    for version in doctrine_versions[-5:]:
        derived.append(
            {
                "era_id": f"era-record-{version.get('record_id')}",
                "doctrine_version": version.get("content"),
                "recorded_at": version.get("recorded_at"),
                "session_id": version.get("session_id"),
                "source": "doctrine_version_record",
                "read_only": True,
            }
        )
    return stored + derived


def _governance_generation_lineage(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "generation_marker")]
    lineage = [
        {
            "generation_id": gen_id,
            "description": desc,
            "lineage_depth": idx + 1,
            "source": "FIX_155_generation_catalog",
            "read_only": True,
        }
        for idx, (gen_id, desc) in enumerate(GOVERNANCE_GENERATIONS)
    ]
    return stored + lineage


def _institutional_transition_analysis(*, records: list[dict[str, Any]], resilience: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "transition_note")]
    recovery = (_resilience_sections(resilience).get("governance_recovery_posture") or [{}])[0]
    transitions = list(stored)
    transitions.append(
        {
            "transition_id": "operational-to-constitutional",
            "from_era": "epoch_operational",
            "to_era": "epoch_constitutional_doctrine",
            "status": "completed",
            "detail": "Mission Control operational era transitioned into constitutional governance stack (FIX 150–155).",
            "autonomous_transition": False,
            "read_only": True,
        }
    )
    if recovery.get("recovery_posture"):
        transitions.append(
            {
                "transition_id": "resilience-to-continuity",
                "from_era": "epoch_constitutional_resilience",
                "to_era": "epoch_temporal_continuity",
                "status": "in_progress",
                "detail": f"Recovery posture `{recovery.get('recovery_posture')}` informs continuity transition planning.",
                "read_only": True,
            }
        )
    return transitions


def _freeze_era_continuity() -> list[dict[str, Any]]:
    shipped = list(MISSION_CONTROL_SHIPPED_FIXES)
    constitutional_fixes = [f for f in shipped if f in {f"FIX {n}" for n in range(150, 156)}]
    return [
        {
            "continuity_id": "freeze-era-baseline",
            "shipped_fix_count": len(shipped),
            "constitutional_fix_count": len(constitutional_fixes),
            "latest_constitutional_fix": constitutional_fixes[-1] if constitutional_fixes else None,
            "detail": "Freeze-era continuity honors contract-frozen FIX baselines across institutional transitions.",
            "autonomous_migration": False,
            "read_only": True,
        }
    ]


def _governance_maturity_progression(*, resilience: dict[str, Any]) -> list[dict[str, Any]]:
    resilience_score = (
        (_resilience_sections(resilience).get("institutional_resilience_scoring") or {}).get("resilience_score") or 0
    )
    current_stage = "temporal_continuity"
    stage_index = MATURITY_STAGES.index(current_stage)
    progression = []
    for idx, stage in enumerate(MATURITY_STAGES):
        progression.append(
            {
                "stage": stage,
                "stage_index": idx + 1,
                "achieved": idx <= stage_index,
                "current": stage == current_stage,
                "read_only": True,
            }
        )
    progression.append(
        {
            "maturity_summary_id": "composite-maturity",
            "current_stage": current_stage,
            "resilience_score": resilience_score,
            "detail": "Governance maturity progression is advisory — no autonomous evolution.",
            "read_only": True,
        }
    )
    return progression


def _long_horizon_drift_analysis(*, resilience: dict[str, Any]) -> list[dict[str, Any]]:
    drift = _resilience_sections(resilience).get("precedent_drift_detection") or []
    return_items: list[dict[str, Any]] = []
    for signal in drift:
        return_items.append(
            {
                "drift_id": signal.get("drift_id"),
                "horizon": "long",
                "signal": signal.get("signal"),
                "detail": signal.get("detail"),
                "recommendation_only": True,
                "read_only": True,
            }
        )
    if not return_items:
        return_items.append(
            {
                "drift_id": "no-long-horizon-drift",
                "horizon": "long",
                "detail": "No long-horizon governance drift detected across institutional eras.",
                "read_only": True,
            }
        )
    return return_items


def _constitutional_epoch_comparison() -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    epochs = list(CONSTITUTIONAL_EPOCHS)
    for idx in range(len(epochs) - 1):
        curr_id, curr_range, curr_desc = epochs[idx]
        next_id, next_range, next_desc = epochs[idx + 1]
        comparisons.append(
            {
                "comparison_id": f"{curr_id}-to-{next_id}",
                "from_epoch": curr_id,
                "to_epoch": next_id,
                "from_fix_range": curr_range,
                "to_fix_range": next_range,
                "transition_note": f"{curr_desc} → {next_desc}",
                "autonomous_migration": False,
                "read_only": True,
            }
        )
    return comparisons


def _governance_migration_reasoning(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "continuity_observation")]
    reasoning = list(stored)
    reasoning.append(
        {
            "reasoning_id": "doctrine-migration-advisory",
            "migration_type": "doctrine_era_transition",
            "executable": EVOLUTION_RECOMMENDATION_EXECUTABLE,
            "detail": (
                "Governance migration reasoning is advisory only — doctrine migration requires "
                "human ratification via amendment proposals (FIX 151), never autonomous execution."
            ),
            "read_only": True,
        }
    )
    return reasoning


def _institutional_continuity_scoring(*, resilience: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    resilience_score = float(
        (_resilience_sections(resilience).get("institutional_resilience_scoring") or {}).get("resilience_score") or 0.5
    )
    era_count = len(_by_kind(records, "doctrine_era"))
    narrative_count = len(_by_kind(records, "narrative_record"))
    base = resilience_score * 0.7 + min(era_count + narrative_count, 5) * 0.06
    score = round(max(0.0, min(0.95, base)), 2)
    label = "strong" if score >= 0.8 else "developing" if score >= 0.6 else "emerging"
    return {
        "continuity_score": score,
        "continuity_label": label,
        "resilience_baseline": resilience_score,
        "recorded_era_markers": era_count,
        "recorded_narratives": narrative_count,
        "scoring_note": "Advisory institutional continuity score — no autonomous evolution or migration.",
        "recommendation_only": True,
        "executable": EVOLUTION_RECOMMENDATION_EXECUTABLE,
        "read_only": True,
    }


def _historical_governance_narrative_reconstruction(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    narratives = [{**r, "read_only": True} for r in _by_kind(records, "narrative_record")]
    if narratives:
        return narratives
    timeline: list[dict[str, Any]] = []
    for epoch_id, fix_range, desc in CONSTITUTIONAL_EPOCHS:
        timeline.append(
            {
                "narrative_id": f"narrative-{epoch_id}",
                "epoch": epoch_id,
                "fix_range": fix_range,
                "narrative": desc,
                "reconstructed": True,
                "source": "FIX_155_epoch_catalog",
                "read_only": True,
            }
        )
    return [
        {
            "reconstruction_id": "institutional-governance-timeline",
            "epoch_count": len(timeline),
            "timeline": timeline,
            "detail": "Historical governance narrative reconstructed from constitutional epoch catalog and records.",
            "read_only": True,
        }
    ]


def build_governance_evolution(*, session_id: str) -> GovernanceEvolutionResult:
    sid = (session_id or "default").strip()[:64] or "default"

    resilience_result = build_governance_resilience(session_id=sid)
    resilience = resilience_result.resilience if resilience_result.ok else {}
    plan_id = str(resilience.get("plan_id") or "") or None
    correlation_id = str(resilience.get("correlation_id") or "") or None

    records = list_governance_evolution_records(session_id=sid, plan_id=plan_id)
    continuity_score = _institutional_continuity_scoring(resilience=resilience, records=records)

    sections = {
        "doctrine_era_tracking": _doctrine_era_tracking(records=records),
        "governance_generation_lineage": _governance_generation_lineage(records=records),
        "institutional_transition_analysis": _institutional_transition_analysis(
            records=records, resilience=resilience
        ),
        "freeze_era_continuity": _freeze_era_continuity(),
        "governance_maturity_progression": _governance_maturity_progression(resilience=resilience),
        "long_horizon_drift_analysis": _long_horizon_drift_analysis(resilience=resilience),
        "constitutional_epoch_comparison": _constitutional_epoch_comparison(),
        "governance_migration_reasoning": _governance_migration_reasoning(records=records),
        "institutional_continuity_scoring": continuity_score,
        "historical_governance_narrative_reconstruction": _historical_governance_narrative_reconstruction(
            records=records
        ),
    }

    evolution: dict[str, Any] = {
        "schema_version": GOVERNANCE_EVOLUTION_SCHEMA_VERSION,
        "fix": GOVERNANCE_EVOLUTION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_155,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_155,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
        "autonomous_governance_evolution_enabled": AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155,
        "self_directed_institutional_transformation_enabled": SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155,
        "automatic_doctrine_migration_enabled": AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155,
        "policy_mutation_authority_enabled": POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155,
        "invariant": GOVERNANCE_EVOLUTION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "evolution_record_count": len(records),
        "all_recommendations_executable": False,
        "institutional_temporal_governance_cognition": True,
        "temporal_cognition_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in TEMPORAL_COGNITION_PRINCIPLES
        ],
        "sources": {
            "governance_resilience": resilience_result.ok,
            "evolution_records": len(records),
        },
    }
    return GovernanceEvolutionResult(
        ok=True,
        session_id=sid,
        evolution=evolution,
        detail="Governance evolution assembled (recommendation-only — no autonomous evolution or doctrine migration).",
    )
