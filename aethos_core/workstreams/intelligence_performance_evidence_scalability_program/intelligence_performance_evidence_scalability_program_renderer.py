# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E1 / FIX 343 — render intelligence performance deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_intelligence_performance_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    trends = payload.get("latency_trends") or {}
    hotspots = _section(payload, "phase_5_hotspot_registry", "compose_hotspot_registry") or {}
    lines = [
        "# Intelligence Performance Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 343')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Performance optimization may not reduce evidence quality. **Performance optimization ≠ truth reduction.**",
        "",
        "## Compose latency",
        "",
        f"- Total tracked compose duration: **{trends.get('total_compose_duration_sec', 0)}s**",
        f"- Slowest module: **{trends.get('slowest_module', '—')}**",
        f"- Scalability risk: **{trends.get('scalability_risk')}**",
        "",
        "## Hotspots",
        "",
    ]
    for row in hotspots.get("hotspots") or []:
        lines.append(
            f"- **{row.get('module')}** — {row.get('duration_sec')}s "
            f"(fan-in {row.get('fan_in')}, severity {row.get('severity')})"
        )
    lines.extend(
        [
            "",
            "## Success criteria",
            "",
            f"- Hotspots identified: **{success.get('compose_hotspots_identified')}**",
            f"- Duplicate paths identified: **{success.get('duplicate_paths_identified')}**",
            f"- Truth reduction performed: **{success.get('truth_reduction_performed')}**",
            f"- Program complete: **{success.get('program_complete')}**",
        ]
    )
    return "\n".join(lines)


def render_compose_dependency_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_dependency_analysis", "compose_dependency_report") or {}
    lines = [
        "# Compose Dependency Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Duplicate composition paths",
        "",
    ]
    for row in report.get("duplicate_compose_paths") or []:
        lines.append(
            f"- **{row.get('dependency')}** recomposed by {row.get('consumer_count')} modules: "
            f"{', '.join(row.get('consumers') or [])}"
        )
    lines.extend(["", "## Recursive fan-in chains", ""])
    for row in report.get("recursive_fan_in_chains") or []:
        lines.append(f"- {' → '.join(row.get('chain') or [])}: {row.get('description')}")
    lines.extend(["", "## Expensive evidence chains", ""])
    for row in report.get("expensive_evidence_chains") or []:
        lines.append(f"- **{row.get('module')}** — {row.get('duration_sec')}s (fan-in {row.get('fan_in')})")
    return "\n".join(lines)


def render_evidence_scalability_report(payload: dict[str, Any]) -> str:
    cache = _section(payload, "phase_3_evidence_caching_analysis", "evidence_cache_report") or {}
    incremental = _section(payload, "phase_4_incremental_composition", "incremental_compose_strategy") or {}
    matrix = _section(payload, "phase_7_performance_priority_matrix", "performance_priority_matrix") or {}
    lines = [
        "# Evidence Scalability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Incremental compose strategy",
        "",
        "```json",
        _json_block(incremental),
        "```",
        "",
        "## Cache boundaries",
        "",
        f"- Reusable evidence modules: **{len(cache.get('reusable_evidence') or [])}**",
        f"- Immutable evidence modules: **{len(cache.get('immutable_evidence') or [])}**",
        f"- Dynamic evidence modules: **{len(cache.get('dynamic_evidence') or [])}**",
        "",
        "## Priority matrix (top opportunities)",
        "",
    ]
    for row in (matrix.get("ranked_opportunities") or [])[:5]:
        lines.append(
            f"- **{row.get('title')}** — impact {row.get('impact')}, "
            f"effort {row.get('effort')}, score {row.get('priority_score')}"
        )
    return "\n".join(lines)


def render_all_intelligence_performance_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "INTELLIGENCE_PERFORMANCE_REPORT.md": render_intelligence_performance_report(payload),
        "COMPOSE_DEPENDENCY_ANALYSIS.md": render_compose_dependency_analysis(payload),
        "EVIDENCE_SCALABILITY_REPORT.md": render_evidence_scalability_report(payload),
    }


def render_intelligence_performance_evidence_scalability_program(
    payload: dict[str, Any],
    *,
    focus: str = "intelligence_performance_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_executive_visibility", "intelligence_performance_dashboard") or {}
    trends = payload.get("latency_trends") or {}
    lines = [
        "# Intelligence Performance & Evidence Scalability Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 343')}",
        "",
        "Reduce intelligence compose latency while preserving evidence integrity.",
        "",
        f"Scalability risk: **{dashboard.get('scalability_risk', trends.get('scalability_risk'))}**",
        f"Slowest module: **{trends.get('slowest_module', '—')}**",
        "",
        "## Operator commands",
        "",
        "- `performance note: ...`",
        "- `analyze intelligence performance`",
        "- `performance review approve: ...`",
        "- `show intelligence performance dashboard`",
        "",
    ]
    return "\n".join(lines)
