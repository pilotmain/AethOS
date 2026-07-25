# SPDX-License-Identifier: Apache-2.0
"""Dependency reasoning — vulnerabilities, modernization targets, blast radius."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.local_workspace.analysis.dependencies import analyze_dependencies, format_dependency_report


def run_dependency_reasoning(repo: Path) -> dict[str, Any]:
    analysis = analyze_dependencies(repo)
    modernization = _modernization_targets(analysis)
    blast = _estimate_blast_radius(analysis, modernization)
    analysis["modernization_targets"] = modernization
    analysis["estimated_blast_radius"] = blast
    analysis["risk_signals"] = _dependency_signals(analysis, modernization)
    return analysis


def format_dependency_reasoning_report(analysis: dict[str, Any]) -> str:
    base = format_dependency_report(analysis)
    extra: list[str] = ["", "## Modernization targets"]
    for t in analysis.get("modernization_targets") or []:
        extra.append(f"- **{t.get('package')}** ({t.get('ecosystem')}) — {t.get('reason')}")
    blast = analysis.get("estimated_blast_radius") or {}
    extra.extend(
        [
            "",
            "## Estimated blast radius",
            f"- Scope: {blast.get('scope', 'unknown')}",
            f"- Impacted surfaces: {', '.join(blast.get('surfaces') or []) or '—'}",
            f"- Risk tier: {blast.get('risk_tier', 'medium')}",
        ]
    )
    return base + "\n".join(extra)


def _modernization_targets(analysis: dict[str, Any]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for finding in analysis.get("findings") or []:
        eco = "npm" if finding.get("ecosystem") == "npm" else "python" if finding.get("ecosystem") == "python" else "unknown"
        outdated = finding.get("outdated_preview") or []
        for pkg in outdated[:8]:
            targets.append(
                {
                    "package": str(pkg.get("name") or pkg),
                    "ecosystem": eco,
                    "reason": str(pkg.get("reason") or "stale or loose version range"),
                }
            )
        for vuln in (finding.get("audit") or {}).get("top_advisories") or []:
            if isinstance(vuln, dict):
                targets.append(
                    {
                        "package": str(vuln.get("name") or vuln.get("module") or "unknown"),
                        "ecosystem": eco,
                        "reason": f"vulnerability: {vuln.get('severity') or 'advisory'}",
                    }
                )
    if not targets and analysis.get("vulnerabilities"):
        for v in analysis["vulnerabilities"][:5]:
            targets.append(
                {
                    "package": str(v.get("name") or v.get("id") or "dependency"),
                    "ecosystem": "mixed",
                    "reason": "known vulnerability in manifest scan",
                }
            )
    return targets[:12]


def _estimate_blast_radius(analysis: dict[str, Any], targets: list[dict[str, str]]) -> dict[str, Any]:
    count = len(targets)
    severity = str(analysis.get("severity") or "low")
    if count >= 8 or severity == "high":
        tier = "high"
        scope = "repo-wide dependency refresh likely required"
    elif count >= 3:
        tier = "medium"
        scope = "targeted package upgrades with regression testing"
    else:
        tier = "low"
        scope = "isolated dependency updates"
    surfaces: list[str] = []
    for finding in analysis.get("findings") or []:
        if finding.get("ecosystem") == "npm":
            surfaces.append("frontend/runtime JS")
        if finding.get("ecosystem") == "python":
            surfaces.append("backend API/runtime")
    return {"scope": scope, "surfaces": sorted(set(surfaces)), "risk_tier": tier, "target_count": count}


def _dependency_signals(analysis: dict[str, Any], targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for v in analysis.get("vulnerabilities") or []:
        signals.append({"kind": "vulnerability", "weight": 2, "detail": str(v.get("name") or "dependency vuln")})
    if len(targets) >= 5:
        signals.append({"kind": "hotspot", "weight": 1, "detail": f"{len(targets)} modernization targets"})
    return signals
