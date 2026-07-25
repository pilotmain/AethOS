# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — patch proposal renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.patch_proposal_contract import (
    DEPLOY_ENABLED_FIX_125C,
    FILE_WRITE_ENABLED_FIX_125C,
    GIT_COMMIT_ENABLED_FIX_125C,
    MERGE_ENABLED_FIX_125C,
    PATCH_PROPOSAL_APPROVAL_PHRASE,
    PR_CREATION_ENABLED_FIX_125C,
)


def render_patch_proposal_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = [
        "# Software Delivery — Patch Proposal Blocked",
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
            "## Flow",
            "plan (125A) → branch (125B) → **patch proposal (125C)** → approval → code write (future)",
            "",
            f"Approval phrase: {PATCH_PROPOSAL_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_proposed_files(proposal: dict[str, Any], *, plan: dict[str, Any] | None = None) -> str:
    files = proposal.get("proposed_files") or []
    lines = [
        "# Software Delivery — Proposed Patch Files",
        "",
        f"- proposal_id: `{proposal.get('proposal_id', '')}`",
        f"- status: **{proposal.get('status', '')}**",
        f"- file_count: **{len(files)}**",
        "",
        "## Files to change (bounded)",
    ]
    if not files:
        lines.append("_No files in scope — widen plan or issue analysis._")
    else:
        for path in files:
            lines.append(f"- `{path}`")
    if plan:
        lines.extend(
            [
                "",
                "## Linked plan",
                f"- issue: **{plan.get('repository', '')}#{plan.get('issue_number', '')}**",
                f"- blast_radius: **{plan.get('blast_radius', '')}**",
            ]
        )
    lines.extend(["", "No file writes performed."])
    return "\n".join(lines)


def render_patch_intent(proposal: dict[str, Any]) -> str:
    intent = proposal.get("patch_intent") or {}
    lines = [
        "# Software Delivery — Patch Intent",
        "",
        f"- intent_id: `{intent.get('intent_id', '')}`",
        f"- summary: {intent.get('summary', '')}",
        f"- risk_tier: **{intent.get('risk_tier', 'unknown')}**",
        f"- branch: `{intent.get('branch_name', '')}`",
        f"- workspace: `{intent.get('workspace_path', '')}`",
        "",
        "## Bounded scope",
    ]
    for path in intent.get("bounded_scope") or []:
        lines.append(f"- `{path}`")
    lines.extend(["", "## Validation steps"])
    for step in intent.get("validation_steps") or []:
        lines.append(f"- {step}")
    lines.extend(
        [
            "",
            "## Rollback",
            str(intent.get("rollback_strategy") or "Revert branch."),
            "",
            "Run `show patch diff preview` before `approve patch proposal`.",
        ]
    )
    return "\n".join(lines)


def render_diff_preview(proposal: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Patch Diff Preview",
        "",
        f"- proposal_id: `{proposal.get('proposal_id', '')}`",
        f"- patch_proposal_approved: **{proposal.get('patch_proposal_approved', False)}**",
        "",
        "## Unified diffs (read-only preview)",
    ]
    diffs = proposal.get("unified_diffs") or []
    if not diffs:
        lines.append("_No diffs generated._")
    else:
        for entry in diffs:
            path = entry.get("file") or "unknown"
            lines.extend([f"### `{path}`", "```diff", (entry.get("diff") or "").strip(), "```", ""])
    lines.extend(
        [
            "## Governance (125C)",
            f"- file_write_enabled: **{FILE_WRITE_ENABLED_FIX_125C}**",
            f"- git_commit: **{GIT_COMMIT_ENABLED_FIX_125C}**",
            f"- pr_creation: **{PR_CREATION_ENABLED_FIX_125C}**",
            f"- merge: **{MERGE_ENABLED_FIX_125C}**",
            f"- deploy: **{DEPLOY_ENABLED_FIX_125C}**",
            "",
            f"Approve with: {PATCH_PROPOSAL_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_patch_proposal_status(proposal: dict[str, Any]) -> str:
    intent = proposal.get("patch_intent") or {}
    lines = [
        "# Software Delivery — Patch Proposal Status",
        "",
        f"- proposal_id: `{proposal.get('proposal_id', '')}`",
        f"- status: **{proposal.get('status', '')}**",
        f"- proposed_files: **{len(proposal.get('proposed_files') or [])}**",
        f"- patch_intent: **{'yes' if intent else 'no'}**",
        f"- diff_preview: **{len(proposal.get('unified_diffs') or [])} hunks**",
        f"- patch_proposal_approved: **{proposal.get('patch_proposal_approved', False)}**",
        f"- file_write_enabled: **{proposal.get('file_write_enabled', False)}**",
        "",
        "plan → branch → patch proposal → approval → code write (future)",
    ]
    return "\n".join(lines)
