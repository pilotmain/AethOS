# SPDX-License-Identifier: Apache-2.0
"""FIX 125E — workspace verification renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.workspace_verification_contract import (
    ARBITRARY_SHELL_ENABLED_FIX_125E,
    DEPENDENCY_INSTALL_ENABLED_FIX_125E,
    PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E,
)


def render_verification_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = [
        "# Software Delivery — Workspace Verification Blocked",
        "",
        "## Blockers",
    ]
    for blocker in blockers:
        lines.append(f"- `{blocker}`")
    if detail:
        lines.extend(["", detail])
    return "\n".join(lines)


def render_verification_report(verification: dict[str, Any]) -> str:
    classification = verification.get("classification") or {}
    lines = [
        "# Software Delivery — Workspace Verification Report",
        "",
        f"- verification_id: `{verification.get('verification_id', '')}`",
        f"- status: **{verification.get('status', '')}**",
        f"- failure_class: `{verification.get('failure_class', '') or 'none'}`",
        f"- pr_drafting_unblocked: **{verification.get('pr_drafting_unblocked', False)}**",
        f"- workspace_tree: `{verification.get('workspace_tree', '')}`",
        "",
        "## Summary",
        str(classification.get("summary") or ""),
        "",
        "## Checks",
    ]
    for check in verification.get("checks") or []:
        status = "pass" if check.get("ok") or check.get("skipped") else "fail"
        skip = " (skipped)" if check.get("skipped") else ""
        lines.append(
            f"- **{check.get('check', '')}**: {status}{skip} — {check.get('detail', '')}"
        )
        if check.get("failure_class"):
            lines.append(f"  - failure_class: `{check.get('failure_class')}`")
    lines.extend(
        [
            "",
            "## Boundaries (125E)",
            f"- repo_write: **false**",
            f"- arbitrary_shell: **{ARBITRARY_SHELL_ENABLED_FIX_125E}**",
            f"- dependency_install: **{DEPENDENCY_INSTALL_ENABLED_FIX_125E}**",
            f"- pr_drafting_requires_verification: **{PR_DRAFTING_REQUIRES_VERIFICATION_FIX_125E}**",
            "",
            "Verification runs against the governed workspace tree; repo/git unchanged.",
        ]
    )
    return "\n".join(lines)


def render_verification_status(verification: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Workspace Verification Status",
        "",
        f"- status: **{verification.get('status', '')}**",
        f"- pr_drafting_unblocked: **{verification.get('pr_drafting_unblocked', False)}**",
        f"- failure_class: `{verification.get('failure_class', '') or 'none'}`",
        "",
        "Run `show workspace verification report` for full check output.",
    ]
    return "\n".join(lines)
