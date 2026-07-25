# SPDX-License-Identifier: Apache-2.0
"""FIX 125H — branch push renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    GITHUB_PR_CREATE_ENABLED_FIX_125H,
    MERGE_ENABLED_FIX_125H,
    MUTATION_PREVIEW_ACK_PHRASE,
)


def render_branch_push_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = ["# Software Delivery — Branch Push Blocked", "", "## Blockers"]
    for blocker in blockers:
        lines.append(f"- `{blocker}`")
    if detail:
        lines.extend(["", detail])
    lines.extend(
        [
            "",
            "## Required phrases",
            f"- push: {BRANCH_PUSH_APPROVAL_PHRASE}",
            f"- ack: {MUTATION_PREVIEW_ACK_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_branch_push_report(push: dict[str, Any]) -> str:
    rollback = push.get("rollback_cleanup_plan") or {}
    lines = [
        "# Software Delivery — Governed Branch Push",
        "",
        f"- push_id: `{push.get('push_id', '')}`",
        f"- status: **{push.get('status', '')}**",
        f"- repository: **{push.get('repository', '')}**",
        f"- branch: `{push.get('branch_name', '')}`",
        f"- head_commit: `{push.get('head_commit_sha', '')}`",
        f"- idempotency_key: `{push.get('idempotency_key', '')}`",
        f"- files_pushed: **{len(push.get('files_pushed') or [])}**",
        "",
        "## Files",
    ]
    for path in push.get("files_pushed") or []:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Boundaries (125H)",
            f"- github_pr_create: **{push.get('github_pr_create_enabled', GITHUB_PR_CREATE_ENABLED_FIX_125H)}**",
            f"- merge: **{MERGE_ENABLED_FIX_125H}**",
            f"- direct_main_push: **{push.get('direct_main_push_enabled', False)}**",
            "",
            "## Rollback / cleanup",
        ]
    )
    for step in rollback.get("branch_push_rollback") or rollback.get("rollback_steps") or []:
        lines.append(f"- {step}")
    lines.append("\nPR open: FIX **125I** (`open governed github pull request` after push).")
    return "\n".join(lines)


def render_branch_push_status(push: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Software Delivery — Branch Push Status",
            "",
            f"- status: **{push.get('status', '')}**",
            f"- branch: `{push.get('branch_name', '')}`",
            f"- head_commit: `{push.get('head_commit_sha', '')}`",
            "",
            "Run `show governed branch push report` for details.",
        ]
    )
