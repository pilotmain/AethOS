# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — Markdown renderer for governed lane readiness board."""

from __future__ import annotations

from typing import Any


def render_governed_lane_readiness_board(governed_lane_readiness_board: dict[str, Any]) -> str:
    sections = governed_lane_readiness_board.get("sections") or {}

    lines = [
        "# Governed Lane Readiness Board (FIX 175 — board ≠ admission decision)",
        "",
        f"- session_id: `{governed_lane_readiness_board.get('session_id', '')}`",
        f"- board records: **{governed_lane_readiness_board.get('lane_readiness_board_record_count', 0)}**",
        f"- board candidates: **{governed_lane_readiness_board.get('board_candidate_count', 0)}**",
        f"- blocked lanes: **{governed_lane_readiness_board.get('blocked_lane_count', 0)}**",
        f"- board tier: `{governed_lane_readiness_board.get('board_tier') or 'none'}`",
        f"- board ready: **{governed_lane_readiness_board.get('board_ready', False)}**",
        f"- lane admission decision performed: **{governed_lane_readiness_board.get('lane_admission_decision_performed', False)}** _(always false)_",
        f"- composes FIX 174: **{governed_lane_readiness_board.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        governed_lane_readiness_board.get("invariant", ""),
        "",
        "_Consolidates lane recommendation for human review — FIX 176 decides admission._",
        "",
    ]

    for title, key in (
        ("Lane recommendation upstream read (FIX 174)", "lane_recommendation_upstream_read"),
        ("Authorization envelope status (FIX 170)", "authorization_envelope_status"),
        ("Recommended lane candidates", "recommended_lane_candidates_board"),
        ("Blocked lanes", "blocked_lanes_board"),
        ("Required gates", "required_gates_board"),
        ("Missing prerequisites", "missing_prerequisites_board"),
        ("Escalation requirements", "escalation_requirements_board"),
        ("Risk / blast radius summary", "risk_blast_radius_summary"),
        ("Lane readiness board packet", "lane_readiness_board_packet"),
        ("Forbidden board actions", "forbidden_board_actions"),
        ("Next-step lane readiness board sequence", "next_step_lane_readiness_board_sequence"),
        ("Lane readiness board integrity scoring", "lane_readiness_board_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("packet_id"):
                lines.append(
                    f"- **{item.get('packet_id')}**: candidates={item.get('candidate_count')} "
                    f"blocked={item.get('blocked_lane_count')} tier={item.get('authorization_tier')}"
                )
            elif item.get("board_row_id") and item.get("recommended_gate"):
                lines.append(
                    f"- **{item.get('board_row_id')}**: lane={item.get('recommended_lane')} "
                    f"gate={item.get('recommended_gate')} status={item.get('recommendation_status')}"
                )
            elif item.get("board_row_id") and item.get("gate_id"):
                lines.append(f"- gate `{item.get('gate_id')}`: {item.get('detail')}")
            elif item.get("summary_id"):
                lines.append(
                    f"- **{item.get('summary_id')}**: risk={item.get('risk_label')} "
                    f"blast={item.get('blast_radius_ceiling')}"
                )
            elif item.get("status_id"):
                lines.append(
                    f"- **{item.get('status_id')}**: tier={item.get('authorization_tier')} "
                    f"lanes={item.get('allowed_lane_count')}"
                )
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

    lines.append("_Lane readiness board ≠ lane admission decision — human decides in FIX 176._")
    return "\n".join(lines)
