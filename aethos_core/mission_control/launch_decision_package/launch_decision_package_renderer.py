# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package renderer."""

from __future__ import annotations

from typing import Any


def render_launch_decision_package(
    payload: dict[str, Any],
    *,
    focus: str = "launch_decision_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("launch_decision_dashboard") or [{}])[0]
    recommendation = (sections.get("launch_recommendation_package") or [{}])[0]
    executive = (sections.get("launch_executive_summary") or [{}])[0]

    lines = [
        "# Launch Decision Package",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 315')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Launch decision package ≠ launch decision. Humans approve launch, not AethOS.",
        "",
        f"Recommendation: **{recommendation.get('recommendation', payload.get('launch_recommendation_package', '—'))}**",
        "",
    ]

    if focus in {"launch_decision_dashboard", "launch_executive_summary"}:
        lines.extend(
            [
                "## Executive summary",
                "",
                f"Platform: {executive.get('platform_summary', '—')}",
                f"Readiness: {executive.get('readiness_summary', '—')}",
                f"Trust: {executive.get('trust_summary', '—')}",
                f"Recommendation: {executive.get('recommendation_summary', '—')}",
                "",
            ]
        )

    if focus == "launch_decision_dashboard":
        capability = (sections.get("launch_capability_summary") or [{}])[0]
        trust = (sections.get("launch_trust_evidence_summary") or [{}])[0]
        lines.extend(
            [
                "## Review package summary",
                "",
                f"Proven capabilities: **{capability.get('proven_count', 0)}**",
                f"Operational capabilities: **{capability.get('operational_count', 0)}**",
                f"Trust baselines: **{trust.get('baseline_count', 0)}**",
                f"Open blockers: **{dashboard.get('open_blocker_count', 0)}**",
                f"Critical risks: **{dashboard.get('critical_risk_count', 0)}**",
                "",
            ]
        )

    if focus in {"launch_decision_dashboard", "launch_risk_summary"}:
        risks = (sections.get("launch_risk_summary") or [{}])[0]
        lines.extend(["## Risk summary", ""])
        for level in ("critical", "high", "medium", "low"):
            rows = risks.get(level) or []
            if rows:
                lines.append(f"**{level.title()}** ({len(rows)})")
                for row in rows[:3]:
                    lines.append(f"- {row.get('detail')}")
        lines.append("")

    if focus in {"launch_decision_dashboard", "launch_blocker_summary"}:
        blockers = (sections.get("launch_blocker_summary") or [{}])[0]
        lines.extend(["## Blocker summary", ""])
        for row in (blockers.get("open") or [])[:6]:
            lines.append(f"- [{row.get('source')}] {row.get('detail')}")
        lines.append("")

    if focus == "launch_recommendation_package":
        lines.extend(
            [
                "## Recommendation rationale",
                "",
                recommendation.get("rationale", "Derived from frozen evidence only."),
                "",
                "### Decision options",
                "",
            ]
        )
        for option in recommendation.get("decision_options") or []:
            lines.append(f"- {option}")
        lines.extend(["", "### What is proven", ""])
        for item in dashboard.get("proven_items") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### What remains unproven", ""])
        for item in dashboard.get("unproven_items") or []:
            lines.append(f"- {item}")

    if focus == "launch_decision_registry":
        registry = (sections.get("launch_decision_registry") or [{}])[0]
        lines.extend(["## Decision history", ""])
        for row in (registry.get("records") or [])[:8]:
            lines.append(f"- [{row.get('kind')}] {row.get('content')}")
        lines.append("")

    lines.extend(
        [
            "",
            "No launch approval, execution, or beta expansion. "
            "Use `launch decision note:` and `launch decision approve:` for human review only.",
        ]
    )
    return "\n".join(lines)
