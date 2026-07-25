# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — Markdown renderer for repository knowledge graph."""

from __future__ import annotations

from typing import Any


def render_repository_knowledge_graph(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    dashboard = (sections.get("engineering_intelligence_dashboard") or [{}])[0]
    architecture = (sections.get("architecture_graph") or [{}])[0]
    change_impact = (sections.get("change_impact_assessment") or [{}])[0]
    risk = (sections.get("repository_risk_profile") or [{}])[0]
    dependency_risk = (sections.get("dependency_risk_report") or [{}])[0]

    lines = [
        "# Repository Knowledge Graph (FIX 240 — repository_intelligence ≠ repository_authority)",
        "",
        f"- repository: **{payload.get('repository_display_name')}** (`{payload.get('repository_id')}`)",
        f"- repository authority: **{payload.get('repository_authority', False)}** _(always false)_",
        f"- knowledge graph execution: **{payload.get('knowledge_graph_execution', False)}** _(always false)_",
        f"- verification passed: **{payload.get('verification_passed')}**",
        "",
        payload.get("invariant", ""),
        "",
        "## Engineering Intelligence Dashboard",
        "",
        f"- architecture nodes: **{dashboard.get('architecture_node_count', 0)}**",
        f"- dependency risk score: **{dependency_risk.get('risk_score', 0)}**",
        f"- ownership confidence: **{dashboard.get('ownership_confidence_score', 0)}**",
        f"- repository risk score: **{risk.get('overall_risk_score', 0)}**",
        "",
        "## Architecture Graph",
        "",
        f"- active subsystems: {', '.join(architecture.get('active_subsystems') or []) or 'none'}",
        f"- node count: **{len(architecture.get('nodes') or [])}**",
        "",
        "## Change Impact Assessment",
        "",
        f"- affected systems: {', '.join(change_impact.get('affected_systems') or []) or 'none'}",
        f"- blast radius: **{change_impact.get('blast_radius') or 'unknown'}**",
        f"- likely reviewers: {', '.join(change_impact.get('likely_reviewers') or []) or 'pending'}",
        f"- deployment impact: **{change_impact.get('likely_deployment_impact')}**",
        "",
        "_Advisory only — understanding is not execution._",
    ]

    cross_repo = (sections.get("cross_repository_knowledge") or [{}])[0]
    repos = cross_repo.get("repositories") or []
    if repos:
        lines.extend(["", "## Phase 1 Repositories", ""])
        for repo in repos:
            lines.append(f"- {repo.get('display_name')} (`{repo.get('repository_id')}`)")

    return "\n".join(lines)
