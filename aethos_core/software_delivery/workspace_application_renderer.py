# SPDX-License-Identifier: Apache-2.0
"""FIX 125D — workspace application renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.workspace_application_contract import (
    DEPENDENCY_INSTALL_ENABLED_FIX_125D,
    DEPLOY_ENABLED_FIX_125D,
    GIT_COMMIT_ENABLED_FIX_125D,
    INFRA_MUTATION_ENABLED_FIX_125D,
    MERGE_ENABLED_FIX_125D,
    PR_CREATION_ENABLED_FIX_125D,
    REPO_WRITE_ENABLED_FIX_125D,
    SHELL_EXECUTION_ENABLED_FIX_125D,
    WORKSPACE_APPLY_APPROVAL_PHRASE,
    WORKSPACE_ROLLBACK_APPROVAL_PHRASE,
)


def render_workspace_apply_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = [
        "# Software Delivery — Workspace Apply Blocked",
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
            "## Phrases",
            f"- apply: {WORKSPACE_APPLY_APPROVAL_PHRASE}",
            f"- rollback: {WORKSPACE_ROLLBACK_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_workspace_apply_status(application: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Workspace Apply Status",
        "",
        f"- application_id: `{application.get('application_id', '')}`",
        f"- status: **{application.get('status', '')}**",
        f"- snapshot_id: `{application.get('snapshot_id', '') or 'none'}`",
        f"- workspace_tree: `{application.get('workspace_tree', '')}`",
        f"- files_applied: **{len(application.get('files_applied') or [])}**",
        "",
        "## Applied files",
    ]
    for path in application.get("files_applied") or []:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Boundaries (125D)",
            f"- repo_write: **{application.get('repo_write_enabled', REPO_WRITE_ENABLED_FIX_125D)}**",
            f"- git_commit: **{application.get('git_commit_enabled', GIT_COMMIT_ENABLED_FIX_125D)}**",
            f"- pr / merge / deploy: **false**",
            f"- shell_execution: **{SHELL_EXECUTION_ENABLED_FIX_125D}**",
            f"- dependency_install: **{DEPENDENCY_INSTALL_ENABLED_FIX_125D}**",
            "",
            "Writes occurred only inside the governed workspace tree.",
        ]
    )
    return "\n".join(lines)


def render_governed_workspace_diff(application: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Governed Workspace Diff",
        "",
        f"- plan_id: `{application.get('plan_id', '')}`",
        f"- status: **{application.get('status', 'not_applied')}**",
        "",
        "## Workspace vs repo (unified diff)",
    ]
    diffs = application.get("workspace_diffs") or []
    if not diffs:
        lines.append("_No workspace diff yet — apply patch first._")
    else:
        for entry in diffs:
            path = entry.get("file") or "unknown"
            lines.extend([f"### `{path}`", "```diff", (entry.get("diff") or "").strip(), "```", ""])
    lines.extend(
        [
            "",
            "## Still forbidden",
            f"- repo_write: **{REPO_WRITE_ENABLED_FIX_125D}**",
            f"- git_commit: **{GIT_COMMIT_ENABLED_FIX_125D}**",
            f"- pr: **{PR_CREATION_ENABLED_FIX_125D}**",
            f"- merge: **{MERGE_ENABLED_FIX_125D}**",
            f"- deploy: **{DEPLOY_ENABLED_FIX_125D}**",
            f"- infra_mutation: **{INFRA_MUTATION_ENABLED_FIX_125D}**",
        ]
    )
    return "\n".join(lines)
