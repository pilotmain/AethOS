# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.2 — Report quality + evidence grounding."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.agents.providers.runtime_failure_analysis import analyze_runtime_failure
from aethos_core.agents.runtime.evidence_merge import merge_agent_evidence
from aethos_core.agents.runtime.evidence_summarizer import summarize_evidence_record
from aethos_core.agents.runtime.report_mode import infer_report_mode
from aethos_core.agents.runtime.report_templates import render_deployment_failure_report, render_pr_proposal_report
from aethos_core.agents.runtime.severity_authority import resolve_final_severity
from aethos_core.agents.runtime.coordination import run_agent_coordination


def test_infer_report_modes():
    assert infer_report_mode("analyze why the latest Railway deployment failed") == "deployment_failure"
    assert infer_report_mode("prepare a PR proposal for dependency modernization") == "pr_proposal"
    assert infer_report_mode("analyze architecture risks in AethOS") == "architecture_risk"


def test_failure_analysis_does_not_claim_hot_file_as_root_cause():
    analysis = analyze_runtime_failure(
        provider_evidence={"ok": True, "correlation": {"failed_deployment": {}}},
        engineering_evidence={"hot_files": [{"path": "aethos_core/agents/runtime/delegation.py"}]},
        browser_evidence=None,
        goal="analyze why railway deployment failed",
    )
    conc = analysis.get("conclusions") or {}
    signals = " ".join(conc.get("signals") or [])
    hypotheses = " ".join(conc.get("hypotheses") or [])
    assert "delegation.py" in signals
    assert "root cause" not in signals.lower()
    assert "Hot file" not in hypotheses
    assert any("No failed" in c or "completed" in c.lower() for c in conc.get("confirmed") or [])


def test_severity_authority_caps_without_confirmed_failure():
    sev = resolve_final_severity(
        agent_results=[{"agent_id": "code_intelligence", "analysis": {"severity": "CRITICAL"}}],
        report_mode="deployment_failure",
        confidence={"level": "low"},
        provider_payload={"ok": True, "failed_deployment_found": False},
    )
    assert sev["severity"] in ("LOW", "MEDIUM")
    assert any("No confirmed" in r or "credential" in r.lower() for r in sev.get("severity_reason") or [])


def test_evidence_summarizer_readable():
    item = summarize_evidence_record(
        {
            "artifact_id": "lart-abc123",
            "source": "local_workspace",
            "record": {
                "artifact_type": "dependency_audit",
                "summary": "Dependency audit — severity high",
                "payload": {"severity": "high", "vulnerabilities": [{}, {}]},
            },
        }
    )
    assert "lart-abc123" in item["display"]
    assert "Dependency" in item["summary"]


def test_deployment_report_template_sections():
    merged = {
        "goal": "analyze why railway deployment failed",
        "status": "completed",
        "severity": "LOW",
        "severity_authority": {"severity": "LOW", "severity_reason": ["No confirmed failed deployment"]},
        "confidence": {"level": "low", "reasons": []},
        "timeline": [{"agent_id": "provider_ops", "task": "diagnostics", "status": "completed"}],
        "conclusions": {
            "confirmed": ["No failed Railway deployment found."],
            "hypotheses": [],
            "signals": ["Recent commit: abc"],
            "gaps": ["Need deployment logs"],
        },
        "evidence_summaries": [{"display": "`lart-x` — Dependency audit: severity high"}],
        "next_steps": ['Run: "check railway logs for service"'],
    }
    report = render_deployment_failure_report(merged)
    assert "Confirmed findings" in report
    assert "Likely hypothesis" in report
    assert "Evidence gaps" in report
    assert "Probable root cause" not in report


def test_pr_proposal_report_has_proposal_sections():
    merged = {
        "goal": "prepare a PR proposal",
        "pr_proposal": {
            "title": "Modernize Web Dependency Stack",
            "objective": "Reduce vulnerabilities",
            "why_now": "Audit flagged issues",
            "modernization_targets": [{"package": "next", "ecosystem": "npm", "reason": "stale"}],
            "phased_migration": ["Phase 1 — patch"],
            "verification_plan": ["Run tests"],
            "rollback_plan": "Revert branch",
        },
        "severity_authority": {"severity": "MEDIUM"},
    }
    report = render_pr_proposal_report(merged)
    assert "PR Proposal" in report
    assert "Dependency targets" in report
    assert "Readonly proposal only" in report
    assert "root cause" not in report.lower()


@pytest.fixture
def agent_env(monkeypatch, tmp_path):
    artifacts = tmp_path / "agent_artifacts"
    registry = tmp_path / "lw_registry"
    lw_artifacts = tmp_path / "lw_artifacts"
    root = tmp_path / "repo"
    root.mkdir()
    (root / "aethos_core").mkdir()
    (root / "web" / "components").mkdir(parents=True)
    monkeypatch.setenv("AGENT_ARTIFACTS_DIR", str(artifacts))
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", str(registry))
    monkeypatch.setenv("LOCAL_WORKSPACE_ARTIFACTS_DIR", str(lw_artifacts))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_coordination_report_mode_architecture(agent_env):
    result = run_agent_coordination(goal="analyze architecture risks in AethOS", session_id="e2", workspace_hint=str(agent_env))
    report = result.get("report") or ""
    assert result["merged"].get("report_mode") == "architecture_risk"
    assert "Architecture risk" in report
    assert "Probable root cause" not in report


def test_merge_severity_consistent(agent_env):
    merged = merge_agent_evidence(
        plan_id="p1",
        goal="analyze why railway deployment failed",
        agent_results=[
            {
                "agent_id": "operations_analyst",
                "status": "completed",
                "analysis": {"severity": "LOW", "conclusions": {"confirmed": [], "hypotheses": [], "signals": [], "gaps": []}},
            }
        ],
        report_mode="deployment_failure",
    )
    assert merged["severity"] == merged["severity_authority"]["severity"]
