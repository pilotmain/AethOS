# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center renderer."""

from __future__ import annotations

from typing import Any


def render_launch_operations_center(
    payload: dict[str, Any],
    *,
    focus: str = "launch_operations_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("launch_operations_dashboard") or [{}])[0]
    recommendation = (sections.get("launch_recommendation") or [{}])[0]
    status = (sections.get("launch_status_registry") or [{}])[0]

    lines = [
        "# Launch Operations Center",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 313')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Launch operations visibility ≠ launch authority. Humans decide launch.",
        "",
        f"Launch phase: **{status.get('current_launch_phase', '—')}**",
        f"Recommendation: **{recommendation.get('recommendation', payload.get('launch_recommendation', '—'))}**",
        "",
    ]

    if focus in {"launch_operations_dashboard", "launch_status_registry"}:
        lines.extend(
            [
                "## Launch status",
                "",
                f"Readiness: **{status.get('readiness_status', '—')}**",
                f"Beta: **{status.get('beta_status', '—')}**",
                f"Review: **{status.get('review_status', '—')}**",
                "",
            ]
        )

    if focus in {"launch_operations_dashboard", "launch_blocker_registry"}:
        blockers = (sections.get("launch_blocker_registry") or [{}])[0]
        lines.extend(["## Launch blockers", ""])
        for row in (blockers.get("blockers") or [])[:8]:
            lines.append(f"- [{row.get('source')}] {row.get('detail')}")
        if not blockers.get("blockers"):
            lines.append("- No launch blockers from composed evidence.")
        lines.append("")

    if focus in {"launch_operations_dashboard", "launch_risk_dashboard"}:
        risks = (sections.get("launch_risk_dashboard") or [{}])[0]
        for category in ("product", "operational", "governance", "customer"):
            rows = risks.get(category) or []
            if rows:
                lines.append(f"## {category.title()} risks")
                lines.append("")
                for row in rows[:4]:
                    lines.append(f"- [{row.get('level')}] {row.get('detail')}")
                lines.append("")

    if focus == "beta_operations_monitor":
        beta = (sections.get("beta_operations_monitor") or [{}])[0]
        lines.extend(
            [
                "## Beta operations",
                "",
                f"Active cohorts: **{beta.get('active_cohort_count', 0)}**",
                f"Feedback count: **{beta.get('feedback_count', 0)}**",
                f"Activation rate: **{beta.get('activation_rate', 0)}%**",
                "",
            ]
        )

    if focus == "customer_operations_monitor":
        customer = (sections.get("customer_operations_monitor") or [{}])[0]
        lines.extend(
            [
                "## Customer operations",
                "",
                f"Healthy: **{customer.get('healthy_count', 0)}**",
                f"At risk: **{customer.get('at_risk_count', 0)}**",
                f"Open escalations: **{customer.get('open_escalation_count', 0)}**",
                "",
            ]
        )

    if focus == "launch_operations_dashboard":
        lines.extend(
            [
                "## Operations summary",
                "",
                f"Blockers: **{dashboard.get('blocker_count', 0)}**",
                f"Critical risks: **{dashboard.get('critical_risk_count', 0)}**",
                f"Platform healthy: **{dashboard.get('platform_healthy', False)}**",
                "",
                recommendation.get("rationale", "Recommendation derived from evidence only."),
            ]
        )

    lines.extend(
        [
            "",
            "No launch execution, provisioning, or automatic beta expansion. "
            "Use `launch operations note:` and `launch operations review approve:` for human review only.",
        ]
    )
    return "\n".join(lines)
