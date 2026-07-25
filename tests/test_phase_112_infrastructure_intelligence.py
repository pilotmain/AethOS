# SPDX-License-Identifier: Apache-2.0
"""Phase 11.2 — Infrastructure runtime intelligence tests."""

from __future__ import annotations

from aethos_core.infrastructure.docker.restart_reconciliation import reconcile_container_restart
from aethos_core.infrastructure.docker.runtime import analyze_docker_runtime
from aethos_core.infrastructure.kubernetes.runtime import verify_kubernetes_rollout
from aethos_core.infrastructure_confidence.runtime import assess_infrastructure_confidence
from aethos_core.infrastructure_harness.scenarios import list_infrastructure_scenarios
from aethos_core.infrastructure_intelligence.runtime import assess_infrastructure_state
from aethos_core.infrastructure_reconciliation.runtime import reconcile_infrastructure
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.runtime_supervision.runtime import observe_supervision_state
from aethos_core.topology.runtime import build_topology_intelligence


def test_docker_runtime_analysis():
    result = analyze_docker_runtime()
    assert result["ok"] is True
    assert result["substrate"] == "docker"
    assert "Operational container analysis indicates" in result["summary"]
    assert "api runtime healthy" in result["summary"].lower()
    assert "Extended monitoring" in result["summary"]
    assert result["capabilities"]["container_health"] in ("stable", "beta")


def test_kubernetes_rollout_verification():
    result = verify_kubernetes_rollout()
    assert result["verified"] is True
    assert result["maturity"] == "stable"
    assert "Rollout verification confirmed" in result["summary"]
    assert "readiness probes recovered" in result["summary"].lower()
    assert "Extended observation" in result["summary"]


def test_topology_intelligence():
    result = build_topology_intelligence()
    assert result["ok"] is True
    assert result["graph"]["node_count"] >= 3
    assert "relationship awareness" in result["principle"].lower()


def test_runtime_supervision_recovery_narrative():
    snapshot = {
        "containers": [{"name": "api", "status": "healthy", "restart_count": 0}],
    }
    result = observe_supervision_state(runtime_snapshot=snapshot)
    assert result["ok"] is True
    assert "runtime verification indicates" in result["summary"].lower()


def test_container_restart_reconciliation():
    result = reconcile_container_restart(
        container_name="api",
        before={"status": "recovering"},
        after={"status": "healthy", "restart_count": 1},
    )
    assert result["verified"] is True
    assert len(result["checks"]) >= 2


def test_infrastructure_reconciliation():
    result = reconcile_infrastructure()
    assert result["ok"] is True
    assert "continuously reconciled" in result["principle"].lower()
    assert "docker" in result
    assert "kubernetes" in result


def test_infrastructure_confidence_narrative():
    result = assess_infrastructure_confidence()
    assert result["ok"] is True
    assert "System healthy" not in result["narrative"]
    assert "monitor" in result["narrative"].lower() or "stable" in result["narrative"].lower()


def test_infrastructure_harness_scenarios():
    scenarios = list_infrastructure_scenarios()
    assert len(scenarios) == 8
    assert any(s["id"] == "pod_restart" for s in scenarios)
    assert any(s["id"] == "namespace_drift" for s in scenarios)


def test_infrastructure_state_aggregate():
    state = assess_infrastructure_state()
    assert state["phase"] == "11.2"
    assert state["docker"]["substrate"] == "docker"
    assert state["kubernetes"]["substrate"] == "kubernetes"


def test_capability_matrix_infrastructure_baselines():
    matrix = build_capability_truth_matrix()
    docker_cap = next((r for r in matrix if r.get("id") == "docker_container_intelligence"), None)
    k8s_cap = next((r for r in matrix if r.get("id") == "kubernetes_runtime_intelligence"), None)
    assert docker_cap is not None
    assert k8s_cap is not None
    assert docker_cap["verification_coverage_pct"] >= 80
    assert k8s_cap["verification_coverage_pct"] >= 84
    assert k8s_cap["maturity"] in ("stable", "beta", "production-ready")
