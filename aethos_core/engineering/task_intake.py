# SPDX-License-Identifier: Apache-2.0
"""Engineering task intake — issues, workflows, incidents → governed tasks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from uuid import uuid4

_WORKFLOW_FIX_RX = re.compile(
    r"\bfix\b.*\b(?:github\s+)?workflow\b|\bworkflow\s+rerun\b|\bworkflow\s+fail",
    re.I,
)
_RAILWAY_FIX_RX = re.compile(r"\brailway\b.*\b(?:deployment|diagnostic)\b|\bdeployment\s+diagnostic", re.I)
_MODERNIZE_RX = re.compile(r"\bmoderni(?:z|s)e\b.*\b(?:dependenc|next\.js|npm)\b", re.I)


def intake_engineering_task(user_request: str, *, repo: Path | None = None) -> dict[str, Any]:
    """Convert natural language / issue text into governed engineering task."""
    text = (user_request or "").strip()
    task_id = f"etask-{uuid4().hex[:10]}"
    kind = _classify_kind(text)
    affected = _default_files(kind, repo)
    return {
        "task_id": task_id,
        "kind": kind,
        "title": _title_for_kind(kind, text),
        "problem_summary": _problem_summary(kind, text),
        "likely_cause": _likely_cause(kind),
        "affected_files": affected,
        "test_scope": _test_scope(kind),
        "risk_tier": _risk_tier(kind),
        "proposed_fix": _proposed_fix(kind),
        "labels": _labels(kind),
        "source": "user_request",
        "raw_request": text[:500],
    }


def parse_github_issue(issue: dict[str, Any], *, repo: Path | None = None) -> dict[str, Any]:
    body = f"{issue.get('title') or ''}\n{issue.get('body') or ''}"
    task = intake_engineering_task(body, repo=repo)
    task["source"] = "github_issue"
    task["issue_number"] = issue.get("number")
    task["issue_url"] = issue.get("html_url")
    return task


def _classify_kind(text: str) -> str:
    if _WORKFLOW_FIX_RX.search(text):
        return "workflow_fix"
    if _RAILWAY_FIX_RX.search(text):
        return "deployment_diagnostics"
    if _MODERNIZE_RX.search(text):
        return "dependency_modernization"
    if "patch" in text.lower():
        return "governed_patch"
    return "general_engineering"


def _title_for_kind(kind: str, text: str) -> str:
    titles = {
        "workflow_fix": "Fix GitHub workflow rerun resolution",
        "deployment_diagnostics": "Improve Railway deployment diagnostics",
        "dependency_modernization": "Dependency modernization plan",
        "governed_patch": "Governed patch proposal",
    }
    return titles.get(kind, text[:80] or "Engineering task")


def _problem_summary(kind: str, text: str) -> str:
    if kind == "workflow_fix":
        return "GitHub workflow rerun may fail due to readonly/mutation resolver mismatch."
    if kind == "deployment_diagnostics":
        return "Deployment diagnostics need deeper provider telemetry correlation."
    if kind == "dependency_modernization":
        return "Dependency stack requires governed modernization with validation."
    return text[:240] or "Engineering task requires scoped analysis and patch plan."


def _likely_cause(kind: str) -> str:
    causes = {
        "workflow_fix": "Workflow discovery path differs between readonly substrate and mutation preflight.",
        "deployment_diagnostics": "Missing deployment timeline or URL resolution in provider evidence path.",
        "dependency_modernization": "Stale dependency ranges or advisory vulnerabilities in manifest.",
    }
    return causes.get(kind, "Root cause requires correlated readonly evidence — not confirmed until validation.")


def _default_files(kind: str, repo: Path | None) -> list[str]:
    mapping = {
        "workflow_fix": [
            "aethos_core/providers/github/shared/workflow_resolution.py",
            "aethos_core/providers/github/operations/mutations_api.py",
            "aethos_core/operations/mutations/preflight.py",
        ],
        "deployment_diagnostics": [
            "aethos_core/agents/providers/deployment_intelligence.py",
            "aethos_core/agents/providers/railway_reasoning.py",
        ],
        "dependency_modernization": ["package.json", "web/package.json"],
    }
    files = list(mapping.get(kind, []))
    if repo:
        files = [f for f in files if (repo / f).is_file()]
    return files[:12]


def _test_scope(kind: str) -> list[str]:
    scopes = {
        "workflow_fix": ["tests/test_github_workflow*.py", "tests/test_phase_98e*.py"],
        "deployment_diagnostics": ["tests/test_phase_98e3_operational_intelligence.py"],
        "dependency_modernization": ["tests/test_phase_98e2_report_quality.py"],
    }
    return scopes.get(kind, ["tests/"])


def _risk_tier(kind: str) -> str:
    return "E2_branch_diff" if kind in ("workflow_fix", "deployment_diagnostics") else "E1_proposal_only"


def _proposed_fix(kind: str) -> str:
    fixes = {
        "workflow_fix": "Align workflow rerun resolution between readonly discovery and mutation params.",
        "deployment_diagnostics": "Extend deployment intelligence with timeline + correlated CI evidence.",
        "dependency_modernization": "Phased dependency upgrades with governed validation and PR draft.",
    }
    return fixes.get(kind, "Scoped patch with validation and rollback snapshot.")


def _labels(kind: str) -> list[str]:
    return {
        "workflow_fix": ["ci", "github", "engineering"],
        "deployment_diagnostics": ["railway", "deployment", "engineering"],
        "dependency_modernization": ["dependencies", "engineering"],
    }.get(kind, ["engineering"])
