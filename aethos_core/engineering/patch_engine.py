# SPDX-License-Identifier: Apache-2.0
"""Governed patch engine — scoped diffs and blast radius."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.engineering.diff_intelligence import analyze_patch_diffs
from aethos_core.engineering.governance.engineering_patch_plan import build_patch_plan
from aethos_core.engineering.governance.engineering_scope import classify_engineering_risk, validate_scope
from aethos_core.engineering.patch_runtime.patch_generator import generate_governed_patches


def generate_patch_proposal(
    repo: Path,
    *,
    user_request: str,
    task: dict[str, Any] | None = None,
    target_files: list[str] | None = None,
) -> dict[str, Any]:
    """Generate governed patch proposal — no repo writes."""
    task = task or {}
    files = target_files or task.get("affected_files") or _infer_files(repo, user_request, task)
    scope = validate_scope(allowed_files=files, requested_files=files)
    blast = _estimate_blast_radius(repo, files)
    tier = classify_engineering_risk(
        operation="patch_plan",
        files_count=len(files),
        production_impact=bool(blast.get("production_impact")),
    )
    generated = generate_governed_patches(repo, user_request=user_request, task=task, target_files=files)
    diffs = generated.get("unified_diffs") or []
    diff_intel = analyze_patch_diffs(unified_diffs=diffs, blast_radius=blast, task=task)
    plan = build_patch_plan(task=task, affected_files=files, blast_radius=blast)
    return {
        "ok": scope.get("scope_valid", True) and generated.get("ok", False),
        "risk_tier": tier.value,
        "files_affected": files,
        "files_patched": generated.get("files_patched") or [],
        "patch_summary": plan.get("patch_summary"),
        "risk_areas": plan.get("risk_areas"),
        "validation_steps": plan.get("validation_steps"),
        "rollback_strategy": plan.get("rollback_strategy"),
        "approval_status": "pending",
        "blast_radius": blast,
        "scope": scope,
        "unified_diffs": diffs,
        "patches": generated.get("patches") or [],
        "patch_plan": plan,
        "diff_intelligence": diff_intel,
        "execution_enabled": False,
    }


def _infer_files(repo: Path, user_request: str, task: dict[str, Any]) -> list[str]:
    lower = user_request.lower()
    files: list[str] = list(task.get("affected_files") or [])
    hints = {
        "workflow rerun": [
            "aethos_core/providers/github/shared/workflow_resolution.py",
            "aethos_core/providers/github/operations/mutations_api.py",
            "aethos_core/operations/mutations/preflight.py",
        ],
        "railway deployment": [
            "aethos_core/agents/providers/railway_reasoning.py",
            "aethos_core/agents/providers/deployment_intelligence.py",
        ],
        "dependency": ["package.json", "web/package.json"],
    }
    for key, paths in hints.items():
        if key in lower:
            for p in paths:
                if (repo / p).is_file() and p not in files:
                    files.append(p)
    if not files:
        from aethos_core.agents.engineering.git_hotspots import run_git_hotspot_analysis

        hot = run_git_hotspot_analysis(repo)
        for row in (hot.get("hot_files") or [])[:4]:
            path = row.get("path") if isinstance(row, dict) else str(row)
            if path and (repo / path).is_file():
                files.append(path)
    return files[:12]


def _estimate_blast_radius(repo: Path, files: list[str]) -> dict[str, Any]:
    surfaces: list[str] = []
    if any("workflow" in f or "github" in f for f in files):
        surfaces.append("CI")
    if any(f.startswith("web/") for f in files):
        surfaces.append("frontend builds")
    if any(f.startswith("aethos_core/") for f in files):
        surfaces.append("backend runtime")
    if any("test" in f for f in files):
        surfaces.append("tests")
    return {
        "scope": "bounded engineering mutation",
        "surfaces": surfaces or ["monorepo"],
        "file_count": len(files),
        "production_impact": any("operations/mutations" in f for f in files),
    }
