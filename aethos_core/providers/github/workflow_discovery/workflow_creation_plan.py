# SPDX-License-Identifier: Apache-2.0
"""Governed workflow file creation plan — approval-gated, no direct execution."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.operations.mutations.risk import MutationRiskTier

_WORKFLOW_CREATION_RX = re.compile(
    r"\b("
    r"create\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|add\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|commit\s+(?:the\s+|this\s+)?workflow"
    r"|push\s+(?:the\s+|this\s+)?workflow"
    r"|write\s+(?:the\s+|this\s+)?ci\.yml"
    r"|add\s+(?:the\s+|this\s+)?ci\.yml"
    r"|create\s+(?:the\s+|this\s+)?ci\.yml"
    r"|implement\s+(?:the\s+|this\s+)?workflow"
    r"|set\s+up\s+(?:the\s+|this\s+)?workflow"
    r"|make\s+(?:the\s+|this\s+)?workflow\s+file"
    r")\b",
    re.I,
)

_DIRECT_MAIN_WRITE_RX = re.compile(
    r"\b("
    r"(?:push|commit|write|deploy)\s+.*?\bto\s+main\b"
    r"|(?:push|commit|write)\s+.*?\bon\s+main\b"
    r"|directly?\s+(?:to|on)\s+main"
    r")",
    re.I,
)


def is_workflow_creation_intent(text: str) -> bool:
    return bool(_WORKFLOW_CREATION_RX.search(text or ""))


def is_direct_main_write_requested(text: str) -> bool:
    return bool(_DIRECT_MAIN_WRITE_RX.search(text or ""))


def classify_workflow_creation_risk(text: str) -> MutationRiskTier:
    if is_direct_main_write_requested(text):
        return MutationRiskTier.T3_PRODUCTION
    return MutationRiskTier.T2_LOW_RISK


def compose_governed_workflow_creation_plan(
    discovery: dict[str, Any],
    *,
    repo_context: dict[str, Any] | None = None,
    text: str = "",
) -> str:
    repo = str(discovery.get("repository") or "the repository")
    default_branch = str(discovery.get("default_branch") or "main")
    risk_tier = classify_workflow_creation_risk(text)

    branch_name = "add-ci-workflow"
    file_path = ".github/workflows/ci.yml"

    if risk_tier == MutationRiskTier.T3_PRODUCTION:
        return _compose_blocked_direct_write(repo=repo, default_branch=default_branch)

    lines = [
        "I can prepare a governed workflow-file creation plan.",
        "",
        "**Target:**",
        f"- Repo: `{repo}`",
        f"- File: `{file_path}`",
        f"- Branch: `{branch_name}`",
        f"- PR target: `{default_branch}`",
        "",
        "**Execution steps** (after approval):",
        f"1. Create branch `{branch_name}` from `{default_branch}`",
        f"2. Add `{file_path}` with the proposed CI workflow",
        "3. Commit workflow file",
        f"4. Open PR → `{default_branch}`",
        "5. Verify GitHub Actions workflow run after PR",
        "",
        "No file has been created yet.",
        "",
        "This requires approval because it will modify the repository.",
        "",
        "Reply **approve** to execute, or **cancel** to discard.",
    ]
    return "\n".join(lines)


def _compose_blocked_direct_write(*, repo: str, default_branch: str) -> str:
    lines = [
        "I will not push this workflow directly to main.",
        "",
        "**Safer plan:**",
        "- Create branch `add-ci-workflow`",
        "- Commit workflow file there",
        f"- Open PR to `{default_branch}`",
        "- Verify checks",
        "",
        "Direct main push is **T3** and blocked unless explicitly elevated.",
    ]
    return "\n".join(lines)


_CANCEL_RX = re.compile(
    r"\b(cancel|discard|nevermind|never\s+mind|abort)\b",
    re.I,
)


def is_workflow_creation_cancel_intent(text: str) -> bool:
    return bool(_CANCEL_RX.search(text or ""))


def compose_cancel_reply() -> str:
    return (
        "Cancelled the pending workflow-file creation plan.\n"
        "\n"
        "No file, branch, commit, or PR was created."
    )


def route_workflow_creation_from_context(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Route workflow creation intents using persisted pending proposal context."""
    from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
        clear_pending_workflow_proposal,
        get_pending_workflow_proposal,
    )

    pending = get_pending_workflow_proposal(session_id=session_id)
    if pending is None:
        return None

    if is_workflow_creation_cancel_intent(text) and not is_workflow_creation_intent(text):
        clear_pending_workflow_proposal(session_id=session_id)
        return (
            compose_cancel_reply(),
            "workflow_creation_cancelled",
            {
                "route_id": "workflow_creation_plan",
                "matched_module": "providers.github.workflow_discovery.workflow_creation_plan",
                "provider": "github",
                "workflow_creation_context_used": "true",
            },
        )

    if not is_workflow_creation_intent(text):
        return None

    repo = str(pending.get("repo") or "the repository")
    base_branch = str(pending.get("base_branch") or "main")
    file_path = str(pending.get("file_path") or ".github/workflows/ci.yml")
    branch = str(pending.get("branch") or "add-ci-workflow")

    discovery = {
        "repository": repo,
        "default_branch": base_branch,
        "workflows_dir_found": False,
        "workflow_file_names": [],
        "workflow_files": [],
        "actions_status": "enabled",
    }

    body = compose_governed_workflow_creation_plan(discovery, text=text)

    return (
        body,
        "workflow_creation_governed_plan",
        {
            "route_id": "workflow_creation_plan",
            "matched_module": "providers.github.workflow_discovery.workflow_creation_plan",
            "provider": "github",
            "repository": repo,
            "file_path": file_path,
            "branch": branch,
            "base_branch": base_branch,
            "governed_plan": "true",
            "workflow_creation_context_used": "true",
            "blocked_handlers": "llm_fallback,active_thread,generic_workflow_planner",
        },
    )
