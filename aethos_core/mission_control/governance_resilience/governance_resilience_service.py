# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — institutional resilience cognition from coherence under stress conditions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence
from aethos_core.mission_control.governance_resilience.governance_resilience_contract import (
    AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
    AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154,
    GOVERNANCE_MUTATION_PERFORMED_FIX_154,
    GOVERNANCE_RESILIENCE_FIX,
    GOVERNANCE_RESILIENCE_INVARIANT,
    GOVERNANCE_RESILIENCE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_154,
    OVERRIDE_AUTHORITY_ENABLED_FIX_154,
    RESILIENCE_COGNITION_PRINCIPLES,
    RESILIENCE_SIMULATION_EXECUTABLE,
    SELF_HEALING_GOVERNANCE_ENABLED_FIX_154,
    STRESS_SCENARIO_CATALOG,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_store import (
    list_governance_resilience_records,
)
from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import build_mission_orchestration


@dataclass(frozen=True)
class GovernanceResilienceResult:
    ok: bool
    session_id: str
    resilience: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _coherence_sections(coherence: dict[str, Any]) -> dict[str, Any]:
    return coherence.get("sections") or {}


def _governance_stress_scenarios(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "simulation_only": True, "read_only": True} for r in _by_kind(records, "stress_scenario")]
    catalog = [
        {
            "scenario_id": sid,
            "severity": severity,
            "description": desc,
            "simulation_only": True,
            "executable": RESILIENCE_SIMULATION_EXECUTABLE,
            "source": "FIX_154_stress_catalog",
            "read_only": True,
        }
        for sid, severity, desc in STRESS_SCENARIO_CATALOG
    ]
    return stored + catalog


def _approval_chain_overload_simulation(*, session_id: str) -> list[dict[str, Any]]:
    inbox = approval_inbox_payload(session_id=session_id)
    pending = list(inbox.get("pending_approvals") or inbox.get("items") or [])
    pending_count = len(pending)
    overload_threshold = 3
    simulated_load = pending_count + 5
    return [
        {
            "simulation_id": "approval-chain-overload",
            "current_pending": pending_count,
            "simulated_pending": simulated_load,
            "overload_detected": simulated_load >= overload_threshold,
            "impact": "Advisory: approval queue saturation may delay governance gate progression.",
            "simulation_only": True,
            "executable": RESILIENCE_SIMULATION_EXECUTABLE,
            "read_only": True,
        }
    ]


def _incident_surge_resilience_analysis(*, session_id: str, coherence: dict[str, Any]) -> list[dict[str, Any]]:
    orchestration = build_mission_orchestration(session_id=session_id)
    orch = orchestration.orchestration if orchestration.ok else {}
    health = ((orch.get("sections") or {}).get("cross_lane_mission_health") or {})
    open_incidents = int(health.get("open_incidents") or 0)
    stability = (_coherence_sections(coherence).get("governance_stability_indicators") or [{}])[0]
    stability_label = stability.get("stability_label", "unknown")
    surge_level = "critical" if open_incidents >= 2 else "elevated" if open_incidents >= 1 else "normal"
    return [
        {
            "analysis_id": "incident-surge-resilience",
            "open_incidents": open_incidents,
            "surge_level": surge_level,
            "governance_stability": stability_label,
            "detail": (
                "Simulated incident surge stresses governance review capacity — human sovereignty required."
                if surge_level != "normal"
                else "No active incident surge stress detected in current mission context."
            ),
            "simulation_only": True,
            "read_only": True,
        }
    ]


def _quorum_failure_modeling(*, coherence: dict[str, Any]) -> list[dict[str, Any]]:
    contradictions = _coherence_sections(coherence).get("governance_contradiction_surfacing") or []
    active = [c for c in contradictions if c.get("contradiction") != "no_contradictions_surfaced"]
    quorum_risk = "high" if len(active) >= 2 else "moderate" if active else "low"
    return [
        {
            "model_id": "quorum-failure",
            "quorum_risk": quorum_risk,
            "active_contradiction_count": len(active),
            "detail": (
                "Simulated quorum failure: insufficient consensus under competing governance readings."
                if quorum_risk == "high"
                else "Quorum composition appears viable under current coherence signals."
            ),
            "simulation_only": True,
            "read_only": True,
        }
    ]


