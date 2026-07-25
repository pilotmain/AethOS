# SPDX-License-Identifier: Apache-2.0
"""CI / workflow reasoning — readonly pipeline analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.local_workspace.analysis.diagnostics import analyze_diagnostics, format_workflow_report


def run_ci_reasoning(repo: Path) -> dict[str, Any]:
    diagnostics = analyze_diagnostics(repo)
    workflows = diagnostics.get("workflows") or []
    failures = _cluster_failures(workflows)
    analysis = {
        "ok": True,
        "repo": str(repo),
        "diagnostics": diagnostics,
        "workflow_count": len(workflows),
        "failure_clusters": failures,
        "risk_signals": _ci_signals(workflows, failures),
    }
    return analysis


def format_ci_reasoning_report(analysis: dict[str, Any]) -> str:
    diag = analysis.get("diagnostics") or {}
    base = format_workflow_report(diag)
    extra: list[str] = ["", "## Failure clustering"]
    clusters = analysis.get("failure_clusters") or []
    if not clusters:
        extra.append("- No workflow failure patterns detected in static scan.")
    else:
        for c in clusters:
            extra.append(f"- **{c.get('pattern')}** — {c.get('detail')}")
    return base + "\n".join(extra)


def _cluster_failures(workflows: list[dict[str, Any]]) -> list[dict[str, str]]:
    clusters: list[dict[str, str]] = []
    if not workflows:
        clusters.append({"pattern": "missing_ci", "detail": "No GitHub Actions workflows detected."})
        return clusters
    names = [str(w.get("name") or w.get("path") or "") for w in workflows]
    if any("test" in n.lower() for n in names):
        clusters.append({"pattern": "test_pipeline", "detail": "Test workflow present — verify flaky test history separately."})
    if any("deploy" in n.lower() for n in names):
        clusters.append({"pattern": "deploy_pipeline", "detail": "Deploy workflow present — correlate with provider deployment failures."})
    return clusters


def _ci_signals(workflows: list[dict[str, Any]], failures: list[dict[str, str]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if any(f.get("pattern") == "missing_ci" for f in failures):
        signals.append({"kind": "missing_verification", "weight": 1, "detail": "no CI workflows detected"})
    return signals
