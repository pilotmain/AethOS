# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.1 — Agent evidence depth + real substrate binding."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.agents.engineering.risk_scoring import classify_severity
from aethos_core.agents.providers.deployment_correlation import correlate_deployments
from aethos_core.agents.providers.runtime_failure_analysis import analyze_runtime_failure
from aethos_core.agents.runtime.coordination import run_agent_coordination
from aethos_core.agents.runtime.evidence_merge import hydrate_evidence_bundle, merge_agent_evidence
from aethos_core.agents.runtime.planner import plan_task


@pytest.fixture
def agent_env(monkeypatch, tmp_path):
    artifacts = tmp_path / "agent_artifacts"
    registry = tmp_path / "lw_registry"
    lw_artifacts = tmp_path / "lw_artifacts"
    root = tmp_path / "repo"
    root.mkdir()
    (root / "aethos_core").mkdir()
    (root / "web" / "components").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    monkeypatch.setenv("AGENT_ARTIFACTS_DIR", str(artifacts))
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", str(registry))
    monkeypatch.setenv("LOCAL_WORKSPACE_ARTIFACTS_DIR", str(lw_artifacts))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_deployment_failure_plan_includes_engineering_and_analyst():
    plan = plan_task("analyze why the latest Railway deployment failed")
    ids = [a.agent_id for a in plan.assignments]
    assert "provider_ops" in ids
    assert "web_evidence" in ids
    assert "code_intelligence" in ids
    assert "operations_analyst" in ids


def test_correlate_deployments_marks_regression():
    failed = {"id": "dep_123", "state": "CRASHED", "commit": "abc"}
    healthy = {"id": "dep_122", "state": "ready", "commit": "def"}
    out = correlate_deployments(failed=failed, healthy=healthy)
    assert out["regression_detected"] is True
    assert out["failed_deployment"]["id"] == "dep_123"
    assert out["last_healthy_deployment"]["id"] == "dep_122"


def test_runtime_failure_analysis_confidence_from_substrate():
    analysis = analyze_runtime_failure(
        provider_evidence={
            "correlation": {
                "failed_deployment": {"id": "dep_123", "state": "CRASHED", "error_message": "Module not found: redis"},
            },
            "log_text": "Error: Module not found: redis",
        },
        engineering_evidence={"recent_commits": ["abc123 fix deps"], "hot_files": [{"path": "requirements.txt"}]},
        browser_evidence={"health_badge": "failed", "metadata": {"console_errors": ["500"]}},
        goal="analyze why railway deployment failed",
    )
    assert analysis["confidence"] in ("medium", "high")
    hypotheses = " ".join((analysis.get("conclusions") or {}).get("hypotheses") or [])
    assert "redis" in hypotheses.lower() or "module" in hypotheses.lower() or "dependency" in hypotheses.lower()
    assert "severity" not in analysis or analysis.get("report_mode") == "deployment_failure"


def test_severity_scoring_critical_on_production():
    sev = classify_severity(
        signals=[
            {"kind": "deployment_failed", "weight": 2, "detail": "crash"},
            {"kind": "production_impact", "weight": 2, "detail": "prod down"},
        ]
    )
    assert sev["severity"] in ("HIGH", "CRITICAL")


def test_coordination_produces_deep_artifacts(agent_env):
    with patch("aethos_core.agents.providers.railway_reasoning.run_railway_diagnostics") as mock_rail:
        mock_rail.return_value = {
            "ok": True,
            "report": "# Railway diagnostics\n\nDeployment dep_123 CRASHED",
            "correlation": {"failed_deployment": {"id": "dep_123", "state": "CRASHED"}},
            "log_text": "Module not found: redis",
        }
        with patch("aethos_core.browser.runtime.browser_runtime.run_deployment_evidence_capture") as mock_browser:
            mock_browser.return_value = {
                "ok": True,
                "summary": "Browser metadata captured",
                "artifacts": [{"artifact_id": "bart-test1", "artifact_type": "deployment_metadata_only"}],
                "metadata_only": True,
            }
            result = run_agent_coordination(
                goal="analyze why the latest Railway deployment failed",
                session_id="e1",
                workspace_hint=str(agent_env),
            )
    assert result["ok"] is True
    merged = result.get("merged") or {}
    assert merged.get("evidence_bundle_count", 0) >= 0
    assert merged.get("confidence")
    assert "Confirmed findings" in (result.get("report") or "") or "Agent timeline" in (result.get("report") or "")
    types = {r.get("agent_id") for r in result.get("results") or []}
    assert "operations_analyst" in types
    assert result.get("graph", {}).get("nodes")


def test_merge_includes_substrate_and_confidence(agent_env):
    results = [
        {
            "agent_id": "provider_ops",
            "status": "completed",
            "summary": "Railway diagnostics",
            "artifact_id": "aart-prov1",
            "evidence_ids": [],
            "substrate_invoked": ["provider_readonly"],
            "duration_ms": 120,
            "finished_at": 1.0,
        },
        {
            "agent_id": "operations_analyst",
            "status": "completed",
            "summary": "Analyst",
            "artifact_id": "aart-an1",
            "analysis": {"severity": "HIGH", "probable_root_cause": "dependency mismatch"},
            "duration_ms": 50,
            "finished_at": 2.0,
        },
    ]
    merged = merge_agent_evidence(
        plan_id="plan-test",
        goal="analyze why the latest Railway deployment failed",
        agent_results=results,
    )
    assert merged["severity"] == merged["severity_authority"]["severity"]
    assert merged.get("report_mode") == "deployment_failure"


def test_hydrate_evidence_empty_safe():
    assert hydrate_evidence_bundle([]) == []