def _governance_fragmentation_stress(*, coherence: dict[str, Any]) -> list[dict[str, Any]]:
    fragmentation = _coherence_sections(coherence).get("policy_fragmentation_analysis") or []
    high_frag = [f for f in fragmentation if f.get("fragmentation_level") == "high"]
    return [
        {
            "stress_id": f.get("fragmentation_id", "fragmentation"),
            "fragmentation_level": f.get("fragmentation_level"),
            "detail": f.get("detail"),
            "simulation_only": True,
            "read_only": True,
        }
        for f in fragmentation
    ] or [
        {
            "stress_id": "no-fragmentation-stress",
            "fragmentation_level": "low",
            "detail": "No governance fragmentation stress detected.",
            "read_only": True,
        }
    ]


def _operator_loss_handoff_resilience(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "handoff_stress_note")]
    derived = [
        {
            "handoff_id": "operator-loss-simulation",
            "scenario": "primary_operator_unavailable",
            "continuity_requirement": "Multi-operator collaboration memory (FIX 149) preserves institutional continuity.",
            "delegated_authority": False,
            "detail": "Simulated operator loss — handoff resilience depends on human governance, not autonomous delegation.",
            "simulation_only": True,
            "read_only": True,
        }
    ]
    return stored + derived


def _doctrine_conflict_escalation_scenarios(*, coherence: dict[str, Any]) -> list[dict[str, Any]]:
    contradictions = _coherence_sections(coherence).get("governance_contradiction_surfacing") or []
    conflicts = _coherence_sections(coherence).get("doctrine_topology_consistency_analysis") or []
    scenarios: list[dict[str, Any]] = []
    for c in contradictions:
        if c.get("severity") in ("high", "critical", None) and c.get("contradiction") != "no_contradictions_surfaced":
            scenarios.append(
                {
                    "escalation_id": c.get("contradiction_id"),
                    "escalation_level": c.get("severity", "moderate"),
                    "conflict": c.get("contradiction"),
                    "detail": c.get("detail"),
                    "simulation_only": True,
                    "read_only": True,
                }
            )
    for check in conflicts:
        if check.get("status") in ("fail", "warn"):
            scenarios.append(
                {
                    "escalation_id": check.get("analysis_id"),
                    "escalation_level": check.get("status"),
                    "conflict": "doctrine_topology_misalignment",
                    "detail": check.get("detail"),
                    "simulation_only": True,
                    "read_only": True,
                }
            )
    if not scenarios:
        scenarios.append(
            {
                "escalation_id": "no-escalation",
                "escalation_level": "none",
                "detail": "No doctrine conflict escalation scenarios under current stress modeling.",
                "read_only": True,
            }
        )
    return scenarios


def _trust_boundary_breach_simulation(*, records: list[dict[str, Any]], coherence: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "breach_simulation_note")]
    trust_checks = _coherence_sections(coherence).get("trust_boundary_consistency_analysis") or []
    derived = [
        {
            "simulation_id": "trust-boundary-breach-hypothetical",
            "boundary": check.get("boundary", "topology"),
            "status": check.get("status"),
            "breach_simulated": check.get("status") == "fail",
            "detail": (
                f"Hypothetical breach simulation: {check.get('detail')}"
                if check.get("status") == "fail"
                else "Trust boundaries hold under hypothetical breach simulation."
            ),
            "simulation_only": True,
            "executable": RESILIENCE_SIMULATION_EXECUTABLE,
            "read_only": True,
        }
        for check in trust_checks[:3]
    ]
    if not derived:
        derived.append(
            {
                "simulation_id": "trust-boundary-stable",
                "breach_simulated": False,
                "detail": "No trust-boundary breach detected in stress simulation.",
                "read_only": True,
            }
        )
    return stored + derived


