# SPDX-License-Identifier: Apache-2.0
"""FIX 125B — branch orchestration renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.branch_orchestration_contract import (
    BRANCH_ARCHIVE_APPROVAL_PHRASE,
    BRANCH_CREATE_APPROVAL_PHRASE,
    BRANCH_RESTORE_APPROVAL_PHRASE,
    CODE_MODIFICATION_ENABLED_FIX_125B,
    MERGE_ENABLED_FIX_125B,
    PR_CREATION_ENABLED_FIX_125B,
)


def render_branch_status(ctx: dict[str, Any], *, plan: dict[str, Any] | None = None) -> str:
    lines = [
        "# Software Delivery — Implementation Branch Status",
        "",
        f"- branch_context_id: `{ctx.get('branch_context_id', '')}`",
        f"- plan_id: `{ctx.get('plan_id', '')}`",
        f"- job_id: `{ctx.get('job_id', '')}`",
        f"- repository: **{ctx.get('repository', '')}**",
        f"- issue: **#{ctx.get('issue_number', '')}**",
        f"- branch_name: `{ctx.get('branch_name', '')}`",
        f"- workspace_path: `{ctx.get('workspace_path', '')}`",
        f"- lifecycle_state: **{ctx.get('lifecycle_state', '')}**",
        f"- lock_holder: `{ctx.get('lock_holder', '') or 'none'}`",
        "",
        "## Workspace execution layer (125B)",
        "- Isolated workspace path reserved (no file writes yet)",
        "- Branch creation is **simulated** — durable receipts only",
        "",
        "## Forbidden (125B)",
        f"- code_modification: **{CODE_MODIFICATION_ENABLED_FIX_125B}**",
        f"- pr_creation: **{PR_CREATION_ENABLED_FIX_125B}**",
        f"- merge: **{MERGE_ENABLED_FIX_125B}**",
        "",
        "Software delivery lane ≠ infrastructure mutation lane.",
    ]
    if plan:
        lines.extend(
            [
                "",
                "## Linked plan",
                f"- planning_approved: **{plan.get('planning_approved', False)}**",
                f"- plan_status: **{plan.get('status', '')}**",
            ]
        )
    return "\n".join(lines)


def render_branch_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = [
        "# Software Delivery — Branch Orchestration Blocked",
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
            "## Approval phrases",
            f"- create: {BRANCH_CREATE_APPROVAL_PHRASE}",
            f"- archive: {BRANCH_ARCHIVE_APPROVAL_PHRASE}",
            f"- restore: {BRANCH_RESTORE_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_software_delivery_timeline(timeline: dict[str, Any]) -> str:
    plan = timeline.get("plan") or {}
    ctx = timeline.get("branch_context") or {}
    lines = [
        "# Software Delivery — Timeline",
        "",
        f"- plan_id: `{plan.get('plan_id', '')}`",
        f"- branch_context_id: `{ctx.get('branch_context_id', '') or 'none'}`",
        f"- branch lifecycle: **{ctx.get('lifecycle_state', 'not_created')}**",
        "",
        "## Plan events",
    ]
    plan_events = timeline.get("plan_events") or []
    if not plan_events:
        lines.append("_No plan events yet._")
    else:
        for ev in plan_events:
            lines.append(
                f"- `{ev.get('recorded_at', '')}` **{ev.get('action', '')}**"
                + (f" — {ev.get('detail', '')}" if ev.get("detail") else "")
            )
    lines.extend(["", "## Branch events"])
    branch_events = timeline.get("branch_events") or []
    if not branch_events:
        lines.append("_No branch events yet._")
    else:
        for ev in branch_events:
            lines.append(
                f"- `{ev.get('recorded_at', '')}` **{ev.get('action', '')}**"
                + (f" — {ev.get('detail', '')}" if ev.get("detail") else "")
            )
    lines.extend(["", "## Branch receipts"])
    receipts = timeline.get("branch_receipts") or []
    if not receipts:
        lines.append("_No branch receipts yet._")
    else:
        for rc in receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** "
                f"({rc.get('status', '')})"
            )
    proposal = timeline.get("patch_proposal") or {}
    lines.extend(
        [
            "",
            "## Patch proposal",
            f"- proposal_id: `{proposal.get('proposal_id', '') or 'none'}`",
            f"- status: **{proposal.get('status', 'not_started')}**",
            f"- approved: **{proposal.get('patch_proposal_approved', False)}**",
            "",
            "## Patch events",
        ]
    )
    patch_events = timeline.get("patch_events") or []
    if not patch_events:
        lines.append("_No patch events yet._")
    else:
        for ev in patch_events:
            lines.append(
                f"- `{ev.get('recorded_at', '')}` **{ev.get('action', '')}**"
                + (f" — {ev.get('detail', '')}" if ev.get("detail") else "")
            )
    lines.extend(["", "## Patch receipts"])
    patch_receipts = timeline.get("patch_receipts") or []
    if not patch_receipts:
        lines.append("_No patch receipts yet._")
    else:
        for rc in patch_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** "
                f"({rc.get('status', '')})"
            )
    application = timeline.get("workspace_application") or {}
    lines.extend(
        [
            "",
            "## Workspace application (125D)",
            f"- application_id: `{application.get('application_id', '') or 'none'}`",
            f"- status: **{application.get('status', 'not_applied')}**",
            "",
            "## Workspace apply events",
        ]
    )
    ws_events = timeline.get("workspace_apply_events") or []
    if not ws_events:
        lines.append("_No workspace apply events yet._")
    else:
        for ev in ws_events:
            lines.append(
                f"- `{ev.get('recorded_at', '')}` **{ev.get('action', '')}**"
                + (f" — {ev.get('detail', '')}" if ev.get("detail") else "")
            )
    lines.extend(["", "## Workspace apply receipts"])
    ws_receipts = timeline.get("workspace_apply_receipts") or []
    if not ws_receipts:
        lines.append("_No workspace apply receipts yet._")
    else:
        for rc in ws_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** "
                f"({rc.get('status', '')})"
            )
    verification = timeline.get("workspace_verification") or {}
    lines.extend(
        [
            "",
            "## Workspace verification (125E)",
            f"- verification_id: `{verification.get('verification_id', '') or 'none'}`",
            f"- status: **{verification.get('status', 'not_run')}**",
            f"- pr_drafting_unblocked: **{verification.get('pr_drafting_unblocked', False)}**",
            "",
            "## Verification events",
        ]
    )
    verify_events = timeline.get("workspace_verify_events") or []
    if not verify_events:
        lines.append("_No verification events yet._")
    else:
        for ev in verify_events:
            lines.append(
                f"- `{ev.get('recorded_at', '')}` **{ev.get('action', '')}**"
                + (f" — {ev.get('detail', '')}" if ev.get("detail") else "")
            )
    lines.extend(["", "## Verification receipts"])
    verify_receipts = timeline.get("workspace_verify_receipts") or []
    if not verify_receipts:
        lines.append("_No verification receipts yet._")
    else:
        for rc in verify_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** "
                f"({rc.get('status', '')})"
            )
    pr_draft = timeline.get("pr_draft") or {}
    lines.extend(
        [
            "",
            "## PR draft (125F)",
            f"- draft_id: `{pr_draft.get('draft_id', '') or 'none'}`",
            f"- status: **{pr_draft.get('status', 'not_created')}**",
            f"- github_pr_created: **{pr_draft.get('github_pr_created', False)}**",
            "",
            "## PR draft events",
        ]
    )
    draft_events = timeline.get("pr_draft_events") or []
    if not draft_events:
        lines.append("_No PR draft events yet._")
    else:
        for ev in draft_events:
            lines.append(
                f"- `{ev.get('recorded_at', '')}` **{ev.get('action', '')}**"
                + (f" — {ev.get('detail', '')}" if ev.get("detail") else "")
            )
    lines.extend(["", "## PR draft receipts"])
    draft_receipts = timeline.get("pr_draft_receipts") or []
    if not draft_receipts:
        lines.append("_No PR draft receipts yet._")
    else:
        for rc in draft_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** "
                f"({rc.get('status', '')})"
            )
    github_pf = timeline.get("github_pr_preflight") or {}
    lines.extend(
        [
            "",
            "## GitHub PR preflight (125G)",
            f"- preflight_id: `{github_pf.get('preflight_id', '') or 'none'}`",
            f"- status: **{github_pf.get('status', 'not_run')}**",
            f"- approved: **{github_pf.get('preflight_approved', False)}**",
            "",
            "## GitHub preflight receipts",
        ]
    )
    g_receipts = timeline.get("github_pr_preflight_receipts") or []
    if not g_receipts:
        lines.append("_No GitHub preflight receipts yet._")
    else:
        for rc in g_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** ({rc.get('status', '')})"
            )
    branch_push = timeline.get("github_branch_push") or {}
    lines.extend(
        [
            "",
            "## GitHub branch push (125H)",
            f"- push_id: `{branch_push.get('push_id', '') or 'none'}`",
            f"- status: **{branch_push.get('status', 'not_run')}**",
            f"- branch: `{branch_push.get('branch_name', '')}`",
            "",
            "## Branch push receipts",
        ]
    )
    bp_receipts = timeline.get("github_branch_push_receipts") or []
    if not bp_receipts:
        lines.append("_No branch push receipts yet._")
    else:
        for rc in bp_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** ({rc.get('status', '')})"
            )
    pr_open = timeline.get("github_pr_open") or {}
    lines.extend(
        [
            "",
            "## GitHub PR open (125I)",
            f"- pr_open_id: `{pr_open.get('pr_open_id', '') or 'none'}`",
            f"- status: **{pr_open.get('status', 'not_run')}**",
            f"- PR URL: {pr_open.get('pr_url', '') or 'none'}",
            "",
            "## PR open receipts",
        ]
    )
    po_receipts = timeline.get("github_pr_open_receipts") or []
    if not po_receipts:
        lines.append("_No PR open receipts yet._")
    else:
        for rc in po_receipts:
            lines.append(
                f"- `{rc.get('recorded_at', '')}` **{rc.get('phase', '')}** ({rc.get('status', '')})"
            )
    if pr_open.get("status") == "opened":
        lines.append("\nGoverned PR opened — **human review required** before merge or deploy.")
    elif branch_push.get("status") == "pushed":
        lines.append("\nFeature branch pushed. PR open: FIX **125I** (`open governed github pull request`).")
    else:
        lines.append(
            "\nRepo/git unchanged until 125H push (after 125G approve); workspace writes are bounded and receipted."
        )
    return "\n".join(lines)
