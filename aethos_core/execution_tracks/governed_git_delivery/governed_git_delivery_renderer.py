# SPDX-License-Identifier: Apache-2.0
"""FIX 336 / EXECUTION_TRACK_3 — render Git delivery deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_git_delivery_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    lines = [
        "# Git Delivery Report",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 336')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Git mutations are governed under human approval. **Git delivery ≠ merge authority.**",
        "",
        "## Success criteria",
        "",
        f"- Branch created: **{success.get('branch_created')}**",
        f"- Commit created: **{success.get('commit_created')}**",
        f"- Branch pushed: **{success.get('branch_pushed')}**",
        f"- Pull request created: **{success.get('pull_request_created')}**",
        f"- Track complete: **{success.get('track_complete')}**",
        "",
        "## Phase 1 — Delivery request intake",
        "",
        "```json",
        _json_block(_section(payload, "phase_1_delivery_request_intake", "git_delivery_request_registry")),
        "```",
        "",
        "## Phase 9 — Delivery dashboard",
        "",
        "```json",
        _json_block(_section(payload, "phase_9_delivery_dashboard", "git_delivery_dashboard")),
        "```",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_pull_request_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_6_pull_request_creation", "pull_request_report") or {}
    branch = _section(payload, "phase_2_branch_planning", "branch_plan_report") or {}
    lines = [
        "# Pull Request Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Pull request",
        "",
        f"- URL: **{report.get('pull_request_url', '—')}**",
        f"- Number: **{report.get('pull_request_number', '—')}**",
        f"- Title: **{report.get('title', '—')}**",
        f"- Base: **{report.get('base_branch', '—')}**",
        f"- Head: **{report.get('head_branch', '—')}**",
        f"- Merge performed: **{report.get('merge_performed')}**",
        "",
        "## Branch plan",
        "",
        f"- Pattern: `{branch.get('delivery_branch_pattern', 'aethos/<work-item>/<timestamp>')}`",
        f"- Target branch: **{branch.get('target_branch', 'main')}**",
        "",
    ]
    return "\n".join(lines)


def render_git_delivery_verification_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_7_delivery_verification", "git_delivery_verification_report") or {}
    bundle = _section(payload, "phase_8_evidence_collection", "git_delivery_evidence_bundle") or {}
    lines = [
        "# Git Delivery Verification Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Verification",
        "",
        f"- Verified: **{report.get('verified')}**",
        f"- Branch exists: **{report.get('branch_exists')}**",
        f"- Commit exists: **{report.get('commit_exists')}**",
        f"- Pull request exists: **{report.get('pull_request_exists')}**",
        f"- Repository healthy: **{report.get('repository_healthy')}**",
        f"- Merge performed: **{report.get('merge_performed')}**",
        "",
        "## Evidence bundle",
        "",
        "```json",
        _json_block(bundle),
        "```",
    ]
    return "\n".join(lines)


def render_all_governed_git_delivery_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "GIT_DELIVERY_REPORT.md": render_git_delivery_report(payload),
        "PULL_REQUEST_REPORT.md": render_pull_request_report(payload),
        "GIT_DELIVERY_VERIFICATION_REPORT.md": render_git_delivery_verification_report(payload),
    }


def render_governed_git_delivery(
    payload: dict[str, Any],
    *,
    focus: str = "git_delivery_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_9_delivery_dashboard") or [{}])[0].get("git_delivery_dashboard", {})
    lines = [
        "# Governed Git Delivery",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 336')}",
        "",
        "Bounded Git delivery under human approval — merge and deployment remain separate.",
        "",
        f"Branch: **{dashboard.get('branch_status', '—')}**",
        f"Commit: **{dashboard.get('commit_status', '—')}**",
        f"Push: **{dashboard.get('push_status', '—')}**",
        f"Pull request: **{dashboard.get('pull_request_status', '—')}**",
        f"Verification: **{dashboard.get('verification_status', '—')}**",
        f"Handoff ready: **{dashboard.get('handoff_ready', False)}**",
        "",
    ]

    if focus == "git_delivery_verification":
        report = (sections.get("phase_7_delivery_verification") or [{}])[0].get(
            "git_delivery_verification_report", {}
        )
        lines.extend(
            [
                "## Delivery verification",
                "",
                f"Verified: **{report.get('verified')}**",
                f"Repository healthy: **{report.get('repository_healthy')}**",
                "",
            ]
        )
    else:
        pr = (sections.get("phase_6_pull_request_creation") or [{}])[0].get("pull_request_report", {})
        lines.extend(
            [
                "## Latest pull request",
                "",
                f"URL: `{pr.get('pull_request_url', '—')}`",
                "",
            ]
        )

    lines.extend(["## Required review gates", ""])
    for gate in (
        "git_delivery_review_note",
        "branch_delivery_review_note",
        "commit_delivery_review_note",
        "pull_request_review_note",
    ):
        lines.append(f"- `{gate}`")
    lines.append("")
    return "\n".join(lines)