def _governance_recovery_posture(*, records: list[dict[str, Any]], coherence: dict[str, Any]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "recovery_posture_note")]
    integrity = _coherence_sections(coherence).get("institutional_integrity_scoring") or {}
    score = float(integrity.get("integrity_score") or 0)
    posture = "recoverable" if score >= 0.7 else "stressed" if score >= 0.5 else "critical_review_required"
    derived = [
        {
            "posture_id": "recovery-posture-composite",
            "recovery_posture": posture,
            "integrity_score": score,
            "detail": (
                "Governance recovery posture is advisory — human ratification required before any institutional reset."
            ),
            "autonomous_recovery": False,
            "simulation_only": True,
            "read_only": True,
        }
    ]
    return stored + derived


def _institutional_resilience_scoring(*, coherence: dict[str, Any]) -> dict[str, Any]:
    integrity = _coherence_sections(coherence).get("institutional_integrity_scoring") or {}
    stability_items = _coherence_sections(coherence).get("governance_stability_indicators") or []
    stability = (stability_items[-1] if stability_items else {}).get("stability_label", "unknown")
    base = float(integrity.get("integrity_score") or 0.5)
    stability_penalty = {"at_risk": 0.2, "monitoring": 0.1, "stable": 0.0}.get(str(stability), 0.05)
    score = round(max(0.0, min(0.95, base - stability_penalty)), 2)
    label = "resilient" if score >= 0.75 else "stressed" if score >= 0.55 else "fragile"
    return {
        "resilience_score": score,
        "resilience_label": label,
        "integrity_baseline": integrity.get("integrity_score"),
        "stability_label": stability,
        "scoring_note": "Advisory institutional resilience score — simulation-only, not adaptive correction.",
        "simulation_only": True,
        "executable": RESILIENCE_SIMULATION_EXECUTABLE,
        "read_only": True,
    }


def build_governance_resilience(*, session_id: str) -> GovernanceResilienceResult:
    sid = (session_id or "default").strip()[:64] or "default"

    coherence_result = build_governance_coherence(session_id=sid)
    coherence = coherence_result.coherence if coherence_result.ok else {}
    plan_id = str(coherence.get("plan_id") or "") or None
    correlation_id = str(coherence.get("correlation_id") or "") or None

    records = list_governance_resilience_records(session_id=sid, plan_id=plan_id)
    resilience_score = _institutional_resilience_scoring(coherence=coherence)

    sections = {
        "governance_stress_scenarios": _governance_stress_scenarios(records=records),
        "approval_chain_overload_simulation": _approval_chain_overload_simulation(session_id=sid),
        "incident_surge_resilience_analysis": _incident_surge_resilience_analysis(
            session_id=sid, coherence=coherence
        ),
        "quorum_failure_modeling": _quorum_failure_modeling(coherence=coherence),
        "governance_fragmentation_stress": _governance_fragmentation_stress(coherence=coherence),
        "operator_loss_handoff_resilience": _operator_loss_handoff_resilience(records=records),
        "doctrine_conflict_escalation_scenarios": _doctrine_conflict_escalation_scenarios(coherence=coherence),
        "trust_boundary_breach_simulation": _trust_boundary_breach_simulation(records=records, coherence=coherence),
        "governance_recovery_posture": _governance_recovery_posture(records=records, coherence=coherence),
        "institutional_resilience_scoring": resilience_score,
    }

    resilience: dict[str, Any] = {
        "schema_version": GOVERNANCE_RESILIENCE_SCHEMA_VERSION,
        "fix": GOVERNANCE_RESILIENCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "simulation_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_154,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_154,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
        "automatic_governance_adaptation_enabled": AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154,
        "autonomous_resilience_correction_enabled": AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154,
        "self_healing_governance_enabled": SELF_HEALING_GOVERNANCE_ENABLED_FIX_154,
        "override_authority_enabled": OVERRIDE_AUTHORITY_ENABLED_FIX_154,
        "invariant": GOVERNANCE_RESILIENCE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "resilience_record_count": len(records),
        "all_simulations_executable": False,
        "institutional_resilience_cognition": True,
        "resilience_cognition_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in RESILIENCE_COGNITION_PRINCIPLES
        ],
        "sources": {
            "governance_coherence": coherence_result.ok,
            "resilience_records": len(records),
        },
    }
    return GovernanceResilienceResult(
        ok=True,
        session_id=sid,
        resilience=resilience,
        detail="Governance resilience assembled (simulation-only — no autonomous adaptation or correction).",
    )
