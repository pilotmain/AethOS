# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — Markdown renderer for agent execution quality and throughput metrics."""

from __future__ import annotations

from typing import Any


def render_agent_execution_quality_throughput_metrics(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}

    lines = [
        "# Agent Execution Quality & Throughput Metrics (FIX 190 — metrics ≠ authority)",
        "",
        f"- throughput score: **{payload.get('throughput_score')}** ({payload.get('throughput_label')})",
        f"- package completion: **{payload.get('package_completion_rate_percent')}%**",
        f"- human interventions: **{payload.get('human_intervention_count')}**",
        f"- FIX 189 receipts: **{payload.get('execution_receipt_count')}**",
        f"- agent metrics grant authority: **{payload.get('agent_metrics_grant_authority', False)}** _(always false)_",
        "",
        payload.get("invariant", ""),
        "",
        "## Per-agent success / failure",
        "",
    ]

    for row in sections.get("success_failure_per_agent") or []:
        lines.append(
            f"- `{row.get('agent_role_id')}`: success **{row.get('success_count')}** / "
            f"failure **{row.get('failure_count')}** · retries **{row.get('retry_count')}**"
        )
    lines.append("")

    throughput = (sections.get("end_to_end_throughput_score") or [{}])[0]
    lines.extend(
        [
            "## End-to-end throughput",
            "",
            f"- score: **{throughput.get('throughput_score')}**",
            f"- success rate: **{throughput.get('success_rate_percent')}%**",
            f"- label: **{throughput.get('throughput_label')}**",
            "",
            "_Metrics compose FIX 189 receipts only — no execution, no authority expansion._",
        ]
    )
    return "\n".join(lines)
