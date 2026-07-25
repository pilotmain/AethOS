# SPDX-License-Identifier: Apache-2.0
"""Infrastructure reconciliation orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_reconciliation.desired_vs_actual import reconcile_desired_vs_actual
from aethos_core.infrastructure_reconciliation.drift_repair_detection import detect_drift_repair
from aethos_core.infrastructure_reconciliation.infrastructure_truth import assess_infrastructure_truth
from aethos_core.infrastructure_reconciliation.reconciliation_memory import record_reconciliation, reconciliation_memory_state
from aethos_core.infrastructure_reconciliation.topology_recovery import analyze_topology_recovery
from aethos_core.infrastructure_reconciliation.verification_windows import active_verification_windows
from aethos_core.infrastructure.docker.runtime import analyze_docker_runtime
from aethos_core.infrastructure.kubernetes.runtime import verify_kubernetes_rollout
from aethos_core.runtime_supervision.runtime import observe_supervision_state
from aethos_core.topology.runtime import build_topology_intelligence


def reconcile_infrastructure(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    if not runtime_snapshot:
        from aethos_core.infrastructure.docker.runtime import _default_snapshot as docker_default
        from aethos_core.infrastructure.kubernetes.runtime import _default_snapshot as k8s_default

        runtime_snapshot = {**docker_default(), **k8s_default()}
    docker = analyze_docker_runtime(runtime_snapshot=runtime_snapshot)
    kubernetes = verify_kubernetes_rollout(runtime_snapshot=runtime_snapshot)
    topology = build_topology_intelligence(runtime_snapshot=runtime_snapshot)
    supervision = observe_supervision_state(runtime_snapshot=runtime_snapshot)

    desired = runtime_snapshot.get("desired") or {"services": [c.get("name") for c in runtime_snapshot.get("containers") or [] if isinstance(c, dict)]}
    observed = {"services": [c.get("name") for c in (runtime_snapshot.get("containers") or []) if isinstance(c, dict)], "containers": runtime_snapshot.get("containers")}
    state_diff = reconcile_desired_vs_actual(desired=desired, observed=observed)
    drift_repair = detect_drift_repair(state_diff=state_diff, drift=kubernetes.get("drift") or {})
    topology_recovery = analyze_topology_recovery(propagation=topology.get("propagation") or {}, supervision=supervision)
    truth = assess_infrastructure_truth(docker=docker, kubernetes=kubernetes, reconciliation={"reconciled": state_diff.get("aligned")})
    windows = active_verification_windows(stabilization=supervision.get("stabilization") or {})

    reconciled = state_diff.get("aligned") and truth.get("truth_score", 0) >= 0.6
    result = {
        "ok": True,
        "reconciled": reconciled,
        "docker": docker,
        "kubernetes": kubernetes,
        "topology": topology,
        "supervision": supervision,
        "state_diff": state_diff,
        "drift_repair": drift_repair,
        "topology_recovery": topology_recovery,
        "truth": truth,
        "verification_windows": windows,
        "principle": "Infrastructure stability is not a momentary event. It is a continuously reconciled operational state.",
        "summary": truth.get("summary", ""),
    }
    record_reconciliation(entry={"reconciled": reconciled, "truth_score": truth.get("truth_score")})
    result["memory"] = reconciliation_memory_state()
    return result
