# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.3 — Operational intelligence depth."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.agents.engineering.architecture_intelligence import run_architecture_intelligence
from aethos_core.agents.engineering.pr_proposal_engine import build_dependency_modernization_proposal, format_pr_proposal_report
from aethos_core.agents.memory.operational_patterns import (
    clear_operational_patterns_for_tests,
    get_recurring_patterns,
    record_operational_event,
)
from aethos_core.agents.providers.deployment_intelligence import build_deployment_intelligence, format_deployment_intelligence_report
from aethos_core.agents.runtime.confidence_engine import score_merged_confidence
from aethos_core.agents.runtime.evidence_correlation_engine import correlate_operational_evidence
from aethos_core.agents.runtime.evidence_merge import merge_agent_evidence
from aethos_core.agents.runtime.report_templates import render_deployment_failure_report, render_pr_proposal_report
from aethos_core.agents.runtime.coordination import build_coordination_graph, run_agent_coordination


@pytest.fixture(autouse=True)
def _clean_patterns():
    clear_operational_patterns_for_tests()
    yield
    clear_operational_patterns_for_tests()


def test_deployment_intelligence_unavailable_credentials():
    with patch("aethos_core.providers.railway.auth.RailwayAuthAdapter") as mock_auth:
        mock_auth.return_value.resolve_best_auth_method.return_value = {}
        intel = build_deployment_intelligence("analyze why railway deployment failed")
    assert intel.get("credential_state") == "unavailable"
    report = format_deployment_intelligence_report(intel)
    assert "Deployment Intelligence" in report


def test_evidence_correlation_temporal_and_operational():
    corr = correlate_operational_evidence(
        provider={"correlation": {"failed_deployment": {"id": "dep_1", "state": "failed", "commit": "abc123"}}},
        engineering={"recent_commits": ["abc123 fix deploy"], "hot_files": [{"path": "Dockerfile"}]},
        browser={"target_unresolved": True},
        deployment_intel={"latest_deployment": {"state": "success"}, "restart_count": 0},
        report_mode="deployment_failure",
    )
    assert corr["correlation_count"] >= 2
    assert corr["graph_edges"]
    signals = " ".join(corr["conclusions"].get("signals") or [])
    assert "abc123" in signals or "Browser" in signals


def test_confidence_engine_evidence_quality():
    conf = score_merged_confidence(
        bundle=[{"record": {"created_at": 9999999999}}],
        agent_results=[
            {"agent_id": "provider_ops", "status": "completed", "substrate_payload": {"logs_available": True}},
            {"agent_id": "web_evidence", "substrate_payload": {"target_unresolved": True}},
        ],
        correlation={"correlation_count": 2},
        deployment_intel={"telemetry_quality": "high", "logs_available": True},
        conflicts=[],
    )
    assert conf["level"] in ("medium", "high")
    assert conf["reasons"]
    assert any("browser" in g.lower() for g in conf.get("gaps") or [])


