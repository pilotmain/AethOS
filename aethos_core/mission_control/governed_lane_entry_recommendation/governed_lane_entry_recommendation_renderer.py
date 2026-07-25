# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — Markdown renderer for governed lane entry recommendation."""

from __future__ import annotations

from typing import Any


def render_governed_lane_entry_recommendation(governed_lane_entry_recommendation: dict[str, Any]) -> str:
    sections = governed_lane_entry_recommendation.get("sections") or {}

    lines = [
        "# Governed Lane Entry Recommendation (FIX 174 — recommendation ≠ admission)",
        "",
        f"- session_id: `{governed_lane_entry_recommendation.get('session_id', '')}`",
        f"- lane recommendation records: **{governed_lane_entry_recommendation.get('lane_recommendation_record_count', 0)}**",
        f"- lane entry candidates: **{governed_lane_entry_recommendation.get('lane_entry_candidate_count', 0)}**",
        f"- eligible entries: **{governed_lane_entry_recommendation.get('eligible_lane_entry_count', 0)}**",
        f"- recommendation tier: `{governed_lane_entry_recommendation.get('recommendation_tier') or 'none'}`",
        f"- recommendation ready: **{governed_lane_entry_recommendation.get('recommendation_ready', False)}**",
        f"- lane admission performed: **{governed_lane_entry_recommendation.get('lane_admission_performed', False)}** _(always false)_",
        f"- composes FIX 169 + FIX 173: **{governed_lane_entry_recommendation.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        governed_lane_entry_recommendation.get("invariant", ""),
        "",
        "_Composes upstream readiness and gate review — frozen gates decide admission._",
        "",
    ]

    for title, key in (
        ("Readiness upstream read (FIX 169)", "readiness_upstream_read"),
        ("Gate review upstream read (FIX 173)", "gate_review_upstream_read"),
        ("Lane entry candidates", "lane_entry_candidates"),
        ("Eligibility rationale", "eligibility_rationale"),
        ("Blocked lane explanations", "blocked_lane_explanations"),
        ("Missing prerequisites (references)", "missing_prerequisites_references"),
        ("Escalation requirements", "escalation_requirements"),
        ("Recommended next gate", "recommended_next_gate"),
        ("Forbidden recommendation actions", "forbidden_lane_recommendation_actions"),
        ("Next-step lane recommendation sequence", "next_step_lane_recommendation_sequence"),
        ("Lane recommendation integrity scoring", "lane_recommendation_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("candidate_id"):
                lines.append(
                    f"- **{item.get('candidate_id')}**: gate=`{item.get('recommended_gate')}` "
                    f"status={item.get('recommendation_status')} admission={item.get('lane_admission_performed', False)}"
                )
            elif item.get("rationale_id"):
                lines.append(f"- rationale `{item.get('rationale_id')}`: {item.get('detail')}")
            elif item.get("explanation_id"):
                lines.append(f"- blocked `{item.get('explanation_id')}` ({item.get('upstream_fix')}): {item.get('detail')}")
            elif item.get("reference_id"):
                missing = item.get("missing_prerequisites")
                if missing:
                    lines.append(f"- prereq ref `{item.get('reference_id')}`: missing={missing}")
                else:
                    lines.append(f"- {item.get('detail')}")
            elif item.get("gate_id") and item.get("detail"):
                lines.append(f"- next gate `{item.get('gate_id')}`: {item.get('detail')}")
            elif item.get("read_id"):
                lines.append(f"- **{item.get('read_id')}** ({item.get('upstream_fix')})")
            elif item.get("requirement_id") or item.get("trigger_id"):
                rid = item.get("requirement_id") or item.get("trigger_id")
                lines.append(f"- escalation `{rid}`")
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

    lines.append("_Lane recommendation ≠ lane admission — human and frozen gates decide._")
    return "\n".join(lines)
