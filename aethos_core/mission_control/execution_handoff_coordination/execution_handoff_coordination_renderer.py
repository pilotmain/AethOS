# SPDX-License-Identifier: Apache-2.0
"""FIX 167 — Markdown renderer for execution handoff coordination."""

from __future__ import annotations

from typing import Any


def render_execution_handoff_coordination(execution_handoff_coordination: dict[str, Any]) -> str:
    sections = execution_handoff_coordination.get("sections") or {}

    lines = [
        "# Governed Execution Handoff Coordination (FIX 167 — handoff cognition)",
        "",
        f"- session_id: `{execution_handoff_coordination.get('session_id', '')}`",
        f"- handoff records: **{execution_handoff_coordination.get('handoff_record_count', 0)}**",
        f"- selected path: `{execution_handoff_coordination.get('selected_path_id') or 'pending'}`",
        f"- eligible lanes: **{execution_handoff_coordination.get('eligible_lane_count', 0)}**",
        f"- autonomous execution: **{execution_handoff_coordination.get('autonomous_execution_enabled', False)}** _(always false)_",
        f"- autonomous lane entry: **{execution_handoff_coordination.get('autonomous_lane_entry_enabled', False)}** _(always false)_",
        "",
        execution_handoff_coordination.get("invariant", ""),
        "",
        "_Handoff coordination — connects human decision to governed lanes, never executes._",
        "",
    ]

    for title, key in (
        ("Selected human decision read", "selected_human_decision_read"),
        ("Eligible lane mapping", "eligible_lane_mapping"),
        ("Execution handoff package", "execution_handoff_package"),
        ("Required lane gates", "required_lane_gates"),
        ("Required approvals", "required_approvals"),
        ("Remaining blockers", "remaining_blockers"),
        ("Forbidden actions", "forbidden_actions"),
        ("Next-step command sequence", "next_step_command_sequence"),
        ("Handoff integrity scoring", "handoff_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("selected_path_id"):
                lines.append(
                    f"- **{item.get('read_id')}**: path=`{item.get('selected_path_id')}` "
                    f"by `{item.get('selected_by') or 'pending'}` ready={item.get('handoff_ready')}"
                )
            elif item.get("mapping_id"):
                lanes = ", ".join(item.get("eligible_lanes") or []) or "none"
                lines.append(f"- **{item.get('mapping_id')}** → lanes: `{lanes}`")
            elif item.get("package_id"):
                lines.append(f"- **{item.get('package_id')}**: {item.get('detail')}")
            elif item.get("gate_id"):
                lines.append(f"- gate `{item.get('gate_id')}` lane={item.get('lane')}: {item.get('detail', item.get('status', ''))}")
            elif item.get("approval_id"):
                lines.append(f"- approval `{item.get('approval_id')}`: {item.get('detail', 'human review required')}")
            elif item.get("blocker_id"):
                lines.append(f"- blocker `{item.get('blocker_id')}`: {item.get('detail') or item.get('blocked_by')}")
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

    lines.append("_Handoff coordination ≠ execution authority — humans enter governed lanes with explicit approval._")
    return "\n".join(lines)
