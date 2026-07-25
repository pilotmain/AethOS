# SPDX-License-Identifier: Apache-2.0
"""PR proposal engine — dependency modernization (preflight-only, no writes)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.agents.engineering.dependency_reasoning import run_dependency_reasoning
from aethos_core.local_workspace.mutations.foundation import BLOCKED_AUTONOMOUS_ACTIONS


def build_dependency_modernization_proposal(
    repo: Path,
    *,
    user_request: str,
    provider: str = "github",
) -> dict[str, Any]:
    dep = run_dependency_reasoning(repo)
    targets = dep.get("modernization_targets") or []
    blast = dep.get("estimated_blast_radius") or {}
    phases = _phased_migration(targets)
    dep_table = _dependency_table(targets)
    pkg_names = [str(t.get("package") or "") for t in targets[:6] if t.get("package")]
    title = "Modernize Web Dependency Stack" if any(p in pkg_names for p in ("next", "vite", "vitest")) else "Dependency Modernization Proposal"
    why_now = _why_now(dep, targets)
    risk_level = str(dep.get("severity") or "medium").upper()
    business_impact = _business_impact(dep, targets)
    validation = _validation_plan(targets)
    return {
        "ok": True,
        "status": "proposal_only",
        "artifact_type": "engineering_pr_proposal",
        "title": title,
        "objective": "Reduce high-risk dependency vulnerabilities and stale package ranges through phased governed upgrades.",
        "business_impact": business_impact,
        "why_now": why_now,
        "risk_level": risk_level,
        "confidence": "medium" if targets else "low",
        "provider": provider,
        "target": str(repo),
        "user_request": user_request[:500],
        "dependency_findings": {
            "severity": dep.get("severity"),
            "vulnerabilities": dep.get("vulnerabilities") or [],
            "risk_summary": dep.get("risk_summary") or [],
        },
        "dependency_table": dep_table,
        "modernization_targets": targets,
        "compatibility_risks": _compatibility_risks(targets),
        "phased_migration": phases,
        "migration_phases": phases,
        "blast_radius": _blast_radius_detail(blast),
        "impacted_services": blast.get("surfaces") or [],
        "estimated_blast_radius": blast,
        "proposed_changes": [f"Upgrade {t.get('package')} ({t.get('ecosystem')})" for t in targets[:8]],
        "verification_plan": validation,
        "required_validation": validation,
        "rollback_plan": _rollback_strategy(),
        "rollback_strategy": _rollback_strategy(),
        "blocked_actions": sorted(BLOCKED_AUTONOMOUS_ACTIONS),
        "governance": {
            "status": "readonly proposal only",
            "branch_creation": False,
            "push": False,
            "merge": False,
            "execution_enabled": False,
            "mutation_preflight_required": True,
        },
    }


def format_pr_proposal_report(proposal: dict[str, Any]) -> str:
    lines = [
        "# PR Proposal",
        "",
        f"**Objective:** {proposal.get('objective') or 'Dependency modernization'}",
        f"**Business impact:** {proposal.get('business_impact') or proposal.get('why_now') or '—'}",
        f"**Risk level:** {proposal.get('risk_level') or (proposal.get('dependency_findings') or {}).get('severity', 'unknown')}",
        f"**Confidence:** {proposal.get('confidence', 'medium')}",
        "",
        "## Dependency table",
        "| Package | Current | Target | Risk |",
        "|---|---|---|---|",
    ]
    for row in proposal.get("dependency_table") or []:
        lines.append(f"| {row.get('package')} | {row.get('current')} | {row.get('target')} | {row.get('risk')} |")
    if not proposal.get("dependency_table"):
        lines.append("| — | — | — | Run dependency audit |")
    lines.extend(["", "## Blast radius"])
    for item in proposal.get("blast_radius") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Migration phases"])
    for i, phase in enumerate(proposal.get("phased_migration") or proposal.get("migration_phases") or [], 1):
        lines.append(f"{i}. {phase}")
    lines.extend(["", "## Required validation"])
    for step in proposal.get("required_validation") or proposal.get("verification_plan") or []:
        lines.append(f"- {step}")
    lines.extend(
        [
            "",
            "## Rollback strategy",
            proposal.get("rollback_strategy") or proposal.get("rollback_plan") or "Revert branch — no auto-merge.",
            "",
            "## Governance status",
            "**Readonly proposal only.** Mutation preflight required before branch creation.",
            "**Blocked:** branch creation · push · merge · autonomous execution",
        ]
    )
    return "\n".join(lines)


def _why_now(dep: dict[str, Any], targets: list[dict[str, str]]) -> str:
    sev = str(dep.get("severity") or "unknown")
    vulns = dep.get("vulnerabilities") or []
    if vulns:
        return f"Dependency audit severity {sev} with {len(vulns)} vulnerability signal(s) — modernization reduces exploit surface."
    if targets:
        return f"{len(targets)} packages flagged for stale ranges or advisory updates."
    return "Proactive dependency hygiene — no critical vulnerabilities confirmed in scan."


def _phased_migration(targets: list[dict[str, str]]) -> list[str]:
    if not targets:
        return ["No modernization targets identified — run full dependency audit first."]
    dev_tools = [t["package"] for t in targets if t.get("ecosystem") == "npm" and any(x in str(t.get("package", "")).lower() for x in ("eslint", "vitest", "vite", "typescript"))][:4]
    runtime = [t["package"] for t in targets if t["package"] not in dev_tools and t.get("ecosystem") == "npm"][:4]
    framework = [t["package"] for t in targets if t.get("ecosystem") == "npm" and any(x in str(t.get("package", "")).lower() for x in ("next", "react"))][:3]
    python = [t["package"] for t in targets if t.get("ecosystem") == "python"][:4]
    phases: list[str] = []
    if dev_tools:
        phases.append(f"Phase 1 — dev tooling: {', '.join(dev_tools)}")
    if runtime:
        phases.append(f"Phase 2 — runtime deps: {', '.join(runtime)}")
    if framework:
        phases.append(f"Phase 3 — framework alignment: {', '.join(framework)}")
    if python:
        phases.append(f"Phase 4 — Python stack: {', '.join(python)}")
    phases.append("Phase 5 — cleanup: remove unused deps, lockfile refresh, governed verification")
    return phases


def _dependency_table(targets: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for t in targets[:12]:
        reason = str(t.get("reason") or "")
        risk = "high" if "vulnerability" in reason.lower() else "medium" if "stale" in reason.lower() else "low"
        rows.append(
            {
                "package": str(t.get("package") or "—"),
                "current": str(t.get("current") or t.get("installed") or "pinned"),
                "target": str(t.get("target") or "latest compatible"),
                "risk": risk,
            }
        )
    return rows


def _blast_radius_detail(blast: dict[str, Any]) -> list[str]:
    surfaces = blast.get("surfaces") or []
    items = [
        f"Scope: {blast.get('scope') or 'workspace-wide dependency refresh'}",
        f"Apps/services: {', '.join(surfaces) or 'monorepo packages'}",
        "CI: workflow build + test jobs",
        "Builds: npm build, docker compose",
        "Tests: vitest, pytest",
        "Deployment paths: provider build pipelines touching lockfiles",
    ]
    return items


def _validation_plan(targets: list[dict[str, str]]) -> list[str]:
    steps = ["npm build", "vitest", "pytest", "docker compose", "e2e smoke"]
    if any(t.get("ecosystem") == "python" for t in targets):
        steps.insert(2, "pip install -r requirements (readonly check)")
    steps.extend(
        [
            "Run mutation preflight for any write scope",
            "Human approval required before branch/patch/PR",
        ]
    )
    return steps


def _rollback_strategy() -> str:
    return "Revert branch · restore lockfile · redeploy previous artifact — no auto-merge."


def _business_impact(dep: dict[str, Any], targets: list[dict[str, str]]) -> str:
    sev = str(dep.get("severity") or "unknown")
    vulns = len(dep.get("vulnerabilities") or [])
    if vulns:
        return f"Reduces {vuln_count_label(vulns)} vulnerability exposure (audit severity {sev}) and stabilizes build/deploy pipelines."
    if targets:
        return f"Modernizes {len(targets)} stale dependency target(s) — lowers CI flake risk and security drift."
    return "Proactive dependency hygiene — maintains supply-chain resilience."


def vuln_count_label(count: int) -> str:
    return f"{count} known"


def _compatibility_risks(targets: list[dict[str, str]]) -> list[str]:
    risks: list[str] = []
    npm = sum(1 for t in targets if t.get("ecosystem") == "npm")
    py = sum(1 for t in targets if t.get("ecosystem") == "python")
    if npm and py:
        risks.append("Cross-stack upgrade — coordinate frontend and backend release timing.")
    if npm >= 5:
        risks.append("Large npm surface — expect transitive dependency churn.")
    if py >= 5:
        risks.append("Python dependency refresh may affect runtime and test harness.")
    if not risks:
        risks.append("Low compatibility risk for isolated package bumps.")
    return risks
