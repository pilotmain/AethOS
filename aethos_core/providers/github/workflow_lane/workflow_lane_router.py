# SPDX-License-Identifier: Apache-2.0
"""GitHub Workflow Lane — single authoritative hard router for all workflow lifecycle prompts.

This router owns the entire workflow lifecycle:
  discovered → proposal_ready → creation_plan_ready → cancelled

It intercepts before ANY other handler and never falls through to generic routes.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
    compose_generic_ci_workflow_yaml,
    compose_workflow_proposal_reply,
)

_PROPOSAL_RX = re.compile(
    r"\b("
    r"draft\s+(?:a\s+|the\s+)?workflow\s+proposal"
    r"|create\s+(?:a\s+)?workflow\s+proposal"
    r"|create\s+(?:a\s+)?ci\s+(?:workflow\s+)?proposal"
    r"|generate\s+ci\s+workflow"
    r"|draft\s+ci\.yml"
    r"|propose\s+(?:a\s+)?(?:github\s+actions\s+)?workflow"
    r"|prepare\s+(?:the\s+)?workflow\s+file"
    r")\b",
    re.I,
)

_CREATION_RX = re.compile(
    r"\b("
    r"create\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|add\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|create\s+(?:the\s+|this\s+)?ci\.yml"
    r"|add\s+(?:the\s+|this\s+)?ci\.yml"
    r"|write\s+(?:the\s+|this\s+)?ci\.yml"
    r"|commit\s+(?:the\s+|this\s+)?workflow"
    r"|implement\s+(?:the\s+|this\s+)?workflow"
    r"|set\s+up\s+(?:the\s+|this\s+)?workflow"
    r"|make\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|open\s+(?:a\s+)?PR\s+for\s+(?:the\s+|this\s+)?workflow"
    r")\b",
    re.I,
)

_PUSH_MAIN_RX = re.compile(
    r"\b("
    r"(?:push|commit|write|deploy)\s+.*?\bto\s+main\b"
    r"|(?:push|commit|write)\s+.*?\bon\s+main\b"
    r"|directly?\s+(?:to|on)\s+main"
    r")",
    re.I,
)

_CANCEL_RX = re.compile(
    r"^\s*(cancel|discard|nevermind|never\s+mind|abort)\s*$",
    re.I,
)

_APPROVE_RX = re.compile(
    r"^\s*(approve|yes|go\s+ahead|execute|do\s+it|proceed|confirm)\s*[.!]?\s*$",
    re.I,
)

_WORKFLOW_LANE_EXPLICIT_RETRY_RX = re.compile(
    r"\b("
    r"retry\s+approval"
    r"|retry\s+approve"
    r"|approve\s+again"
    r"|re-?execute"
    r"|I\s+added\s+(?:the\s+)?(?:GitHub\s+)?token"
    r"|I\s+configured\s+(?:the\s+)?(?:GitHub\s+)?(?:token|credential)"
    r"|refresh\s+credentials?"
    r"|token\s+(?:is\s+)?(?:added|configured|ready|set)"
    r"|credential\s+(?:is\s+)?(?:added|configured|ready|set)"
    r")\b",
    re.I,
)

_AMBIGUOUS_RETRY_RX = re.compile(r"^\s*(?:retry|try\s+again)\s*\.?\s*$", re.I)

_LANE_STORE: dict[str, dict[str, Any]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "github_workflow_lane"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _load_state(session_id: str) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _LANE_STORE.get(session_id)
    if cached is not None:
        return dict(cached)

    from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
        get_resolved_workflow_lane_state,
    )

    state = get_resolved_workflow_lane_state(session_id=session_id)
    if state is not None:
        _LANE_STORE[session_id] = state
    return state


def _save_state(session_id: str, state: dict[str, Any]) -> None:
    session_id = (session_id or "default").strip()
    state["updated_at"] = datetime.now(UTC).isoformat()
    _LANE_STORE[session_id] = state
    from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
        persist_workflow_lane_state,
    )

    persist_workflow_lane_state(session_id, state)


def _clear_state(session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _LANE_STORE.pop(session_id, None)
    try:
        _session_path(session_id).unlink(missing_ok=True)
    except OSError:
        pass
    from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
        remove_workflow_lane_from_index,
    )

    remove_workflow_lane_from_index(session_id=session_id)


def clear_memory_cache_for_tests() -> None:
    """Clear in-process cache only (simulates process restart without losing durable state)."""
    _LANE_STORE.clear()
    from aethos_core.providers.github.workflow_lane import workflow_lane_lifecycle

    workflow_lane_lifecycle._RUNTIME_CTX.set(None)
    workflow_lane_lifecycle._INDEX_MEMORY = None


def clear_for_tests() -> None:
    _LANE_STORE.clear()
    from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
        clear_lifecycle_for_tests,
    )

    clear_lifecycle_for_tests()


def get_workflow_lane_state(*, session_id: str) -> dict[str, Any] | None:
    return _load_state(session_id)


def _resolve_repo(session_id: str) -> str:
    """Best-effort repo resolution from existing GitHub context."""
    try:
        from aethos_core.providers.github.context.github_context_store import (
            get_active_github_context,
            get_github_rerun_context,
        )

        ctx = get_active_github_context(session_id) or {}
        repo = str(ctx.get("repo_full_name") or "")
        if repo:
            return repo
        rerun = get_github_rerun_context(session_id) or {}
        repo = str(rerun.get("rerun_target_repo") or "")
        if repo:
            return repo
    except Exception:
        pass
    return "pilotmain/aethos"


def _resolve_base_branch(session_id: str) -> str:
    try:
        from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
            get_runtime_workflow_discovery,
        )

        discovery = get_runtime_workflow_discovery(session_id=session_id)
        if discovery:
            branch = str(discovery.get("default_branch") or "")
            if branch:
                return branch
    except Exception:
        pass
    return "main"


# ─── Intent Detection ────────────────────────────────────────────────────────

def is_workflow_lane_intent(text: str) -> bool:
    from aethos_core.providers.github.workflow_lane.workflow_lane_guards import (
        has_github_workflow_lane_intent,
        is_railway_mutation_context,
    )

    raw = text or ""
    if is_railway_mutation_context(raw):
        return False
    if has_github_workflow_lane_intent(raw):
        return True
    if _is_approve_with_state(text):
        return True
    return False


def _is_approve_with_state(text: str, session_id: str | None = None) -> bool:
    """Approve only matches if there's a pending creation plan."""
    if not _APPROVE_RX.search(text or ""):
        return False
    if session_id:
        state = _load_state(session_id)
        return state is not None and state.get("stage") == "creation_plan_ready"
    return any(
        v.get("stage") == "creation_plan_ready" for v in _LANE_STORE.values()
    )


