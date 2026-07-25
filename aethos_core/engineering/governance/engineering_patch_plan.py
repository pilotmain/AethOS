# SPDX-License-Identifier: Apache-2.0
"""Engineering patch plan — scoped change proposal."""

from __future__ import annotations

from typing import Any


def build_patch_plan(
    *,
    task: dict[str, Any],
    affected_files: list[str],
    blast_radius: dict[str, Any] | None = None,
    validation_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Structured patch plan — readonly until approval."""
    files = affected_files[:12]
    return {
        "ok": True,
        "status": "patch_plan",
        "task_id": task.get("task_id"),
        "title": task.get("title") or "Engineering patch plan",
        "problem_summary": task.get("problem_summary"),
        "likely_cause": task.get("likely_cause"),
        "affected_files": files,
        "patch_summary": task.get("proposed_fix") or "Targeted fix scoped to affected files.",
        "risk_areas": _risk_areas(files, blast_radius),
        "validation_steps": validation_steps or _default_validation(files),
        "rollback_strategy": "Revert branch · restore rollback snapshot · discard sandbox diff.",
        "approval_status": "pending",
        "execution_enabled": False,
        "blast_radius": blast_radius or {},
    }


def format_patch_plan_report(plan: dict[str, Any]) -> str:
    lines = [
        "# Engineering patch plan (approval required)",
        "",
        f"**Title:** {plan.get('title')}",
        f"**Status:** {plan.get('approval_status', 'pending')}",
        f"**Problem:** {plan.get('problem_summary') or '—'}",
        f"**Likely cause:** {plan.get('likely_cause') or '—'}",
        "",
        "## Files affected",
    ]
    for f in plan.get("affected_files") or []:
        lines.append(f"- `{f}`")
    lines.extend(["", "## Patch summary", plan.get("patch_summary") or "—", "", "## Validation steps"])
    for step in plan.get("validation_steps") or []:
        lines.append(f"- {step}")
    lines.extend(["", "## Rollback strategy", plan.get("rollback_strategy") or "Revert branch."])
    lines.extend(["", "**No writes performed** until engineering preflight is approved."])
    return "\n".join(lines)


def _risk_areas(files: list[str], blast: dict[str, Any] | None) -> list[str]:
    risks: list[str] = []
    if any("workflow" in f for f in files):
        risks.append("CI/workflow path — validate workflow syntax and rerun tests.")
    if any(f.endswith(".py") for f in files):
        risks.append("Python runtime — run pytest scoped to affected modules.")
    if any("package.json" in f or f.endswith(".lock") for f in files):
        risks.append("Dependency surface — run build + lockfile validation.")
    if blast and blast.get("surfaces"):
        risks.append(f"Blast radius: {', '.join(blast['surfaces'][:4])}")
    if not risks:
        risks.append("Low — scoped file edits with bounded validation.")
    return risks


def _default_validation(files: list[str]) -> list[str]:
    steps = ["pytest (scoped)", "lint changed files"]
    if any(".github" in f for f in files):
        steps.insert(0, "workflow syntax validation")
    if any(f.endswith((".ts", ".tsx", ".js")) for f in files):
        steps.append("vitest / npm build")
    return steps
