# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 / FIX 345 — render scalability implementation deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_intelligence_scalability_implementation_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    benchmark = payload.get("runtime_benchmark") or {}
    lines = [
        "# Intelligence Scalability Implementation Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 345')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Optimization execution may never mutate truth. **Optimization execution ≠ truth mutation.**",
        "",
        "## Implementation status",
        "",
        f"- Memoization implemented: **{success.get('memoization_implemented')}**",
        f"- PMF snapshot persisted: **{success.get('pmf_snapshot_persisted')}**",
        f"- Value snapshot persisted: **{success.get('value_snapshot_persisted')}**",
        f"- Dependency flattening executed: **{success.get('dependency_flattening_executed')}**",
        f"- Truth preservation verified: **{success.get('truth_preservation_verified')}**",
        "",
        "## Runtime benchmark",
        "",
        f"- Before: **{benchmark.get('before_compose_duration_sec', '—')}s**",
        f"- After: **{benchmark.get('after_compose_duration_sec', '—')}s**",
        f"- Reduction: **{benchmark.get('compose_duration_reduction_pct', 0)}**",
        f"- Cache hit ratio: **{benchmark.get('cache_hit_ratio', 0)}**",
        "",
        f"- Program complete: **{success.get('program_complete')}**",
    ]
    return "\n".join(lines)


def render_runtime_benchmark_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_runtime_benchmarking", "runtime_benchmark_report") or {}
    benchmark = report.get("benchmark") or payload.get("runtime_benchmark") or report
    lines = [
        "# Runtime Benchmark Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Before vs after",
        "",
        "```json",
        _json_block(
            {
                "before": report.get("before_optimization") or {
                    "compose_duration_sec": benchmark.get("before_compose_duration_sec"),
                },
                "after": report.get("after_optimization") or {
                    "compose_duration_sec": benchmark.get("after_compose_duration_sec"),
                },
                "compose_duration_reduction_pct": benchmark.get("compose_duration_reduction_pct"),
                "cache_hit_ratio": benchmark.get("cache_hit_ratio"),
                "snapshot_reuse_ratio": benchmark.get("snapshot_reuse_ratio"),
                "runtime_cost_reduction_pct": benchmark.get("runtime_cost_reduction_pct"),
            }
        ),
        "```",
    ]
    return "\n".join(lines)


def render_truth_preservation_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_6_truth_preservation_validation", "truth_preservation_report") or {}
    lines = [
        "# Truth Preservation Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Evidence provenance identical: **{report.get('evidence_provenance_identical')}**",
        f"- Trust boundaries identical: **{report.get('trust_boundaries_identical')}**",
        f"- Governance guarantees identical: **{report.get('governance_guarantees_identical')}**",
        f"- Truth mutation performed: **{report.get('truth_mutation_performed')}**",
        f"- Answer quality reduced: **{report.get('answer_quality_reduced')}**",
        "",
        "## Validation checks",
        "",
    ]
    for check in report.get("validation_checks") or []:
        lines.append(f"- {check.replace('_', ' ')}")
    return "\n".join(lines)


def render_all_intelligence_scalability_implementation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    flattening = _section(payload, "phase_4_dependency_flattening_execution", "dependency_flattening_execution_report") or {}
    runtime_report = render_intelligence_scalability_implementation_report(payload)
    if flattening:
        runtime_report += (
            "\n\n## Dependency flattening\n\n"
            f"- Depth reduction: **{flattening.get('dependency_depth_reduction', 0)}**\n"
            f"- Flattened: **{flattening.get('flattened')}**\n"
        )
    return {
        "INTELLIGENCE_SCALABILITY_IMPLEMENTATION_REPORT.md": runtime_report,
        "RUNTIME_BENCHMARK_REPORT.md": render_runtime_benchmark_report(payload),
        "TRUTH_PRESERVATION_REPORT.md": render_truth_preservation_report(payload),
    }


def render_intelligence_scalability_implementation_program(
    payload: dict[str, Any],
    *,
    focus: str = "intelligence_scalability_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_executive_visibility", "intelligence_scalability_dashboard") or {}
    benchmark = payload.get("runtime_benchmark") or {}
    lines = [
        "# Intelligence Scalability Implementation Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 345')}",
        "",
        "Execute runtime scalability improvements while preserving evidence and governance integrity.",
        "",
        f"Runtime improved: **{dashboard.get('runtime_improved', False)}**",
        f"Compose reduction: **{benchmark.get('compose_duration_reduction_pct', 0)}**",
        "",
        "## Operator commands",
        "",
        "- `scalability note: ...`",
        "- `execute scalability implementation`",
        "- `scalability review approve: ...`",
        "- `show intelligence scalability dashboard`",
        "",
    ]
    return "\n".join(lines)
