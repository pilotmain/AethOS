# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — Markdown renderer for cross-repository validation."""

from __future__ import annotations

from typing import Any


def render_cross_repository_multi_agent_delivery_validation(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    matrix = sections.get("cross_repository_validation_matrix") or []

    lines = [
        "# Cross-Repository Multi-Agent Delivery Validation (FIX 191 — validation ≠ trust granting)",
        "",
        f"- validation grants trust: **{payload.get('cross_repo_validation_grants_trust', False)}** _(always false)_",
        f"- pilot reexecution: **{payload.get('pilot_reexecution_performed', False)}** _(always false)_",
        "",
        payload.get("invariant", ""),
        "",
        "## Cross-Repository Validation Matrix",
        "",
        "| Repository | Trust State | Throughput | Alignment | Interventions | PR Open |",
        "|------------|-------------|------------|-----------|---------------|---------|",
    ]

    for row in matrix:
        throughput = row.get("throughput_score")
        alignment = row.get("alignment_score")
        pr_rate = row.get("pr_open_success_rate_percent")
        lines.append(
            f"| {row.get('display_name')} | {row.get('trust_state')} | "
            f"{throughput if throughput is not None else '-'} | "
            f"{alignment if alignment is not None else '-'} | "
            f"{row.get('human_intervention_count', 0)} | "
            f"{pr_rate if pr_rate is not None else '-'} |"
        )

    lines.extend(["", "## Delivery generalization", ""])
    assessment = (sections.get("delivery_generalization_assessment") or [{}])[0]
    lines.append(f"- largest unknown: {assessment.get('largest_unknown')}")
    lines.append(f"- merge/deploy premature: **{assessment.get('merge_deploy_premature')}**")
    lines.append("")
    lines.append("_Validation reports evidence — humans still grant trust._")
    return "\n".join(lines)
