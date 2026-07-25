# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — Markdown renderer for bounded execution participation."""

from __future__ import annotations

from typing import Any


def render_bounded_execution_participation(bounded_execution_participation: dict[str, Any]) -> str:
    sections = bounded_execution_participation.get("sections") or {}

    lines = [
        "# Bounded Execution Participation (FIX 171 — envelope-scoped agent coordination)",
        "",
        f"- session_id: `{bounded_execution_participation.get('session_id', '')}`",
        f"- participation records: **{bounded_execution_participation.get('participation_record_count', 0)}**",
        f"- selected path: `{bounded_execution_participation.get('selected_path_id') or 'pending'}`",
        f"- allowed lanes: **{bounded_execution_participation.get('allowed_lane_count', 0)}**",
        f"- participation tier: `{bounded_execution_participation.get('participation_tier') or 'none'}`",
        f"- participation ready: **{bounded_execution_participation.get('participation_ready', False)}**",
        f"- autonomous lane entry: **{bounded_execution_participation.get('autonomous_lane_entry_enabled', False)}** _(always false)_",
        f"- gate bypass: **{bounded_execution_participation.get('gate_bypass_enabled', False)}** _(always false)_",
        "",
        bounded_execution_participation.get("invariant", ""),
        "",
        "_Agents participate inside the authorized envelope — existing gates still enforce boundaries._",
        "",
    ]

    for title, key in (
        ("Authorization envelope read", "authorization_envelope_read"),
        ("Participation scope", "participation_scope"),
        ("Gate-routed participation", "gate_routed_participation"),
        ("Tier boundary enforcement", "tier_boundary_enforcement"),
        ("Forbidden participation actions", "forbidden_participation_actions"),
        ("Re-engagement triggers", "reengagement_triggers"),
        ("Next-step participation sequence", "next_step_participation_sequence"),
        ("Participation integrity scoring", "participation_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("scope_id"):
                lanes = ", ".join(item.get("allowed_lanes") or []) or item.get("lane") or "none"
                lines.append(
                    f"- **{item.get('scope_id')}**: lanes=`{lanes}` autonomous_entry={item.get('autonomous_lane_entry')}"
                )
            elif item.get("read_id"):
                lines.append(
                    f"- **{item.get('read_id')}**: ready={item.get('participation_ready')} tier={item.get('authorization_tier')}"
                )
            elif item.get("participation_action_id"):
                lines.append(
                    f"- action `{item.get('participation_action_id')}`: bypass={item.get('gate_bypass', False)}"
                )
            elif item.get("boundary_id"):
                lines.append(f"- **{item.get('boundary_id')}**: {item.get('detail')}")
            elif item.get("trigger_id"):
                lines.append(
                    f"- trigger `{item.get('trigger_id')}`: reengagement={item.get('reengagement_required')}"
                )
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} label={item.get('integrity_label')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Bounded execution participation ≠ autonomous execution — humans re-engage only on escalation._")
    return "\n".join(lines)
