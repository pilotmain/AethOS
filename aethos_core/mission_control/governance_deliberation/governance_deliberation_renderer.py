# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — Markdown renderer for governance deliberation workspace."""

from __future__ import annotations

from typing import Any

_SECTION_TITLES = {
    "operator_notes": "Operator notes",
    "reviewer_annotations": "Reviewer annotations",
    "structured_concerns": "Structured concerns",
    "dissent_tracking": "Dissent tracking",
    "rationale_capture": "Rationale capture",
    "alternative_path_comparison": "Alternative-path comparison",
    "review_checklist": "Review checklist",
    "approval_rejection_rationale": "Why was this approved/rejected?",
    "decision_justification_records": "Decision justification records",
}


def _render_records(items: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not items:
        lines.append("_None recorded._")
        return lines
    for item in items:
        if item.get("path"):
            suffix = " _(advisory alignment)_" if item.get("advisory_alignment") else ""
            lines.append(f"- **{item.get('path')}**: {item.get('description', '')}{suffix}")
        elif item.get("checklist_key"):
            mark = "x" if item.get("checked") else " "
            lines.append(f"- [{mark}] {item.get('label')}")
            if item.get("note"):
                lines.append(f"  - _{item.get('note')}_")
        else:
            author = item.get("author") or "operator"
            lines.append(f"- **{author}** ({item.get('kind', item.get('recorded_at', ''))}): {item.get('content', '')}")
    return lines


def render_governance_deliberation(workspace: dict[str, Any]) -> str:
    sections = workspace.get("sections") or {}
    ctx = sections.get("readiness_review_context") or {}

    lines = [
        "# Governance Deliberation Workspace (FIX 148 — institutional memory, no approval automation)",
        "",
        f"- session_id: `{workspace.get('session_id', '')}`",
        f"- plan_id: `{workspace.get('plan_id') or '—'}`",
        f"- deliberation records: **{workspace.get('deliberation_record_count', 0)}**",
        f"- governance mutation: **{workspace.get('governance_mutation_performed', False)}** _(always false)_",
        f"- automatic approval: **{workspace.get('automatic_approval_enabled', False)}** _(always false)_",
        "",
        workspace.get("invariant", ""),
        "",
        "_Collaborative decision reasoning — operator retains governance authority._",
        "",
        "## Readiness review context",
        "",
        f"- go/no-go/hold advisory: **{ctx.get('go_no_go_hold', '—')}**",
        f"- blockers: {ctx.get('blocker_count', 0)} · pending approvals: {ctx.get('pending_approval_count', 0)}",
        "",
    ]

    timeline = sections.get("governance_discussion_timeline") or []
    lines.extend(["## Governance discussion timeline", ""])
    lines.extend(_render_records(timeline))
    lines.append("")

    for key, title in _SECTION_TITLES.items():
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        lines.extend(_render_records(items if isinstance(items, list) else []))
        lines.append("")

    lines.append(
        "_Deliberation records persist institutional governance memory only — they do not approve, reject, or mutate policy._"
    )
    return "\n".join(lines)
