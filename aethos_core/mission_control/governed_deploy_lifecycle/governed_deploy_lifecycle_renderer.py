# SPDX-License-Identifier: Apache-2.0
"""FIX 210 — Markdown renderer for governed deploy lifecycle."""

from __future__ import annotations

from typing import Any


def render_governed_deploy_lifecycle(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    readiness = (sections.get("deploy_readiness_assessment") or [{}])[0]
    recommendation = (sections.get("deploy_recommendation") or [{}])[0]
    handoff = (sections.get("deploy_handoff_artifact") or [{}])[0] if sections.get("deploy_handoff_artifact") else {}

    lines = [
        "# Governed Deploy Lifecycle (FIX 210 — deploy_authority ≠ autonomous_deploy)",
        "",
        f"- deploy authority: **{payload.get('deploy_authority', False)}** _(always false)_",
        f"- autonomous deploy: **{payload.get('autonomous_deploy_enabled', False)}** _(always false)_",
        f"- phase 1: GitHub Actions only",
        f"- current stage: **{payload.get('current_stage')}**",
        f"- target environment: **{payload.get('deploy_target_environment') or 'pending'}**",
        "",
        payload.get("invariant", ""),
        "",
        "## Deploy Readiness",
        "",
        f"- readiness score: **{readiness.get('readiness_score', 0)}**",
        f"- merge approved: **{(readiness.get('merge_status') or {}).get('merge_approved')}**",
        f"- merge completed: **{(readiness.get('merge_status') or {}).get('merge_completed_acknowledged')}**",
        f"- human decision: **{payload.get('human_deploy_decision') or 'pending'}**",
    ]

    blockers = readiness.get("outstanding_blockers") or []
    if blockers:
        lines.append(f"- blockers: {', '.join(blockers)}")

    lines.extend(
        [
            "",
            "## Deploy Recommendation",
            "",
            f"**{recommendation.get('recommendation', 'HOLD_DEPLOY')}** — {recommendation.get('rationale', '')}",
            "",
            "_Recommendation only — not deploy authority._",
        ]
    )

    if handoff:
        lines.extend(
            [
                "",
                "## Deploy Handoff",
                "",
                f"- handoff id: `{handoff.get('handoff_id')}`",
                f"- environment: **{handoff.get('environment_target')}**",
                f"- executable: **{handoff.get('handoff_executable', False)}**",
            ]
        )

    adapter = (sections.get("github_actions_deployment_adapter") or [{}])[0]
    if adapter.get("command_template"):
        lines.extend(
            [
                "",
                "## GitHub Actions Adapter",
                "",
                f"`{adapter.get('command_template')}`",
                "",
                "_Human must dispatch workflow — AethOS does not deploy autonomously._",
            ]
        )

    return "\n".join(lines)
