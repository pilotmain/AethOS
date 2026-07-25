# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — Markdown renderer for governed merge lifecycle."""

from __future__ import annotations

from typing import Any


def render_governed_merge_lifecycle(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    readiness = (sections.get("merge_readiness_assessment") or [{}])[0]
    recommendation = (sections.get("merge_recommendation") or [{}])[0]
    handoff = (sections.get("merge_handoff_artifact") or [{}])[0] if sections.get("merge_handoff_artifact") else {}

    lines = [
        "# Governed Merge Lifecycle (FIX 200 — merge_authority ≠ autonomous_merge)",
        "",
        f"- merge authority: **{payload.get('merge_authority', False)}** _(always false)_",
        f"- autonomous merge: **{payload.get('autonomous_merge_enabled', False)}** _(always false)_",
        f"- current stage: **{payload.get('current_stage')}**",
        "",
        payload.get("invariant", ""),
        "",
        "## Merge Readiness",
        "",
        f"- readiness score: **{readiness.get('readiness_score', 0)}**",
        f"- PR open: **{readiness.get('pr_open_complete')}**",
        f"- verification passed: **{readiness.get('verification_passed')}**",
        f"- human decision: **{payload.get('human_merge_decision') or 'pending'}**",
    ]

    blockers = readiness.get("outstanding_blockers") or []
    if blockers:
        lines.append(f"- blockers: {', '.join(blockers)}")

    lines.extend(
        [
            "",
            "## Merge Recommendation",
            "",
            f"**{recommendation.get('recommendation', 'HOLD')}** — {recommendation.get('rationale', '')}",
            "",
            "_Recommendation only — not merge authority._",
        ]
    )

    if handoff:
        lines.extend(
            [
                "",
                "## Merge Handoff",
                "",
                f"- handoff id: `{handoff.get('handoff_id')}`",
                f"- executable: **{handoff.get('handoff_executable', False)}**",
            ]
        )

    adapter = (sections.get("merge_execution_adapter") or [{}])[0]
    if adapter.get("command_template"):
        lines.extend(
            [
                "",
                "## Merge Execution Adapter (GitHub)",
                "",
                f"`{adapter.get('command_template')}`",
                "",
                "_Human must execute — AethOS does not merge autonomously._",
            ]
        )

    return "\n".join(lines)
