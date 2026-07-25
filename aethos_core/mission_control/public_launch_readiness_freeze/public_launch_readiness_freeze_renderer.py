# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze renderer."""

from __future__ import annotations

from typing import Any


def render_public_launch_readiness_freeze(
    payload: dict[str, Any],
    *,
    focus: str = "launch_readiness_freeze_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("launch_readiness_freeze_dashboard") or [{}])[0]
    recommendation = (sections.get("launch_recommendation_freeze") or [{}])[0]

    lines = [
        "# Public Launch Readiness Freeze",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 314')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Launch readiness freeze ≠ launch authority. Evidence frozen for human review.",
        "",
        f"Recommendation: **{recommendation.get('recommendation', payload.get('launch_recommendation_freeze', '—'))}**",
        "",
    ]

    if focus in {"launch_readiness_freeze_dashboard", "launch_evidence_timeline"}:
        timeline = (sections.get("launch_evidence_timeline") or [{}])[0]
        lines.extend(["## Launch evidence timeline", ""])
        for event in (timeline.get("events") or [])[:8]:
            lines.append(f"- [{event.get('fix')}] {event.get('detail')}")
        lines.append("")

    if focus == "launch_readiness_freeze_dashboard":
        trust = (sections.get("launch_trust_baseline_summary") or [{}])[0]
        capability = (sections.get("launch_capability_baseline") or [{}])[0]
        lines.extend(
            [
                "## Frozen baseline summary",
                "",
                f"Trust baselines frozen: **{trust.get('baseline_count', 0)}**",
                f"Proven capabilities: **{capability.get('proven_count', 0)}**",
                f"Unproven capabilities: **{capability.get('unproven_count', 0)}**",
                f"Blockers frozen: **{dashboard.get('blocker_count', 0)}**",
                f"Risks frozen: **{dashboard.get('risk_count', 0)}**",
                "",
            ]
        )

    if focus in {"launch_readiness_freeze_dashboard", "launch_blocker_freeze"}:
        blockers = (sections.get("launch_blocker_freeze") or [{}])[0]
        lines.extend(["## Launch blockers (frozen)", ""])
        for row in (blockers.get("blockers") or [])[:6]:
            lines.append(f"- [{row.get('source')}] {row.get('detail')}")
        lines.append("")

    if focus in {"launch_readiness_freeze_dashboard", "launch_risk_freeze"}:
        risks = (sections.get("launch_risk_freeze") or [{}])[0]
        lines.extend(["## Launch risks (frozen)", ""])
        for row in (risks.get("risks") or [])[:6]:
            lines.append(f"- [{row.get('level')}] {row.get('detail')}")
        lines.append("")

    if focus == "launch_recommendation_freeze":
        lines.extend(
            [
                "## Recommendation rationale",
                "",
                recommendation.get("rationale", "Derived from frozen evidence only."),
                "",
                "### What is proven",
                "",
            ]
        )
        for item in dashboard.get("proven_items") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### What remains unproven", ""])
        for item in dashboard.get("unproven_items") or []:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "No launch execution, trust mutation, or readiness promotion. "
            "Use `launch freeze note:` and `launch freeze review approve:` for human review only.",
        ]
    )
    return "\n".join(lines)
