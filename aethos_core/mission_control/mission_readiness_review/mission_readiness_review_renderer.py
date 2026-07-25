# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — Markdown renderer for mission readiness review board."""

from __future__ import annotations

from typing import Any


def render_mission_readiness_review(review: dict[str, Any]) -> str:
    sections = review.get("sections") or {}
    go_rec = sections.get("go_no_go_hold_recommendation") or {}
    score = sections.get("readiness_score_summary") or {}

    lines = [
        "# Mission Readiness Review Board (FIX 147 — advisory only, human review required)",
        "",
        f"- session_id: `{review.get('session_id', '')}`",
        f"- plan_id: `{review.get('plan_id') or '—'}`",
        f"- correlation_id: `{review.get('correlation_id') or '—'}`",
        f"- human_review_required: **{review.get('human_review_required', True)}**",
        f"- execution_authority_delegated: **{review.get('execution_authority_delegated', False)}** _(always false)_",
        "",
        review.get("invariant", ""),
        "",
        "_Bridge between mission state cognition and operator governance decision — no execution authority._",
        "",
        "## Go / no-go / hold recommendation (advisory)",
        "",
        f"- recommendation: **{go_rec.get('recommendation', '—')}**",
        f"- rationale: {go_rec.get('rationale', '')}",
        f"- readiness_score: {go_rec.get('readiness_score', '—')}",
        f"- pending_approvals: {go_rec.get('pending_approval_count', 0)} · blockers: {go_rec.get('blocker_count', 0)}",
        "",
        "## Readiness score summary",
        "",
        f"- score: **{score.get('readiness_score', '—')}** ({score.get('readiness_label', '')})",
        f"- cross-lane overall: {score.get('cross_lane_overall', '—')}",
        f"- factors: {score.get('factors', {})}",
        "",
    ]

    for title, key in (
        ("Blockers", "blockers"),
        ("Pending approvals", "pending_approvals"),
        ("Evidence gaps", "evidence_gaps"),
        ("Recommended operator decisions", "recommended_operator_decisions"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None identified._")
        for item in items:
            if item.get("decision"):
                lines.append(f"- **{item.get('kind', 'decision')}**: {item.get('decision')}")
                if item.get("rationale"):
                    lines.append(f"  - _{item.get('rationale')}_")
            elif item.get("blocked_by"):
                lines.append(
                    f"- `{item.get('blocked_entity')}` blocked by **{item.get('blocked_by')}** "
                    f"({item.get('priority', 'medium')})"
                )
            elif item.get("gate_id"):
                lines.append(
                    f"- gate `{item.get('gate_id')}` — severity {item.get('severity')} "
                    f"(ui_eligible={item.get('ui_approval_eligible')})"
                )
            elif item.get("gap"):
                lines.append(f"- [{item.get('severity', '—')}] {item.get('gap')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    rollback = sections.get("rollback_posture") or {}
    lines.extend(
        [
            "## Rollback posture",
            "",
            f"- workspace rollback: {rollback.get('workspace_rollback', '—')}",
            f"- autonomous rollback: **{rollback.get('autonomous_rollback', 'forbidden')}**",
            f"- snapshot required: {rollback.get('snapshot_required', '—')}",
            f"- escalation signals: {rollback.get('rollback_escalation_signals', 0)}",
            "",
        ]
    )
    for row in rollback.get("rollback_patterns") or []:
        lines.append(f"- {row.get('insight')}")

    incident = sections.get("incident_exposure") or {}
    lines.extend(
        [
            "",
            "## Incident exposure",
            "",
            f"- open incidents: **{incident.get('open_incidents', 0)}**",
            f"- exposure: {incident.get('exposure_label', '—')}",
            f"- production impact risk: {incident.get('production_impact_risk', '—')}",
            "",
            "_All readiness recommendations are `executable: false`. Operator retains governance authority._",
        ]
    )
    return "\n".join(lines)
