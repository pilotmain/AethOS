# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — Markdown renderer for mission strategy."""

from __future__ import annotations

from typing import Any

_SECTION_TITLES = {
    "long_running_mission_themes": "Long-running mission themes",
    "operational_drift": "Operational drift",
    "strategic_bottlenecks": "Strategic bottlenecks",
    "mission_outcome_comparison": "Mission outcome comparison",
    "governance_maturity_priorities": "Governance maturity priorities",
    "operational_hardening_areas": "Operational hardening areas",
    "unstable_rollout_patterns": "Unstable rollout patterns",
    "organizational_risk_concentration": "Organizational risk concentration",
    "high_friction_mission_archetypes": "High-friction mission archetypes",
}


def render_mission_strategy(strategy: dict[str, Any]) -> str:
    lines = [
        "# Mission Strategy Layer (FIX 145 — strategic cognition, read-only)",
        "",
        f"- session_id: `{strategy.get('session_id', '')}`",
        f"- recommendations: **{strategy.get('recommendation_count', 0)}**",
        f"- autonomous planning: **{strategy.get('autonomous_planning_enabled', False)}** _(always false)_",
        f"- organizational self-direction: **{strategy.get('organizational_self_direction_enabled', False)}** _(always false)_",
        "",
        strategy.get("invariant", ""),
        "",
        "_Strategic cognition without strategic autonomy — no reprioritization or policy mutation._",
        "",
    ]
    sections = strategy.get("sections") or {}

    risk = sections.get("organizational_risk_concentration") or {}
    if risk:
        lines.extend(
            [
                "## Organizational risk concentration",
                "",
                f"- score: **{risk.get('concentration_score', '—')}** ({risk.get('concentration_label', '')})",
                f"- factors: {risk.get('factors', {})}",
                "",
            ]
        )

    for key, title in _SECTION_TITLES.items():
        if key == "organizational_risk_concentration":
            continue
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_No signals in this section._")
        for item in items:
            if item.get("recommendation"):
                lines.append(f"- **[{item.get('priority', '—')}]** {item.get('recommendation')}")
                if item.get("rationale"):
                    lines.append(f"  - _{item.get('rationale')}_")
            elif item.get("insight"):
                lines.append(f"- {item.get('insight')}")
            elif item.get("theme"):
                lines.append(f"- theme `{item.get('theme')}` — {item}")
            elif item.get("signal"):
                lines.append(f"- **{item.get('signal')}**: {item.get('detail', '')}")
            elif item.get("pattern"):
                lines.append(f"- pattern: {item.get('pattern')}")
            elif item.get("archetype"):
                lines.append(f"- archetype **{item.get('archetype')}**: {item.get('detail', '')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All strategic recommendations are `executable: false`._")
    return "\n".join(lines)
