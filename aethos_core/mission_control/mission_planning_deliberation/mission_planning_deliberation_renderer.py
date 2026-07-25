# SPDX-License-Identifier: Apache-2.0
"""FIX 165 — Markdown renderer for mission planning deliberation."""

from __future__ import annotations

from typing import Any


def render_mission_planning_deliberation(mission_planning_deliberation: dict[str, Any]) -> str:
    sections = mission_planning_deliberation.get("sections") or {}

    lines = [
        "# Mission Planning Multi-Agent Deliberation (FIX 165 — bounded agent analysis)",
        "",
        f"- session_id: `{mission_planning_deliberation.get('session_id', '')}`",
        f"- deliberation records: **{mission_planning_deliberation.get('deliberation_record_count', 0)}**",
        f"- agent roles completed: **{mission_planning_deliberation.get('agent_role_count', 0)}**",
        f"- autonomous execution: **{mission_planning_deliberation.get('autonomous_execution_enabled', False)}** _(always false)_",
        f"- autonomous lane selection: **{mission_planning_deliberation.get('autonomous_lane_selection_enabled', False)}** _(always false)_",
        "",
        mission_planning_deliberation.get("invariant", ""),
        "",
        "_Bounded multi-agent deliberation — analysis only, never execution authority._",
        "",
    ]

    for title, key in (
        ("PlannerAgent analysis", "planner_agent_analysis"),
        ("RiskAgent analysis", "risk_agent_analysis"),
        ("ConstitutionalAgent analysis", "constitutional_agent_analysis"),
        ("DeliveryAgent analysis", "delivery_agent_analysis"),
        ("VerificationAgent analysis", "verification_agent_analysis"),
        ("SynthesisAgent summary", "synthesis_agent_summary"),
        ("Multi-agent deliberation map", "multi_agent_deliberation_map"),
        ("Consolidated recommendation", "consolidated_recommendation"),
        ("Deliberation integrity scoring", "deliberation_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("agent_role_id") and item.get("findings"):
                lines.append(f"- **{item.get('agent_role_id')}** ({item.get('focus')}): {'; '.join(item.get('findings') or [])}")
                for rec in item.get("recommendations") or []:
                    lines.append(f"  - {rec}")
            elif item.get("role_id"):
                lines.append(f"- `{item.get('role_id')}` ({item.get('display_name')}): {item.get('focus')}")
            elif item.get("recommendation_id"):
                lines.append(f"- **{item.get('recommendation_id')}**: {item.get('detail')}")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} label={item.get('integrity_label')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            elif item.get("map_id"):
                lines.append(f"- **{item.get('map_id')}**: {item.get('agent_output_count')} agent outputs")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All deliberation outputs are `executable: false` — humans select institutional path and govern execution._")
    return "\n".join(lines)
