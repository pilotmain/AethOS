# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — Markdown renderer for mission authorization."""

from __future__ import annotations

from typing import Any


def render_mission_authorization(mission_authorization: dict[str, Any]) -> str:
    sections = mission_authorization.get("sections") or {}

    lines = [
        "# Mission Authorization (FIX 170 — bounded work envelope)",
        "",
        f"- session_id: `{mission_authorization.get('session_id', '')}`",
        f"- authorization records: **{mission_authorization.get('authorization_record_count', 0)}**",
        f"- selected path: `{mission_authorization.get('selected_path_id') or 'pending'}`",
        f"- allowed lanes: **{mission_authorization.get('allowed_lane_count', 0)}**",
        f"- authorization tier: `{mission_authorization.get('authorization_tier') or 'none'}`",
        f"- gate bypass: **{mission_authorization.get('gate_bypass_enabled', False)}** _(always false)_",
        f"- tier escalation: **{mission_authorization.get('tier_escalation_enabled', False)}** _(always false)_",
        "",
        mission_authorization.get("invariant", ""),
        "",
        "_Bounded envelope reduces approval repetition — existing gates still enforce boundaries._",
        "",
    ]

    for title, key in (
        ("Human decision read", "human_decision_read"),
        ("Bounded work envelope", "bounded_work_envelope"),
        ("Envelope validation", "envelope_validation"),
        ("Existing gate checks", "existing_gate_checks"),
        ("Tier boundary enforcement", "tier_boundary_enforcement"),
        ("Re-engagement triggers", "reengagement_triggers"),
        ("Forbidden authorization actions", "forbidden_authorization_actions"),
        ("Next-step authorization sequence", "next_step_authorization_sequence"),
        ("Authorization integrity scoring", "authorization_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("envelope_id"):
                lanes = ", ".join(item.get("allowed_lanes") or []) or "none"
                lines.append(
                    f"- **{item.get('envelope_id')}**: lanes=`{lanes}` tier={item.get('authorization_tier')} "
                    f"bypass={item.get('gate_bypass')}"
                )
            elif item.get("validation_id"):
                lines.append(f"- validation `{item.get('validation_id')}`: status={item.get('status')}")
            elif item.get("gate_check_id"):
                lines.append(f"- gate `{item.get('gate_check_id')}`: bypass={item.get('gate_bypass', False)}")
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

    lines.append("_Mission authorization ≠ gate bypass — humans re-engage only on escalation._")
    return "\n".join(lines)
