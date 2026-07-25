# SPDX-License-Identifier: Apache-2.0
"""FIX 230 — Markdown renderer for governed rollback lifecycle."""

from __future__ import annotations

from typing import Any


def render_governed_rollback_lifecycle(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    assessment = (sections.get("rollback_assessment") or [{}])[0]
    recommendation = (sections.get("rollback_recommendation") or [{}])[0]
    candidates = (sections.get("rollback_candidate_registry") or [{}])[0]
    handoff = (sections.get("rollback_handoff_artifact") or [{}])[0] if sections.get(
        "rollback_handoff_artifact"
    ) else {}

    lines = [
        "# Governed Rollback Lifecycle (FIX 230 — rollback_authority ≠ autonomous_rollback)",
        "",
        f"- rollback authority: **{payload.get('rollback_authority', False)}** _(always false)_",
        f"- autonomous rollback: **{payload.get('autonomous_rollback_enabled', False)}** _(always false)_",
        f"- incident classification: **{payload.get('incident_classification')}**",
        f"- current stage: **{payload.get('current_stage')}**",
        f"- human rollback decision: **{payload.get('human_rollback_decision') or 'pending'}**",
        "",
        payload.get("invariant", ""),
        "",
        "## Rollback Assessment",
        "",
        f"- readiness score: **{assessment.get('readiness_score', 0)}**",
        f"- incident severity: **{assessment.get('incident_severity')}**",
        f"- deployment history events: **{assessment.get('deployment_history_count', 0)}**",
    ]

    blockers = assessment.get("outstanding_blockers") or []
    if blockers:
        lines.append(f"- blockers: {', '.join(blockers)}")

    lkg = candidates.get("last_known_good") or {}
    lines.extend(
        [
            "",
            "## Rollback Candidate",
            "",
            f"- target: **{lkg.get('target_release') or 'none identified'}**",
            f"- source: **{lkg.get('source') or 'pending'}**",
            "",
            "## Rollback Recommendation",
            "",
            f"**{recommendation.get('recommendation', 'INVESTIGATE')}** — {recommendation.get('rationale', '')}",
            "",
            "_Recommendation only — not rollback authority._",
        ]
    )

    if handoff:
        adapter = handoff.get("github_actions_rollback_adapter") or {}
        lines.extend(
            [
                "",
                "## Rollback Handoff",
                "",
                f"- handoff id: `{handoff.get('handoff_id')}`",
                f"- target release: **{handoff.get('target_release')}**",
                f"- command template: `{adapter.get('command_template')}`",
                f"- executable: **{handoff.get('handoff_executable', False)}**",
            ]
        )

    timeline = sections.get("recovery_timeline") or []
    if timeline:
        lines.extend(["", "## Recovery Timeline", ""])
        for event in timeline[-6:]:
            lines.append(f"- {event.get('stage')}: {event.get('kind') or event.get('label') or event.get('event_id')}")

    return "\n".join(lines)
