# SPDX-License-Identifier: Apache-2.0
"""FIX 176 — Markdown renderer for human lane admission decision."""

from __future__ import annotations

from typing import Any


def render_human_lane_admission_decision(human_lane_admission_decision: dict[str, Any]) -> str:
    sections = human_lane_admission_decision.get("sections") or {}

    lines = [
        "# Human Lane Admission Decision (FIX 176 — decision ≠ lane entry execution)",
        "",
        f"- session_id: `{human_lane_admission_decision.get('session_id', '')}`",
        f"- decision records: **{human_lane_admission_decision.get('human_lane_admission_decision_record_count', 0)}**",
        f"- human decision recorded: **{human_lane_admission_decision.get('human_decision_recorded', False)}**",
        f"- decision tier: `{human_lane_admission_decision.get('decision_tier') or 'none'}`",
        f"- decision ready: **{human_lane_admission_decision.get('decision_ready', False)}**",
        f"- lane entry execution performed: **{human_lane_admission_decision.get('lane_entry_execution_performed', False)}** _(always false)_",
        f"- lane admission executed: **{human_lane_admission_decision.get('lane_admission_executed', False)}** _(always false)_",
        f"- composes FIX 175: **{human_lane_admission_decision.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        human_lane_admission_decision.get("invariant", ""),
        "",
        "_Human records admit, hold, or reject — FIX 177 performs gate-routed handoff._",
        "",
    ]

    for title, key in (
        ("Lane readiness board upstream read (FIX 175)", "lane_readiness_board_upstream_read"),
        ("Selected lane admission decision", "selected_lane_admission_decision"),
        ("Decision rationale", "decision_rationale"),
        ("Accepted risks / tradeoffs", "accepted_risks_tradeoffs"),
        ("Rejected lane candidates", "rejected_lane_candidates"),
        ("Acknowledged remaining blockers", "acknowledged_remaining_blockers"),
        ("Lane admission decision packet", "lane_admission_decision_packet"),
        ("Forbidden decision actions", "forbidden_decision_actions"),
        ("Next-step admission decision sequence", "next_step_admission_decision_sequence"),
        ("Decision integrity scoring", "decision_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("packet_id"):
                lines.append(
                    f"- **{item.get('packet_id')}**: decision={item.get('decision_value')} "
                    f"recorded={item.get('human_decision_recorded')}"
                )
            elif item.get("decision_id"):
                lines.append(
                    f"- **{item.get('decision_id')}**: value={item.get('decision_value')} "
                    f"by={item.get('decided_by')}"
                )
            elif item.get("read_id"):
                lines.append(f"- **{item.get('read_id')}** ({item.get('upstream_fix')})")
            elif item.get("rejection_id"):
                lines.append(f"- rejected `{item.get('rejection_id')}`: {item.get('detail')}")
            elif item.get("acknowledgment_id"):
                lines.append(f"- blocker `{item.get('acknowledgment_id')}`: {item.get('detail')}")
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

    lines.append("_Human lane admission decision ≠ lane entry execution — gates decide execution._")
    return "\n".join(lines)
