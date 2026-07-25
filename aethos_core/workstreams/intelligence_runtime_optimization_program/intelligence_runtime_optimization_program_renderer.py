# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 / FIX 344 — render intelligence runtime optimization deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_intelligence_runtime_optimization_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("runtime_metrics") or {}
    hotspots = _section(payload, "phase_5_runtime_hotspot_registry", "runtime_hotspot_registry") or {}
    lines = [
        "# Intelligence Runtime Optimization Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 344')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Runtime optimization may never reduce evidence quality. **Runtime optimization ≠ truth reduction.**",
        "",
        "## Runtime metrics",
        "",
        f"- Compose duration reduction (projected): **{metrics.get('compose_duration_reduction', 0)}**",
        f"- Cache hit ratio: **{metrics.get('cache_hit_ratio', 0)}**",
        f"- Artifact reuse ratio: **{metrics.get('artifact_reuse_ratio', 0)}**",
        f"- Dependency depth reduction: **{metrics.get('dependency_depth_reduction', 0)}**",
        f"- Recomposition reduction: **{metrics.get('recomposition_reduction', 0)}**",
        "",
        "## Hotspots",
        "",
    ]
    for row in hotspots.get("hotspots") or []:
        lines.append(
            f"- **{row.get('module')}** — {row.get('duration_sec')}s "
            f"(recompositions {row.get('recomposition_frequency')}, severity {row.get('severity')})"
        )
    lines.extend(
        [
            "",
            "## Success criteria",
            "",
            f"- Hotspots identified: **{success.get('runtime_hotspots_identified')}**",
            f"- Flattening planned: **{success.get('dependency_flattening_planned')}**",
            f"- Truth reduction performed: **{success.get('truth_reduction_performed')}**",
            f"- Program complete: **{success.get('program_complete')}**",
        ]
    )
    return "\n".join(lines)


def render_dependency_flattening_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_dependency_flattening_analysis", "dependency_flattening_report") or {}
    memo = _section(payload, "phase_2_memoization_opportunity_analysis", "memoization_opportunity_report") or {}
    lines = [
        "# Dependency Flattening Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Current recursive chain",
        "",
        " → ".join(report.get("current_chain") or []),
        "",
        "## Target chain",
        "",
        " → ".join(report.get("target_chain") or []),
        "",
        f"- Current depth: **{report.get('current_depth')}**",
        f"- Target depth: **{report.get('target_depth')}**",
        f"- Projected compose avoidance: **{report.get('projected_compose_avoidance_sec')}s**",
        "",
        "## Memoization targets",
        "",
    ]
    for row in memo.get("high_value_modules") or []:
        lines.append(
            f"- **{row.get('module')}** — {row.get('recomposition_count')} recompositions, "
            f"value {row.get('memoization_value')}"
        )
    return "\n".join(lines)


def render_runtime_scalability_report(payload: dict[str, Any]) -> str:
    artifacts = _section(payload, "phase_3_artifact_persistence_analysis", "artifact_persistence_report") or {}
    matrix = _section(payload, "phase_7_optimization_priority_matrix", "runtime_optimization_priority_matrix") or {}
    lines = [
        "# Runtime Scalability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Artifact persistence candidates",
        "",
    ]
    for row in artifacts.get("candidates") or []:
        lines.append(
            f"- **{row.get('module')}** — {row.get('baseline_duration_sec')}s baseline, "
            f"fan-in {row.get('fan_in')}"
        )
    lines.extend(["", "## Priority matrix (top opportunities)", ""])
    for row in (matrix.get("ranked_opportunities") or [])[:5]:
        lines.append(
            f"- **{row.get('title')}** — category {row.get('category')}, "
            f"impact {row.get('impact')}, score {row.get('priority_score')}"
        )
    lines.extend(["", "## Metrics tracked", ""])
    for metric in payload.get("runtime_optimization_metrics") or []:
        lines.append(f"- {metric.replace('_', ' ')}")
    return "\n".join(lines)


def render_all_intelligence_runtime_optimization_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "INTELLIGENCE_RUNTIME_OPTIMIZATION_REPORT.md": render_intelligence_runtime_optimization_report(payload),
        "DEPENDENCY_FLATTENING_ANALYSIS.md": render_dependency_flattening_analysis(payload),
        "RUNTIME_SCALABILITY_REPORT.md": render_runtime_scalability_report(payload),
    }


def render_intelligence_runtime_optimization_program(
    payload: dict[str, Any],
    *,
    focus: str = "runtime_optimization_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_executive_visibility", "runtime_optimization_dashboard") or {}
    metrics = payload.get("runtime_metrics") or {}
    lines = [
        "# Intelligence Runtime Optimization Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 344')}",
        "",
        "Reduce intelligence runtime cost while preserving evidence, trust, and governance integrity.",
        "",
        f"Projected compose reduction: **{metrics.get('compose_duration_reduction', 0)}**",
        f"Scalability improving: **{dashboard.get('scalability_improving')}**",
        "",
        "## Operator commands",
        "",
        "- `runtime optimization note: ...`",
        "- `analyze runtime optimization`",
        "- `runtime optimization review approve: ...`",
        "- `show runtime optimization dashboard`",
        "",
    ]
    return "\n".join(lines)
