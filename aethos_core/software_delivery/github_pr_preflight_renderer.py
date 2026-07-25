# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR preflight renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.github_pr_preflight_contract import (
    GITHUB_PR_CREATE_ENABLED_FIX_125G,
    GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
    GIT_PUSH_ENABLED_FIX_125G,
)


def render_preflight_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = ["# Software Delivery — GitHub PR Preflight Blocked", "", "## Blockers"]
    for blocker in blockers:
        lines.append(f"- `{blocker}`")
    if detail:
        lines.extend(["", detail])
    return "\n".join(lines)


def render_preflight_report(preflight: dict[str, Any]) -> str:
    preview = preflight.get("mutation_preview") or {}
    rollback = preflight.get("rollback_cleanup_plan") or {}
    review = preflight.get("pr_final_review") or {}
    lines = [
        "# Software Delivery — GitHub PR Creation Preflight",
        "",
        f"- preflight_id: `{preflight.get('preflight_id', '')}`",
        f"- status: **{preflight.get('status', '')}**",
        f"- preflight_approved: **{preflight.get('preflight_approved', False)}**",
        f"- github_creation_unblocked: **{preflight.get('github_creation_unblocked', False)}**",
        f"- idempotency_key: `{preflight.get('idempotency_key', '')}`",
        "",
        "## PR final review",
        f"- title: {review.get('title', '')}",
        f"- body_length: **{review.get('body_length', 0)}** chars",
        "",
        "## Checks",
    ]
    for check in preflight.get("checks") or []:
        mark = "pass" if check.get("ok") else "fail"
        lines.append(f"- **{check.get('check', '')}**: {mark} — {check.get('detail', '')}")
    lines.extend(
        [
            "",
            "## Mutation preview (no mutation in 125G)",
            f"- git_push (125H): **{GIT_PUSH_ENABLED_FIX_125G}** (preview only)",
            f"- github_pr_create (125I): **{GITHUB_PR_CREATE_ENABLED_FIX_125G}** (preview only)",
        ]
    )
    for step in (preview.get("fix_125h_branch_push") or {}).get("actions") or []:
        lines.append(f"  - 125H: {step}")
    for step in (preview.get("fix_125i_open_pr") or {}).get("actions") or []:
        lines.append(f"  - 125I: {step}")
    lines.extend(["", "## Rollback / cleanup plan"])
    for step in rollback.get("rollback_steps") or []:
        lines.append(f"- {step}")
    lines.extend(
        [
            "",
            "## Approval (required before 125H/125I)",
            f"{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_preflight_status(preflight: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Software Delivery — GitHub PR Preflight Status",
            "",
            f"- status: **{preflight.get('status', '')}**",
            f"- approved: **{preflight.get('preflight_approved', False)}**",
            f"- idempotency_key: `{preflight.get('idempotency_key', '')}`",
            "",
            "Run `show github pr creation preflight report` for full output.",
        ]
    )
