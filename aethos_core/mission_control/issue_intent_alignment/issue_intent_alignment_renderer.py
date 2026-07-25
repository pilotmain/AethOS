# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — Markdown renderer for issue intent alignment."""

from __future__ import annotations

from typing import Any


def render_issue_intent_alignment(issue_intent_alignment: dict[str, Any]) -> str:
    sections = issue_intent_alignment.get("sections") or {}

    lines = [
        "# Issue Intent Alignment & Patch Target Validation (FIX 184 — validation ≠ patch execution)",
        "",
        f"- session_id: `{issue_intent_alignment.get('session_id', '')}`",
        f"- repo/issue: `{issue_intent_alignment.get('repo_issue') or 'none'}`",
        f"- alignment score: **{issue_intent_alignment.get('alignment_score', 0)}** _(advisory)_",
        f"- target validation: **{issue_intent_alignment.get('target_validation_status', 'none')}**",
        f"- escalation required: **{issue_intent_alignment.get('escalation_required', False)}**",
        f"- gate satisfied: **{issue_intent_alignment.get('intent_alignment_gate_satisfied', False)}**",
        f"- patch execution performed: **{issue_intent_alignment.get('patch_execution_performed', False)}** _(always false)_",
        "",
        issue_intent_alignment.get("invariant", ""),
        "",
        "_Alignment validation is advisory — operator re-engagement required on escalation._",
        "",
    ]

    for title, key in (
        ("Issue scope extraction", "issue_scope_extraction"),
        ("Patch target validation", "patch_target_validation"),
        ("Patch purpose validation", "patch_purpose_validation"),
        ("Authorization envelope validation", "authorization_envelope_validation"),
        ("Unrelated change detection", "unrelated_change_detection"),
        ("Alignment assessment", "alignment_assessment"),
        ("Misalignment findings", "misalignment_findings"),
        ("Escalation rules", "escalation_rules"),
        ("Recommended review", "recommended_review"),
        ("Forbidden alignment actions", "forbidden_alignment_actions"),
        ("Alignment integrity scoring", "alignment_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("assessment_id"):
                lines.append(
                    f"- score **{item.get('alignment_score')}** / threshold {item.get('alignment_threshold')}: "
                    f"{item.get('rationale')}"
                )
            elif item.get("validation_id"):
                lines.append(f"- `{item.get('validation_id')}`: {item}")
            elif item.get("extraction_id"):
                lines.append(f"- expected targets: {', '.join(item.get('expected_targets') or []) or 'none'}")
                lines.append(f"- subsystem: `{item.get('intended_subsystem')}` blast: `{item.get('expected_blast_radius')}`")
            elif item.get("finding_id"):
                lines.append(f"- `{item.get('finding_id')}`: {item.get('detail') or item.get('path')}")
            elif item.get("rule_id"):
                lines.append(f"- escalation: {item.get('escalation_required')} reasons={item.get('escalation_reasons')}")
            elif item.get("review_id"):
                lines.append(f"- {item.get('guidance')}")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_FIX 184 answers: are we changing the correct thing? — before patch proceeds._")
    return "\n".join(lines)
