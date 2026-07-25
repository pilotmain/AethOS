# SPDX-License-Identifier: Apache-2.0
"""Infrastructure truth aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_truth.cluster_truth import assess_cluster_truth
from aethos_core.infrastructure_truth.infrastructure_truth_score import score_infrastructure_truth
from aethos_core.infrastructure_truth.operational_truth_decay import assess_infrastructure_decay
from aethos_core.infrastructure_truth.pod_truth_runtime import assess_pod_truth
from aethos_core.infrastructure_truth.service_truth import assess_service_truth
from aethos_core.infrastructure_truth.topology_truth import assess_topology_truth


def assess_infrastructure_truth() -> dict[str, Any]:
    cluster = assess_cluster_truth()
    topology = assess_topology_truth()
    pods = assess_pod_truth()
    services = assess_service_truth()
    score = score_infrastructure_truth(cluster=cluster, topology=topology, pods=pods)
    decay = assess_infrastructure_decay()
    return {
        "ok": True,
        "cluster": cluster,
        "topology": topology,
        "pods": pods,
        "services": services,
        "score": score,
        "decay": decay,
        "summary": cluster.get("summary", "Infrastructure truth assessing."),
    }
