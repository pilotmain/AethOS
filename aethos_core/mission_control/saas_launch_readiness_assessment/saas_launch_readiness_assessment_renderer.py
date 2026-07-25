# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment renderer."""

from __future__ import annotations

from typing import Any


def render_saas_launch_readiness_assessment(
    payload: dict[str, Any],
    *,
    focus: str = "launch_readiness_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("launch_readiness_dashboard") or [{}])[0]
    risks = (sections.get("launch_risk_registry") or [{}])[0]

    lines = [
        "# SaaS Launch Readiness Assessment",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 309')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Launch assessment ≠ launch authority. Humans decide launch readiness.",
        "",
        f"Overall status: **{payload.get('overall_launch_status', dashboard.get('overall_status', '—'))}**",
        f"Launch authority: **{payload.get('launch_authority', False)}**",
        "",
    ]

    if focus in {"launch_readiness_dashboard", "launch_risk_registry"}:
        lines.extend(["## Launch blockers", ""])
        for blocker in dashboard.get("blockers") or []:
            lines.append(f"- {blocker}")
        if not dashboard.get("blockers"):
            lines.append("- No critical blockers recorded from composed evidence.")
        lines.append("")

    if focus in {"launch_readiness_dashboard", "launch_risk_registry"}:
        lines.extend(["## Launch risks", ""])
        for level in ("critical", "high", "medium", "low"):
            rows = risks.get(level) or []
            if rows:
                lines.append(f"**{level.title()}**")
                for row in rows[:5]:
                    lines.append(f"- [{row.get('domain')}] {row.get('detail')}")
        lines.append("")

    if focus == "launch_readiness_dashboard":
        lines.extend(["## Domain readiness scores", ""])
        for domain, score in (dashboard.get("domain_scores") or {}).items():
            lines.append(f"- **{domain}**: {score}")

        coverage = dashboard.get("evidence_coverage") or {}
        lines.extend(
            [
                "",
                "## Evidence coverage",
                "",
                f"FIX 300–308 composed: **{coverage.get('fix_300_308_composed', 0)}** / **{coverage.get('fix_300_308_total', 9)}**",
                "",
                "## Recommendations",
                "",
            ]
        )
        for item in dashboard.get("recommendations") or []:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "No launch declaration or customer provisioning. Use `launch readiness note:` and "
            "`launch readiness review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
