# SPDX-License-Identifier: Apache-2.0
"""Infrastructure confidence orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_confidence.cluster_integrity import score_cluster_integrity
from aethos_core.infrastructure_confidence.dependency_weighting import weight_dependency_confidence
from aethos_core.infrastructure_confidence.infrastructure_truth_score import compute_infrastructure_truth_score
from aethos_core.infrastructure_confidence.recovery_decay import assess_recovery_decay
from aethos_core.infrastructure_confidence.topology_confidence import score_topology_confidence
from aethos_core.infrastructure_reconciliation.runtime import reconcile_infrastructure


def assess_infrastructure_confidence(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    reconciliation = reconcile_infrastructure(runtime_snapshot=runtime_snapshot)
    topology_score = score_topology_confidence(topology=reconciliation.get("topology") or {})
    cluster_score = score_cluster_integrity(kubernetes=reconciliation.get("kubernetes") or {})
    dependency_score = weight_dependency_confidence(
        topology=reconciliation.get("topology") or {},
        docker=reconciliation.get("docker") or {},
    )
    recovery_decay = assess_recovery_decay(supervision=reconciliation.get("supervision") or {})
    recovery_component = max(0.0, 0.8 - recovery_decay.get("recovery_decay", 0))
    truth = compute_infrastructure_truth_score(
        components={
            "topology": topology_score.get("topology_confidence", 0.5),
            "cluster": cluster_score.get("cluster_integrity", 0.5),
            "dependency": dependency_score.get("dependency_confidence", 0.5),
            "recovery": recovery_component,
        }
    )
    narrative = _build_narrative(reconciliation, truth)
    return {
        "ok": True,
        "confidence": truth,
        "topology": topology_score,
        "cluster": cluster_score,
        "dependency": dependency_score,
        "recovery_decay": recovery_decay,
        "reconciliation": reconciliation,
        "narrative": narrative,
        "summary": narrative,
    }


def _build_narrative(reconciliation: dict[str, Any], truth: dict[str, Any]) -> str:
    docker = reconciliation.get("docker") or {}
    pressure = docker.get("pressure") or {}
    elevated = pressure.get("elevated_containers") or []
    loops = reconciliation.get("supervision", {}).get("restart_patterns", {}).get("unstable_workloads") or []
    if elevated or loops:
        parts = ["Operational infrastructure remains stable overall,"]
        if elevated:
            names = ", ".join(str(e.get("name")) for e in elevated[:2])
            parts.append(f"though elevated {names} memory pressure")
        if loops:
            parts.append(f"and intermittent {'/'.join(str(w) for w in loops[:2])} recovery events")
        parts.append("continue to be monitored for extended stabilization assurance.")
        return " ".join(parts)
    return (
        "Operational infrastructure remains stable overall. "
        f"Infrastructure truth score: {truth.get('infrastructure_truth_score', 0):.0%}. "
        "Extended monitoring remains active."
    )
