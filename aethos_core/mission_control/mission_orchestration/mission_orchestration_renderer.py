# SPDX-License-Identifier: Apache-2.0
"""FIX 146 — Markdown renderer for mission orchestration."""

from __future__ import annotations

from typing import Any

_SECTION_TITLES = {
    "mission_dependency_graph": "Mission dependency graph",
    "governed_stage_orchestration": "Governed stage orchestration",
    "lane_synchronization_visibility": "Lane synchronization visibility",
    "blocked_by_relationships": "Blocked-by relationships",
    "upstream_downstream_mission_effects": "Upstream/downstream mission effects",
    "orchestration_readiness_scoring": "Orchestration readiness scoring",
    "operator_sequencing_recommendations": "Operator sequencing recommendations",
    "coordinated_approval_batching_recommendations": "Coordinated approval batching recommendations",
    "cross_lane_mission_health": "Cross-lane mission health",
}


def render_mission_orchestration(orchestration: dict[str, Any]) -> str:
    lines = [
        "# Coordinated Mission Orchestration (FIX 146 — coordination cognition, read-only)",
        "",
        f"- session_id: `{orchestration.get('session_id', '')}`",
        f"- plan_id: `{orchestration.get('plan_id') or '—'}`",
        f"- correlation_id: `{orchestration.get('correlation_id') or '—'}`",
        f"- recommendations: **{orchestration.get('recommendation_count', 0)}**",
        f"- autonomous orchestration: **{orchestration.get('autonomous_orchestration_enabled', False)}** _(always false)_",
        f"- autonomous sequencing: **{orchestration.get('autonomous_sequencing_execution_enabled', False)}** _(always false)_",
        "",
        orchestration.get("invariant", ""),
        "",
        "_Mission-level orchestration cognition — no autonomous sequencing, batching, or deploy._",
        "",
    ]

    sections = orchestration.get("sections") or {}

    readiness = sections.get("orchestration_readiness_scoring") or {}
    if readiness:
        lines.extend(
            [
                "## Orchestration readiness",
                "",
                f"- score: **{readiness.get('readiness_score', '—')}** ({readiness.get('readiness_label', '')})",
                f"- factors: {readiness.get('factors', {})}",
                "",
            ]
        )

    health = sections.get("cross_lane_mission_health") or {}
    if health:
        lines.extend(
            [
                "## Cross-lane mission health",
                "",
                f"- overall: **{health.get('overall', '—')}**",
                f"- pending gates: {health.get('pending_gates', 0)} · open incidents: {health.get('open_incidents', 0)}",
                "",
            ]
        )

    stage = sections.get("governed_stage_orchestration") or {}
    if stage:
        lines.extend(
            [
                "## Governed stage orchestration",
                "",
                f"- current stage: `{stage.get('current_stage', '—')}`",
                f"- upcoming: {stage.get('upcoming_stages', [])}",
                f"- pending gates: {stage.get('pending_gates', [])}",
                "",
            ]
        )

    graph = sections.get("mission_dependency_graph") or {}
    if graph:
        lines.extend(
            [
                "## Mission dependency graph",
                "",
                f"- nodes: **{graph.get('node_count', 0)}** · edges: **{graph.get('edge_count', 0)}**",
                "",
            ]
        )

    for key, title in _SECTION_TITLES.items():
        if key in {
            "orchestration_readiness_scoring",
            "cross_lane_mission_health",
            "governed_stage_orchestration",
            "mission_dependency_graph",
        }:
            continue
        items = sections.get(key)
        lines.extend([f"## {title}", ""])
        if items is None or items == {}:
            lines.append("_No signals in this section._")
        elif isinstance(items, dict):
            for sub_key, val in items.items():
                if sub_key == "lanes" and isinstance(val, dict):
                    for lane, row in val.items():
                        lines.append(f"- **{lane}**: {row.get('status')} ({row.get('sync_label')})")
                else:
                    lines.append(f"- {sub_key}: {val}")
        elif isinstance(items, list):
            if not items:
                lines.append("_No signals in this section._")
            for item in items:
                if item.get("recommendation"):
                    lines.append(f"- **[{item.get('priority', '—')}]** {item.get('recommendation')}")
                    if item.get("rationale"):
                        lines.append(f"  - _{item.get('rationale')}_")
                elif item.get("blocked_by"):
                    lines.append(
                        f"- `{item.get('blocked_entity')}` blocked by **{item.get('blocked_by')}** "
                        f"({item.get('priority', 'medium')})"
                    )
                elif item.get("effect"):
                    lines.append(
                        f"- {item.get('upstream')} → {item.get('downstream')}: {item.get('effect')}"
                    )
                elif item.get("lane"):
                    lines.append(
                        f"- **{item.get('lane')}**: {item.get('sync_label')} "
                        f"(synchronized={item.get('synchronized')})"
                    )
                else:
                    lines.append(f"- {item}")
        lines.append("")

    lines.append("_All orchestration recommendations are `executable: false`._")
    return "\n".join(lines)
