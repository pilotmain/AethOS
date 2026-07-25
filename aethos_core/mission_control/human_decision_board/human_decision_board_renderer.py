# SPDX-License-Identifier: Apache-2.0
"""FIX 166 — Markdown renderer for human decision board."""

from __future__ import annotations

from typing import Any


def render_human_decision_board(human_decision_board: dict[str, Any]) -> str:
    sections = human_decision_board.get("sections") or {}

    lines = [
        "# Human Decision Board + Action Selection (FIX 166 — human choice only)",
        "",
        f"- session_id: `{human_decision_board.get('session_id', '')}`",
        f"- decision records: **{human_decision_board.get('decision_record_count', 0)}**",
        f"- candidate actions: **{human_decision_board.get('candidate_count', 0)}**",
        f"- autonomous selection: **{human_decision_board.get('autonomous_selection_enabled', False)}** _(always false)_",
        f"- autonomous execution: **{human_decision_board.get('autonomous_execution_enabled', False)}** _(always false)_",
        "",
        human_decision_board.get("invariant", ""),
        "",
        "_Human decision board — records human choice only, never autonomous selection or execution._",
        "",
    ]

    for title, key in (
        ("Candidate action board", "candidate_action_board"),
        ("Human selection record", "human_selection_record"),
        ("Rejected paths analysis", "rejected_paths_analysis"),
        ("Decision rationale capture", "decision_rationale_capture"),
        ("Accepted tradeoffs and risks", "accepted_tradeoffs_and_risks"),
        ("Decision traceability", "decision_traceability"),
        ("Decision review package", "decision_review_package"),
        ("Decision integrity scoring", "decision_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("candidate_label") and item.get("option_id"):
                lanes = ", ".join(item.get("lanes_touched") or []) or "none"
                lines.append(
                    f"- **{item.get('candidate_label')}** `{item.get('option_id')}` ({item.get('label')}): {item.get('detail')} · lanes: `{lanes}`"
                )
            elif item.get("selection_id"):
                lines.append(
                    f"- selection `{item.get('selection_id')}`: {item.get('selected_path') or item.get('detail')} "
                    f"by `{item.get('selected_by') or 'pending'}`"
                )
            elif item.get("rejection_id"):
                lines.append(f"- rejected `{item.get('rejection_id')}`: {item.get('content') or item.get('detail')}")
            elif item.get("trace_id"):
                agents = ", ".join(item.get("agents_participated") or [])
                lines.append(
                    f"- **{item.get('trace_id')}**: selected_by={item.get('selected_by')} "
                    f"agents=[{agents}] records={item.get('decision_record_count')}"
                )
            elif item.get("package_id"):
                lines.append(
                    f"- **{item.get('package_id')}**: decision={item.get('decision_artifact_count')} "
                    f"approval={item.get('approval_artifact_count')} handoff={item.get('execution_handoff_artifact_count')}"
                )
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} label={item.get('integrity_label')}"
                )
            elif item.get("artifact_type"):
                lines.append(f"- artifact `{item.get('artifact_type')}`: {item.get('content') or item.get('selected_path') or item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Human selection is a first-class institutional artifact — AethOS records choice, never makes it._")
    return "\n".join(lines)
