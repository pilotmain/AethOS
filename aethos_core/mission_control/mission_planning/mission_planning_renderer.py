# SPDX-License-Identifier: Apache-2.0
"""FIX 164 — Markdown renderer for mission planning."""

from __future__ import annotations

from typing import Any


def render_mission_planning(mission_planning: dict[str, Any]) -> str:
    sections = mission_planning.get("sections") or {}

    lines = [
        "# Mission Planning + Institutional Action Cognition (FIX 164 — planning cognition)",
        "",
        f"- session_id: `{mission_planning.get('session_id', '')}`",
        f"- planning records: **{mission_planning.get('planning_record_count', 0)}**",
        f"- autonomous action execution: **{mission_planning.get('autonomous_action_execution_enabled', False)}** _(always false)_",
        f"- auto path selection: **{mission_planning.get('auto_path_selection_enabled', False)}** _(always false)_",
        f"- railway mutation: **{mission_planning.get('railway_mutation_enabled', False)}** _(always false)_",
        "",
        mission_planning.get("invariant", ""),
        "",
        "_Mission planning cognition — recommendation-only, never execution authority or autonomous path selection._",
        "",
    ]

    for title, key in (
        ("Action option generation", "action_option_generation"),
        ("Option comparison", "option_comparison"),
        ("Lane touch mapping", "lane_touch_mapping"),
        ("Required approvals", "required_approvals"),
        ("Constitutional tradeoffs", "constitutional_tradeoffs"),
        ("Risks and blockers", "risks_and_blockers"),
        ("Do not do paths", "do_not_do_paths"),
        ("Operator review sequence", "operator_review_sequence"),
        ("Mission action plan artifact", "mission_action_plan_artifact"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("option_id"):
                lanes = ", ".join(item.get("lanes_touched") or []) or "none"
                lines.append(f"- **{item.get('option_id')}** ({item.get('label')}): {item.get('detail')} · lanes: `{lanes}`")
            elif item.get("comparison_id"):
                lines.append(f"- **{item.get('comparison_id')}**: {item.get('detail')}")
            elif item.get("mapping_id"):
                lanes = ", ".join(item.get("lanes_touched") or [])
                lines.append(f"- **{item.get('mapping_id')}** → `{lanes}`: {item.get('detail')}")
            elif item.get("approval_id"):
                lines.append(f"- approval `{item.get('approval_id')}` gate={item.get('gate_id')}: {item.get('detail', 'human review required')}")
            elif item.get("tradeoff_id"):
                lines.append(f"- tradeoff `{item.get('tradeoff_id')}`: {item.get('detail')}")
            elif item.get("risk_id"):
                lines.append(f"- risk `{item.get('risk_id')}`: {item.get('detail') or item.get('blocked_by')}")
            elif item.get("path_id"):
                lines.append(f"- **do not do** `{item.get('path_id')}`: {item.get('detail')}")
            elif item.get("sequence_step") is not None:
                lines.append(f"- step {item.get('sequence_step')}: {item.get('recommendation')}")
            elif item.get("artifact_id"):
                lines.append(
                    f"- **{item.get('artifact_id')}**: options={item.get('action_option_count')} "
                    f"approvals={item.get('required_approval_count')} tradeoffs={item.get('constitutional_tradeoff_count')} "
                    f"risks={item.get('risk_blocker_count')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All planning outputs are `executable: false` — humans govern lane selection and execution._")
    return "\n".join(lines)
