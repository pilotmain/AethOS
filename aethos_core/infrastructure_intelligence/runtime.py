# SPDX-License-Identifier: Apache-2.0
"""Infrastructure intelligence — unified operational awareness."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure.docker.runtime import analyze_docker_runtime
from aethos_core.infrastructure.kubernetes.runtime import verify_kubernetes_rollout
from aethos_core.infrastructure_confidence.runtime import assess_infrastructure_confidence
from aethos_core.infrastructure_harness.harness_runtime import harness_state
from aethos_core.infrastructure_reconciliation.runtime import reconcile_infrastructure
from aethos_core.runtime_supervision.runtime import observe_supervision_state
from aethos_core.topology.runtime import build_topology_intelligence


def assess_infrastructure_state(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """Aggregate infrastructure operational awareness across all Phase 11.2 slices."""
    if not runtime_snapshot:
        from aethos_core.infrastructure.docker.runtime import _default_snapshot as docker_default
        from aethos_core.infrastructure.kubernetes.runtime import _default_snapshot as k8s_default

        runtime_snapshot = {**docker_default(), **k8s_default()}
    docker = analyze_docker_runtime(runtime_snapshot=runtime_snapshot)
    kubernetes = verify_kubernetes_rollout(runtime_snapshot=runtime_snapshot)
    topology = build_topology_intelligence(runtime_snapshot=runtime_snapshot)
    supervision = observe_supervision_state(runtime_snapshot=runtime_snapshot)
    reconciliation = reconcile_infrastructure(runtime_snapshot=runtime_snapshot)
    confidence = assess_infrastructure_confidence(runtime_snapshot=runtime_snapshot)
    harness = harness_state()
    return {
        "ok": True,
        "phase": "11.2",
        "harness_version": harness.get("harness_version"),
        "docker": docker,
        "kubernetes": kubernetes,
        "topology": topology,
        "supervision": supervision,
        "reconciliation": reconciliation,
        "confidence": confidence,
        "harness": harness,
        "capabilities": _capability_summary(docker, kubernetes),
        "summary": confidence.get("narrative", ""),
    }


def _capability_summary(docker: dict[str, Any], kubernetes: dict[str, Any]) -> dict[str, str]:
    caps: dict[str, str] = {}
    caps.update(docker.get("capabilities") or {})
    caps.update({f"k8s_{k}": v for k, v in (kubernetes.get("capabilities") or {}).items()})
    caps["mutation_reconciliation"] = "stable"
    caps["topology_intelligence"] = "stable"
    caps["infrastructure_reconciliation"] = "beta"
    return caps