def test_pr_proposal_rfc_structure(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text('{"name":"demo","dependencies":{"lodash":"4.17.20"}}')
    with patch("aethos_core.agents.engineering.pr_proposal_engine.run_dependency_reasoning") as mock_dep:
        mock_dep.return_value = {
            "severity": "high",
            "vulnerabilities": [{"package": "lodash"}],
            "modernization_targets": [{"package": "lodash", "ecosystem": "npm", "reason": "vulnerability advisory"}],
            "estimated_blast_radius": {"scope": "frontend", "surfaces": ["web"]},
        }
        proposal = build_dependency_modernization_proposal(repo, user_request="prepare PR proposal")
    assert proposal.get("dependency_table")
    assert proposal.get("blast_radius")
    assert proposal.get("rollback_strategy")
    assert proposal["governance"]["mutation_preflight_required"] is True
    report = format_pr_proposal_report(proposal)
    assert "Dependency table" in report
    assert "Rollback strategy" in report


def test_architecture_intelligence_health_score(tmp_path: Path):
    repo = tmp_path / "aethos"
    (repo / "aethos_core").mkdir(parents=True)
    with patch("aethos_core.agents.engineering.architecture_intelligence.run_architecture_reasoning") as mock_arch:
        mock_arch.return_value = {
            "layers": [
                {"layer": "Orchestration brain", "present": True},
                {"layer": "Job runtime", "present": True},
                {"layer": "Browser evidence", "present": True},
            ],
            "semantic_modules": [{"label": "Governed mutation execution lifecycle"}],
            "operational_flows": ["browser capture"],
            "bottlenecks": [],
            "scalability_observations": ["cache scans"],
        }
        intel = run_architecture_intelligence(repo)
    assert intel["architecture_health"]["architecture_health"] >= 40
    assert intel.get("top_risks")


def test_operational_patterns_recurring():
    record_operational_event(category="deployment_instability", detail="restart", provider="railway")
    record_operational_event(category="deployment_instability", detail="restart again", provider="railway")
    patterns = get_recurring_patterns()
    assert any("deployment instability" in p for p in patterns)


def test_merge_includes_correlation_and_deployment_intel():
    merged = merge_agent_evidence(
        plan_id="plan-test",
        goal="analyze why the latest Railway deployment failed",
        agent_results=[
            {
                "agent_id": "provider_ops",
                "status": "completed",
                "artifact_id": "a1",
                "deployment_intelligence": {
                    "latest_deployment": {"id": "dep_1", "state": "SUCCESS"},
                    "telemetry_quality": "medium",
                },
                "substrate_payload": {"ok": True, "failed_deployment_found": False},
            },
            {
                "agent_id": "operations_analyst",
                "status": "completed",
                "analysis": {
                    "conclusions": {"confirmed": ["No failed deployment"], "hypotheses": [], "signals": [], "gaps": []},
                    "correlation": {"correlation_count": 1, "graph_edges": [{"from": "git", "to": "deployment", "label": "x"}]},
                },
            },
        ],
        report_mode="deployment_failure",
    )
    assert merged.get("correlation")
    assert merged.get("deployment_intelligence")
    assert merged["confidence"].get("level")
    report = render_deployment_failure_report(merged)
    assert "Correlations" in report or "Confidence" in report


def test_coordination_graph_replay():
    from aethos_core.agents.runtime.planner import AgentAssignment, TaskPlan

    plan = TaskPlan(
        plan_id="p1",
        goal="test",
        assignments=[AgentAssignment(agent_id="provider_ops", task="diag", action="railway_diagnostics")],
    )
    graph = build_coordination_graph(
        plan,
        [{"agent_id": "provider_ops", "status": "completed", "evidence_ids": []}],
        {"correlation": {"correlation_count": 1}, "confidence": {"level": "medium"}, "evidence_bundle_count": 2, "report_mode": "deployment_failure"},
    )
    assert graph.get("replay")
    assert any(e.get("kind") == "orchestration" for e in graph.get("edges") or [])


def test_coordination_end_to_end_mocked():
    with patch("aethos_core.agents.runtime.delegation.delegate_agent_step") as mock_delegate:
        mock_delegate.side_effect = [
            {
                "agent_id": "provider_ops",
                "status": "completed",
                "artifact_id": "a1",
                "evidence_ids": [],
                "substrate_payload": {"ok": True},
                "deployment_intelligence": {"provider": "railway", "telemetry_quality": "medium"},
            },
            {
                "agent_id": "operations_analyst",
                "status": "completed",
                "artifact_id": "a2",
                "evidence_ids": [],
                "analysis": {"conclusions": {"confirmed": ["done"], "hypotheses": [], "signals": [], "gaps": []}},
            },
        ]
        result = run_agent_coordination(goal="analyze why the latest Railway deployment failed")
    assert result.get("ok")
    assert result.get("graph", {}).get("replay")