def _is_cancel_with_state(text: str, session_id: str) -> bool:
    return bool(_CANCEL_RX.search(text or "")) and _load_state(session_id) is not None


# ─── Route Dispatch ──────────────────────────────────────────────────────────

def route_workflow_lane(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Top-level hard router for the GitHub workflow lane.

    Returns (body, intent, meta) or None if text is not a workflow lane prompt.
    """
    raw = (text or "").strip()
    if not raw:
        return None

    if _PUSH_MAIN_RX.search(raw) and _CREATION_RX.search(raw):
        return _handle_push_to_main(session_id)

    if _PUSH_MAIN_RX.search(raw):
        return _handle_push_to_main(session_id)

    if _APPROVE_RX.search(raw):
        state = _load_state(session_id)
        if state and state.get("stage") == "creation_plan_ready":
            return _handle_approve(session_id, state)

    if _CANCEL_RX.search(raw):
        return _handle_cancel(session_id)

    from aethos_core.providers.github.workflow_lane.workflow_execution_followup import (
        is_workflow_execution_followup,
        route_workflow_execution_followup,
    )

    if is_workflow_execution_followup(raw):
        followup = route_workflow_execution_followup(raw, session_id=session_id)
        if followup is not None:
            return followup

    if _WORKFLOW_LANE_EXPLICIT_RETRY_RX.search(raw):
        return _handle_retry(session_id, no_state_reply=True)

    if _AMBIGUOUS_RETRY_RX.match(raw):
        return _handle_retry(session_id, no_state_reply=False)

    if _CREATION_RX.search(raw):
        return _handle_creation(raw, session_id)

    if _PROPOSAL_RX.search(raw):
        return _handle_proposal(session_id)

    return None


# ─── Handlers ────────────────────────────────────────────────────────────────

def _handle_proposal(session_id: str) -> tuple[str, str, dict[str, str]]:
    repo = _resolve_repo(session_id)
    base_branch = _resolve_base_branch(session_id)
    yaml_body = compose_generic_ci_workflow_yaml(default_branch=base_branch)

    discovery = {
        "repository": repo,
        "default_branch": base_branch,
        "workflows_dir_found": False,
        "workflow_file_names": [],
        "workflow_files": [],
        "actions_status": "enabled",
    }
    body = compose_workflow_proposal_reply(discovery, repo_context={})

    _save_state(session_id, {
        "repo": repo,
        "file_path": ".github/workflows/ci.yml",
        "base_branch": base_branch,
        "branch": "add-ci-workflow",
        "proposal_yaml": yaml_body,
        "stage": "proposal_ready",
        "source": "workflow_lane",
        "created_at": datetime.now(UTC).isoformat(),
    })

    return (
        body,
        "workflow_discovery_proposal",
        _meta(session_id, stage="proposal_ready"),
    )


def _handle_creation(text: str, session_id: str) -> tuple[str, str, dict[str, str]]:
    state = _load_state(session_id)
    repo = state["repo"] if state else _resolve_repo(session_id)
    base_branch = state["base_branch"] if state else _resolve_base_branch(session_id)
    branch = state["branch"] if state else "add-ci-workflow"
    file_path = state["file_path"] if state else ".github/workflows/ci.yml"

    lines = [
        "I can prepare a governed workflow-file creation plan.",
        "",
        "**Target:**",
        f"- Repo: `{repo}`",
        f"- File: `{file_path}`",
        f"- Branch: `{branch}`",
        f"- PR target: `{base_branch}`",
        "",
        "**Execution steps** (after approval):",
        f"1. Create branch `{branch}` from `{base_branch}`",
        f"2. Add `{file_path}` with the proposed CI workflow",
        "3. Commit workflow file",
        f"4. Open PR → `{base_branch}`",
        "5. Verify GitHub Actions workflow run after PR",
        "",
        "No file has been created yet.",
        "",
        "This requires approval because it will modify the repository.",
        "",
        "Reply **approve** to execute, or **cancel** to discard.",
    ]

    new_state = {
        "repo": repo,
        "file_path": file_path,
        "base_branch": base_branch,
        "branch": branch,
        "proposal_yaml": (state or {}).get("proposal_yaml") or compose_generic_ci_workflow_yaml(default_branch=base_branch),
        "stage": "creation_plan_ready",
        "source": (state or {}).get("source") or "workflow_lane",
        "created_at": (state or {}).get("created_at") or datetime.now(UTC).isoformat(),
    }
    _save_state(session_id, new_state)

    return (
        "\n".join(lines),
        "workflow_creation_governed_plan",
        _meta(session_id, stage="creation_plan_ready"),
    )


def _handle_push_to_main(session_id: str) -> tuple[str, str, dict[str, str]]:
    state = _load_state(session_id)
    base_branch = state["base_branch"] if state else _resolve_base_branch(session_id)

    lines = [
        "I will not push this workflow directly to main.",
        "",
        "**Safer governed path:**",
        "- Create branch `add-ci-workflow`",
        "- Commit workflow file there",
        f"- Open PR to `{base_branch}`",
        "- Verify checks",
        "",
        "Direct main push is **T3** and blocked unless explicitly elevated.",
    ]

    return (
        "\n".join(lines),
        "workflow_creation_governed_plan",
        _meta(session_id, stage=(state or {}).get("stage") or "blocked_t3"),
    )


def _handle_cancel(session_id: str) -> tuple[str, str, dict[str, str]]:
    state = _load_state(session_id)

    if state is None:
        from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
            clear_pending_workflow_proposal,
            has_pending_workflow_proposal,
        )

        if has_pending_workflow_proposal(session_id=session_id):
            clear_pending_workflow_proposal(session_id=session_id)
            return (
                "Cancelled the pending workflow-file creation plan.\n\nNo file, branch, commit, push, or PR was created.",
                "workflow_creation_cancelled",
                _meta(session_id, stage="cancelled"),
            )
        return (
            "No pending GitHub workflow creation plan is active.",
            "workflow_lane_no_state",
            _meta(session_id, stage="no_state"),
        )

    _clear_state(session_id)
    from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
        clear_pending_workflow_proposal,
    )

    clear_pending_workflow_proposal(session_id=session_id)
    return (
        "Cancelled the pending workflow-file creation plan.\n\nNo file, branch, commit, push, or PR was created.",
        "workflow_creation_cancelled",
        _meta(session_id, stage="cancelled"),
    )


def _handle_approve(session_id: str, state: dict[str, Any]) -> tuple[str, str, dict[str, str]]:
    """Execute the governed workflow-file creation plan after user approval."""
    from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_execution_auth

    repo = state["repo"]
    file_path = state["file_path"]
    branch = state["branch"]
    base_branch = state["base_branch"]
    yaml_content = state.get("proposal_yaml") or ""

    if not yaml_content.strip():
        return (
            "Cannot execute: no workflow YAML content in the pending plan. "
            "Please start over with `draft workflow proposal`.",
            "workflow_execution_failed",
            _meta(session_id, stage="execution_failed"),
        )

    auth = resolve_execution_auth(provider="github", operation_type="workflow_file_creation", params={"target_name": repo})
    token = get_provider_api_token(provider="github", auth=auth)
    if not token:
        _save_state(session_id, {
            **state,
            "stage": "execution_blocked",
            "blocker": "missing_github_mutation_credential",
            "last_failed_step": "credential_resolution",
            "pr_opened": False,
            "branch_created": False,
            "file_committed": False,
            "workflow_run_triggered": False,
        })
        return (
            "Cannot execute: GitHub credential not configured for mutation execution.\n\n"
            "**Result:**\n"
            "- Branch created: no\n"
            "- Workflow file committed: no\n"
            "- PR opened: no\n"
            "- Workflow run triggered: no\n\n"
            "**Next step:**\n"
            "Configure a GitHub token with repo write access, then retry approval.",
            "workflow_execution_blocked",
            _meta(session_id, stage="execution_blocked"),
        )

    from aethos_core.providers.github.workflow_lane import workflow_lane_executor

    prior_progress = state.get("execution_progress") or None

    result = workflow_lane_executor.execute_workflow_file_creation(
        token,
        repo=repo,
        file_path=file_path,
        branch=branch,
        base_branch=base_branch,
        yaml_content=yaml_content,
        prior_progress=prior_progress,
    )

    progress = result.get("progress") or {}

    if result.get("ok"):
        pr_url = result.get("pr_url") or ""
        pr_number = result.get("pr_number")
        commit_sha = result.get("commit_sha") or ""
        reused = result.get("reused_pr", False)

        lines = [
            "Governed workflow-file creation **executed successfully**.",
            "",
            "**Result:**",
            f"- Branch: `{branch}`",
            f"- File: `{file_path}`",
            f"- Commit: `{commit_sha[:8]}`" if commit_sha else "- Commit: created",
        ]
        if pr_url:
            lines.append(f"- PR: [{pr_url.split('/')[-1] if '/' in pr_url else f'#{pr_number}'}]({pr_url})")
            if reused:
                lines.append("  *(existing PR reused)*")
        lines.extend([
            "",
            "**Next steps:**",
            "- Wait for GitHub Actions to trigger the first workflow run",
            "- Verify workflow appears in the Actions tab",
            "- Review and merge the PR when satisfied",
        ])

        _save_state(session_id, {
            **state,
            "stage": "executed",
            "execution_progress": progress,
            "execution_result": {
                "pr_url": pr_url,
                "pr_number": pr_number,
                "commit_sha": commit_sha,
                "branch": branch,
            },
        })

        return (
            "\n".join(lines),
            "workflow_creation_executed",
            _meta(session_id, stage="executed"),
        )
    else:
        step = result.get("step") or "unknown"
        detail = result.get("detail") or "Execution failed."

        _save_state(session_id, {
            **state,
            "stage": "execution_blocked",
            "blocker": f"execution_failed_at_{step}",
            "execution_progress": progress,
            "pr_opened": progress.get("pr_opened", False),
            "branch_created": progress.get("branch_created", False),
            "file_committed": progress.get("file_committed", False),
            "workflow_run_triggered": progress.get("workflow_run_detected", False),
        })

        lines = [
            "Governed workflow-file creation **failed**.",
            "",
            f"**Step:** `{step}`",
            f"**Detail:** {detail}",
            "",
            "No further changes were made. You can retry or cancel.",
        ]

        return (
            "\n".join(lines),
            "workflow_execution_failed",
            _meta(session_id, stage="execution_blocked"),
        )


def _handle_retry(
    session_id: str,
    *,
    no_state_reply: bool = True,
) -> tuple[str, str, dict[str, str]] | None:
    """Retry approval after credential has been configured."""
    state = _load_state(session_id)

    if state is None:
        if not no_state_reply:
            return None
        return (
            "No pending GitHub workflow creation plan is active.\n\n"
            "Start with `draft workflow proposal` to begin a new workflow creation lifecycle.",
            "workflow_lane_no_state",
            _meta(session_id, stage="no_state"),
        )

    stage = state.get("stage") or ""

    if stage == "executed":
        return (
            "The workflow creation plan has already been executed successfully.\n\n"
            "No retry is needed.",
            "workflow_lane_already_executed",
            _meta(session_id, stage="executed"),
        )

    if stage == "cancelled":
        return (
            "The workflow creation plan was cancelled.\n\n"
            "Start with `draft workflow proposal` to begin a new workflow creation lifecycle.",
            "workflow_lane_no_state",
            _meta(session_id, stage="cancelled"),
        )

    if stage not in ("execution_blocked", "creation_plan_ready"):
        return (
            "The workflow creation plan is not yet ready for approval.\n\n"
            f"Current stage: `{stage}`. Use `create this workflow file` to advance to the governed plan.",
            "workflow_lane_not_ready",
            _meta(session_id, stage=stage),
        )

    return _handle_approve(session_id, state)


def _meta(session_id: str, *, stage: str) -> dict[str, str]:
    return {
        "route_id": "github_workflow_lane",
        "matched_module": "providers.github.workflow_lane.workflow_lane_router",
        "provider": "github",
        "workflow_lane_stage": stage,
        "blocked_routes": "active_thread,generic_workflow_planner,project_template,llm_fallback",
    }
