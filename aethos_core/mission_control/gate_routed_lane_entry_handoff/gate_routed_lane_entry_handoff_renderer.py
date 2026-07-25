# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — Markdown renderer for gate-routed lane entry handoff."""

from __future__ import annotations

from typing import Any


def render_gate_routed_lane_entry_handoff(gate_routed_lane_entry_handoff: dict[str, Any]) -> str:
    sections = gate_routed_lane_entry_handoff.get("sections") or {}

    lines = [
        "# Gate-Routed Lane Entry Handoff (FIX 177 — handoff ≠ lane entry execution)",
        "",
        f"- session_id: `{gate_routed_lane_entry_handoff.get('session_id', '')}`",
        f"- handoff records: **{gate_routed_lane_entry_handoff.get('gate_handoff_record_count', 0)}**",
        f"- target gate: `{gate_routed_lane_entry_handoff.get('target_gate_id') or 'none'}`",
        f"- handoff tier: `{gate_routed_lane_entry_handoff.get('handoff_tier') or 'none'}`",
        f"- handoff ready: **{gate_routed_lane_entry_handoff.get('handoff_ready', False)}**",
        f"- lane entry execution performed: **{gate_routed_lane_entry_handoff.get('lane_entry_execution_performed', False)}** _(always false)_",
        f"- composes FIX 176: **{gate_routed_lane_entry_handoff.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        gate_routed_lane_entry_handoff.get("invariant", ""),
        "",
        "_Handoff delivers packet to frozen gate — gate validates and decides lane entry._",
        "",
    ]

    for title, key in (
        ("Human decision upstream read (FIX 176)", "human_decision_upstream_read"),
        ("Target frozen gate identification", "target_frozen_gate_identification"),
        ("Decision rationale in handoff", "decision_rationale_in_handoff"),
        ("Accepted risks in handoff", "accepted_risks_in_handoff"),
        ("Remaining blockers in handoff", "remaining_blockers_in_handoff"),
        ("Gate validation requirements", "gate_validation_requirements"),
        ("Required next commands", "required_next_commands"),
        ("Gate handoff packet", "gate_handoff_packet"),
        ("Forbidden handoff actions", "forbidden_handoff_actions"),
        ("Next-step handoff sequence", "next_step_handoff_sequence"),
        ("Handoff integrity scoring", "handoff_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("packet_id"):
                lines.append(
                    f"- **{item.get('packet_id')}**: gate=`{item.get('target_gate_id')}` "
                    f"ready={item.get('handoff_ready')} decision={item.get('decision_value')}"
                )
            elif item.get("identification_id") and item.get("gate_id"):
                lines.append(f"- gate `{item.get('gate_id')}` frozen={item.get('frozen_software_delivery_gate')}")
            elif item.get("requirement_id"):
                lines.append(f"- validation `{item.get('requirement_id')}`: {item.get('detail')}")
            elif item.get("command_id"):
                lines.append(f"- command `{item.get('command_id')}`: `{item.get('command_hint')}`")
            elif item.get("read_id"):
                lines.append(f"- **{item.get('read_id')}** ({item.get('upstream_fix')})")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} "
                    f"composes_upstream={item.get('composes_upstream_layers')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Gate-routed handoff ≠ lane entry execution — frozen gate decides._")
    return "\n".join(lines)
