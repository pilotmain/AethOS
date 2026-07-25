# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — Markdown renderer for operator contextual guidance."""

from __future__ import annotations

from typing import Any


_SECTION_TITLES = {
    "likely_next_governed_steps": "Likely next governed steps",
    "historical_mitigations": "Historical mitigations",
    "recurring_blocker_resolutions": "Recurring blocker resolutions",
    "relevant_incidents_and_prs": "Relevant incidents & PRs",
    "rollout_caution": "Rollout caution",
    "verification_gaps": "Verification gaps",
    "approval_sequencing": "Approval sequencing",
    "replay_and_rerun_review_targets": "Replay & rerun review targets",
}


def render_operator_guidance(guidance: dict[str, Any]) -> str:
    lines = [
        "# Operator Contextual Guidance (FIX 142 — copiloting only)",
        "",
        f"- session_id: `{guidance.get('session_id', '')}`",
        f"- plan_id: `{guidance.get('plan_id') or 'none'}`",
        f"- recommendations: **{guidance.get('recommendation_count', 0)}**",
        f"- all executable: **{guidance.get('all_recommendations_executable', False)}** _(always false)_",
        f"- operator approval required: **{guidance.get('operator_approval_required_for_all', True)}**",
        "",
        guidance.get("invariant", ""),
        "",
        "_Operational copiloting — not autonomous operation. No auto-planning or execution._",
        "",
    ]
    sections = guidance.get("sections") or {}
    for key, title in _SECTION_TITLES.items():
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_No guidance in this section._")
        for item in items:
            pri = item.get("priority", "medium")
            lines.append(f"- **[{pri}]** {item.get('guidance', '')}")
            if item.get("rationale"):
                lines.append(f"  - _{item.get('rationale')}_")
            if item.get("suggested_phrase"):
                lines.append(f"  - phrase (non-executable): `{item.get('suggested_phrase')}`")
        lines.append("")

    lines.append("_All items are `executable: false` — operator must approve and invoke governed chat routes._")
    return "\n".join(lines)
