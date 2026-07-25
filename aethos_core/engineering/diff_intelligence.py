# SPDX-License-Identifier: Apache-2.0
"""Engineering diff intelligence — risk, blast radius, migration signals."""

from __future__ import annotations

import re
from typing import Any


def analyze_patch_diffs(
    *,
    unified_diffs: list[dict[str, str]],
    blast_radius: dict[str, Any] | None = None,
    task: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task = task or {}
    files = [d.get("file") for d in unified_diffs if d.get("file")]
    risky: list[str] = []
    warnings: list[str] = []
    api_changes = False
    migration_risk = "low"
    broad_refactor = False

    total_lines = sum(int(d.get("lines_changed") or 0) for d in unified_diffs)
    if len(files) > 8:
        broad_refactor = True
        warnings.append("More than 8 files changed — broad refactor signal.")
    if total_lines > 200:
        warnings.append("Large diff volume — review carefully.")

    for d in unified_diffs:
        diff = d.get("diff") or ""
        rel = str(d.get("file") or "")
        if re.search(r"^[-+].*\b(password|secret|api_key|token)\b", diff, re.I | re.M):
            risky.append(f"Possible secret touch in `{rel}`")
        if "operations/mutations" in rel:
            risky.append(f"Mutation surface touched: `{rel}`")
        if re.search(r"^[-+].*def |^[-+].*class ", diff, re.M):
            api_changes = True

    if task.get("kind") == "dependency_modernization":
        migration_risk = "medium"
        warnings.append("Dependency modernization — verify compatibility matrix.")

    severity = "low"
    if risky:
        severity = "high"
    elif broad_refactor or api_changes:
        severity = "medium"

    return {
        "summary": _summary(task, files, severity),
        "severity": severity,
        "risky_edits": risky,
        "warnings": warnings,
        "blast_radius": blast_radius or {},
        "api_contract_changes": api_changes,
        "broad_refactor": broad_refactor,
        "migration_risk": migration_risk,
        "dependency_impact": _dependency_impact(files),
        "file_count": len(files),
        "total_diff_lines": total_lines,
    }


def _summary(task: dict[str, Any], files: list[str], severity: str) -> str:
    title = task.get("title") or "Governed patch"
    return f"{title} — {len(files)} file(s), severity {severity}."


def _dependency_impact(files: list[str]) -> list[str]:
    impacts: list[str] = []
    if any(f.endswith("package.json") for f in files):
        impacts.append("npm dependency graph")
    if any("requirements" in f for f in files):
        impacts.append("python dependencies")
    if any(f.startswith("web/") for f in files):
        impacts.append("frontend build")
    return impacts
