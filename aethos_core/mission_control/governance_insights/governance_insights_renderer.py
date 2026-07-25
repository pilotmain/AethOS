# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — Markdown renderer for governance insights."""

from __future__ import annotations

from typing import Any

_SECTION_TITLES = {
    "approval_bottlenecks": "Approval bottlenecks",
    "governance_friction": "Governance friction",
    "rollback_patterns": "Rollback patterns",
    "verification_gaps": "Verification gaps",
    "approval_chain_inefficiencies": "Approval-chain inefficiencies",
    "high_risk_rollout_sequences": "High-risk rollout sequences",
    "governance_health_metrics": "Governance health metrics",
    "operator_workload_heatmap": "Operator workload heatmap",
    "mission_completion_latency": "Mission completion latency",
}


def render_governance_insights(payload: dict[str, Any]) -> str:
    lines = [
        "# Adaptive Governance Insights (FIX 143 — meta-governance, read-only)",
        "",
        f"- session_id: `{payload.get('session_id', '')}`",
        f"- insight count: **{payload.get('insight_count', 0)}**",
        f"- policy auto-tuning: **{payload.get('policy_auto_tuning_enabled', False)}** _(always false)_",
        f"- governance self-modification: **{payload.get('governance_self_modification_enabled', False)}** _(always false)_",
        "",
        payload.get("invariant", ""),
        "",
    ]
    sections = payload.get("insights") or {}

    metrics = sections.get("governance_health_metrics") or {}
    if metrics:
        lines.extend(["## Governance health metrics", ""])
        for key, val in metrics.items():
            if key != "read_only" and key != "note":
                lines.append(f"- {key}: **{val}**")
        if metrics.get("note"):
            lines.append(f"_{metrics.get('note')}_")
        lines.append("")

    for key, title in _SECTION_TITLES.items():
        if key == "governance_health_metrics":
            continue
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_No signals in this section._")
        for item in items:
            if isinstance(item, dict) and item.get("insight"):
                sev = item.get("severity", "—")
                lines.append(f"- **[{sev}]** {item.get('insight', '')}")
            elif isinstance(item, dict):
                lines.append(f"- `{item}`")
        lines.append("")

    lines.extend(["## Recommendations (insight-only)", ""])
    for rec in payload.get("recommendations") or []:
        lines.append(f"- [{rec.get('priority', '')}] {rec.get('recommendation', '')}")

    lines.append("")
    lines.append("_FIX 143 observes governance behavior — it does not tune policy or modify governance rules._")
    return "\n".join(lines)
