# SPDX-License-Identifier: Apache-2.0
"""FIX 125F — PR draft renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.pr_draft_contract import (
    DEPLOY_ENABLED_FIX_125F,
    GITHUB_PR_CREATION_ENABLED_FIX_125F,
    GIT_PUSH_ENABLED_FIX_125F,
    MERGE_ENABLED_FIX_125F,
)


def render_pr_draft_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = [
        "# Software Delivery — PR Draft Blocked",
        "",
        "## Blockers",
    ]
    for blocker in blockers:
        lines.append(f"- `{blocker}`")
    if detail:
        lines.extend(["", detail])
    lines.extend(
        [
            "",
            "Required flow: apply workspace (125D) → verify workspace (125E) → create PR draft (125F).",
        ]
    )
    return "\n".join(lines)


def render_pr_draft(draft: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Governed PR Draft Artifact",
        "",
        f"- draft_id: `{draft.get('draft_id', '')}`",
        f"- status: **{draft.get('status', '')}**",
        f"- title: {draft.get('title', '')}",
        f"- branch: `{draft.get('branch_name', '')}`",
        f"- github_pr_created: **{draft.get('github_pr_created', False)}**",
        f"- artifact: `{draft.get('artifact_path', '')}`",
        "",
        "## Boundaries (125F)",
        f"- github_pr_creation: **{draft.get('github_pr_creation_enabled', GITHUB_PR_CREATION_ENABLED_FIX_125F)}**",
        f"- git_push: **{GIT_PUSH_ENABLED_FIX_125F}**",
        f"- merge: **{MERGE_ENABLED_FIX_125F}**",
        f"- deploy: **{DEPLOY_ENABLED_FIX_125F}**",
        "",
        "---",
        "",
        str(draft.get("body") or ""),
    ]
    return "\n".join(lines)


def render_pr_draft_status(draft: dict[str, Any]) -> str:
    vsum = draft.get("verification_summary") or {}
    lines = [
        "# Software Delivery — PR Draft Status",
        "",
        f"- draft_id: `{draft.get('draft_id', '')}`",
        f"- status: **{draft.get('status', '')}**",
        f"- verification_status: **{vsum.get('status', '')}**",
        f"- files: **{len(draft.get('files') or [])}**",
        "",
        "Run `show software delivery pr draft` for full body and checklist.",
    ]
    return "\n".join(lines)
