# SPDX-License-Identifier: Apache-2.0
"""FIX 125I — GitHub PR open renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.github_pr_open_contract import (
    GITHUB_PR_OPEN_APPROVAL_PHRASE,
    HUMAN_REVIEW_REQUIRED_FIX_125I,
    MERGE_ENABLED_FIX_125I,
)


def render_github_pr_open_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = ["# Software Delivery — GitHub PR Open Blocked", "", "## Blockers"]
    for blocker in blockers:
        lines.append(f"- `{blocker}`")
    if detail:
        lines.extend(["", detail])
    lines.extend(
        [
            "",
            "## Required phrase",
            f"- {GITHUB_PR_OPEN_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_github_pr_open_report(record: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Governed GitHub PR",
        "",
        f"- pr_open_id: `{record.get('pr_open_id', '')}`",
        f"- status: **{record.get('status', '')}**",
        f"- repository: **{record.get('repository', '')}**",
        f"- PR: **#{record.get('pr_number', '')}**",
        f"- URL: {record.get('pr_url', '')}",
        f"- head: `{record.get('head_branch', '')}` → base: `{record.get('base_branch', '')}`",
        f"- idempotency_key: `{record.get('idempotency_key', '')}`",
        "",
        "## Title",
        record.get("title", ""),
        "",
        "## Boundaries (125I)",
        f"- merge: **{record.get('merge_enabled', MERGE_ENABLED_FIX_125I)}**",
        f"- deploy: **{record.get('deploy_enabled', False)}**",
        f"- railway_mutation: **{record.get('railway_mutation_enabled', False)}**",
        f"- human_review_required: **{record.get('human_review_required', HUMAN_REVIEW_REQUIRED_FIX_125I)}**",
        "",
        "## Human review",
        "This PR was opened for **human review**. Merge and deploy require separate governed steps.",
    ]
    return "\n".join(lines)


def render_github_pr_open_status(record: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Software Delivery — GitHub PR Status",
            "",
            f"- status: **{record.get('status', '')}**",
            f"- PR: #{record.get('pr_number', '')}",
            f"- URL: {record.get('pr_url', '')}",
            "",
            "Run `show governed github pr report` for details.",
        ]
    )
