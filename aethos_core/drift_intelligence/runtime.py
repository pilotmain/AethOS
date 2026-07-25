# SPDX-License-Identifier: Apache-2.0
"""Drift intelligence orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.drift_intelligence.configuration_divergence import detect_configuration_divergence
from aethos_core.drift_intelligence.degradation_patterns import detect_degradation_patterns
from aethos_core.drift_intelligence.entropy_tracking import track_operational_entropy
from aethos_core.drift_intelligence.replay_drift import assess_replay_drift
from aethos_core.drift_intelligence.telemetry_anomalies import detect_telemetry_anomalies
from aethos_core.drift_intelligence.topology_instability import assess_topology_instability
from aethos_core.infrastructure_intelligence.runtime import assess_infrastructure_state
from aethos_core.recovery_orchestration.recovery_memory import recovery_memory_state


def assess_drift_intelligence(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    infrastructure = assess_infrastructure_state(runtime_snapshot=runtime_snapshot)
    supervision = infrastructure.get("supervision") or {}
    topology = infrastructure.get("topology") or {}
    reconciliation = infrastructure.get("reconciliation") or {}
    recovery_mem = recovery_memory_state()
    from aethos_core.reliability_memory.replay_memory import replay_memory_state

    replay_mem = replay_memory_state()
    degradation = detect_degradation_patterns(supervision=supervision, memory=recovery_mem)
    entropy = track_operational_entropy(infrastructure=infrastructure)
    config = detect_configuration_divergence(reconciliation=reconciliation)
    replay = assess_replay_drift(memory=replay_mem)
    telemetry = detect_telemetry_anomalies(infrastructure=infrastructure)
    topo_instability = assess_topology_instability(topology=topology)
    drift_bounded = not (degradation.get("degradation_detected") and entropy.get("elevated"))
    summary = _build_summary(degradation, replay, infrastructure)
    return {
        "ok": True,
        "drift_bounded": drift_bounded,
        "maturity": "stable" if drift_bounded else "beta",
        "degradation": degradation,
        "entropy": entropy,
        "configuration": config,
        "replay": replay,
        "telemetry": telemetry,
        "topology_instability": topo_instability,
        "summary": summary,
    }


def _build_summary(degradation: dict[str, Any], replay: dict[str, Any], infrastructure: dict[str, Any]) -> str:
    docker = infrastructure.get("docker") or {}
    elevated = docker.get("pressure", {}).get("elevated_containers") or []
    parts = ["Operational infrastructure remains stable overall,"]
    if replay.get("replay_continuity_degraded"):
        parts.append("though recurring replay continuity degradation")
    if elevated:
        names = "/".join(str(e.get("name")) for e in elevated[:2])
        parts.append(f"and elevated {names} pressure patterns")
    if len(parts) == 1:
        return "Operational infrastructure remains stable overall. Drift remains bounded."
    parts.append("continue to be monitored for long-term stabilization assurance.")
    return " ".join(parts)
