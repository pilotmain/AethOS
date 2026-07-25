# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — Markdown renderer for frozen gate intake preview."""

from __future__ import annotations

from typing import Any


def render_frozen_gate_intake_preview(frozen_gate_intake_preview: dict[str, Any]) -> str:
    sections = frozen_gate_intake_preview.get("sections") or {}

    lines = [
        "# Frozen Gate Intake Preview (FIX 178 — intake preview ≠ gate execution)",
        "",
        f"- session_id: `{frozen_gate_intake_preview.get('session_id', '')}`",
        f"- intake preview records: **{frozen_gate_intake_preview.get('intake_preview_record_count', 0)}**",
        f"- target gate: `{frozen_gate_intake_preview.get('target_gate_id') or 'none'}`",
        f"- intake preview tier: `{frozen_gate_intake_preview.get('intake_preview_tier') or 'none'}`",
        f"- intake preview ready: **{frozen_gate_intake_preview.get('intake_preview_ready', False)}**",
        f"- gate execution performed: **{frozen_gate_intake_preview.get('gate_execution_performed', False)}** _(always false)_",
        f"- lane entry execution performed: **{frozen_gate_intake_preview.get('lane_entry_execution_performed', False)}** _(always false)_",
        f"- composes FIX 177: **{frozen_gate_intake_preview.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        frozen_gate_intake_preview.get("invariant", ""),
        "",
        "_Frozen gate receives handoff preview — gate execution remains in governed lane._",
        "",
    ]

    for title, key in (
        ("Handoff upstream read (FIX 177)", "handoff_upstream_read"),
        ("Matching frozen gate identification", "matching_frozen_gate_identification"),
        ("Intake preview packet", "intake_preview_packet"),
        ("Packet shape validation", "packet_shape_validation"),
        ("Required existing commands", "required_existing_commands"),
        ("Missing gate prerequisites", "missing_gate_prerequisites"),
        ("Lane entry confirmation", "lane_entry_confirmation"),
        ("Forbidden intake actions", "forbidden_intake_actions"),
        ("Next-step intake sequence", "next_step_intake_sequence"),
        ("Intake integrity scoring", "intake_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("preview_id"):
                lines.append(
                    f"- **{item.get('preview_id')}**: gate=`{item.get('target_gate_id')}` "
                    f"ready={item.get('intake_preview_ready')} decision={item.get('decision_value')}"
                )
            elif item.get("match_id") and item.get("gate_id"):
                lines.append(f"- gate `{item.get('gate_id')}` frozen={item.get('frozen_software_delivery_gate')}")
            elif item.get("validation_id"):
                lines.append(
                    f"- validation `{item.get('validation_id')}`: valid={item.get('valid')} "
                    f"{item.get('detail')}"
                )
            elif item.get("prerequisite_id"):
                satisfied = item.get("satisfied")
                suffix = f" satisfied={satisfied}" if satisfied is not None else ""
                lines.append(f"- prerequisite `{item.get('prerequisite_id')}`{suffix}: {item.get('detail')}")
            elif item.get("command_id"):
                lines.append(f"- command `{item.get('command_id')}`: `{item.get('command_hint')}`")
            elif item.get("confirmation_id"):
                lines.append(f"- **{item.get('confirmation_id')}**: {item.get('detail')}")
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

    lines.append("_Gate intake preview ≠ gate execution — frozen lane decides execution._")
    return "\n".join(lines)
