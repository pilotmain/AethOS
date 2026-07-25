# SPDX-License-Identifier: Apache-2.0
"""Workflow Execution Follow-Up — answers from durable blocked/failed lifecycle."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
    _ACTIVE_STAGES,
    get_hydrated_workflow_lane_context,
    get_resolved_workflow_lane_state,
)

_EXECUTION_FOLLOWUP_RX = re.compile(
    r"\b("
    r"did\s+(?:the\s+)?(?:PR|pull\s+request)\s+open"
    r"|(?:was|is)\s+(?:the\s+)?(?:PR|pull\s+request)\s+(?:opened|created)"
    r"|did\s+(?:the\s+)?workflow\s+run"
    r"|(?:was|is)\s+(?:the\s+)?workflow\s+(?:run|triggered)"
    r"|did\s+(?:the\s+)?(?:CI|workflow)\s+(?:trigger|start|execute)"
    r"|where\s+(?:is|was)\s+(?:the\s+)?(?:failure|error)\s+(?:boundary|point)"
    r"|what\s+(?:failed|broke|went\s+wrong|happened)"
    r"|what\s+(?:credential|token)\s+(?:is|was)\s+(?:missing|needed|required)"
    r"|which\s+(?:credential|token)"
    r"|why\s+(?:did|was)\s+(?:it|execution)\s+(?:block|fail|stop)"
    r"|status\s+of\s+(?:the\s+)?(?:workflow|execution|creation)"
    r"|execution\s+(?:status|result|outcome)"
    r"|what\s+completed\s+(?:successfully|so\s+far)"
    r"|what\s+(?:steps?\s+)?(?:succeeded|passed|worked)"
    r"|can\s+(?:we|I)\s+(?:safely\s+)?retry"
    r"|(?:is\s+it\s+)?safe\s+to\s+retry"
    r"|resume\s+execution"
    r"|continue\s+from\s+(?:the\s+)?(?:failed|last)\s+step"
    r"|what\s+were\s+we\s+doing\s+(?:earlier|before)"
    r"|where\s+did\s+we\s+leave\s+off"
    r")\b",
    re.I,
)

_PR_STATUS_RX = re.compile(
    r"\b(?:did\s+(?:the\s+)?(?:PR|pull\s+request)\s+open|(?:was|is)\s+(?:the\s+)?(?:PR|pull\s+request)\s+(?:opened|created))\b",
    re.I,
)

_WORKFLOW_RUN_RX = re.compile(
    r"\b(?:did\s+(?:the\s+)?(?:workflow|CI)\s+(?:run|trigger|start|execute)|(?:was|is)\s+(?:the\s+)?workflow\s+(?:run|triggered))\b",
    re.I,
)

_BOUNDARY_RX = re.compile(
    r"\b(?:where\s+(?:is|was)\s+(?:the\s+)?(?:failure|error)\s+(?:boundary|point)|why\s+(?:did|was)\s+(?:it|execution)\s+(?:block|fail|stop))\b",
    re.I,
)

_WHAT_FAILED_RX = re.compile(
    r"\b(?:what\s+(?:failed|broke|went\s+wrong|happened))\b",
    re.I,
)

_CREDENTIAL_RX = re.compile(
    r"\b(?:what\s+(?:credential|token)\s+(?:is|was)\s+(?:missing|needed|required)|which\s+(?:credential|token))\b",
    re.I,
)

_COMPLETED_RX = re.compile(
    r"\b(?:what\s+completed\s+(?:successfully|so\s+far)|what\s+(?:steps?\s+)?(?:succeeded|passed|worked))\b",
    re.I,
)

_SAFE_RETRY_RX = re.compile(
    r"\b(?:can\s+(?:we|I)\s+(?:safely\s+)?retry|(?:is\s+it\s+)?safe\s+to\s+retry)\b",
    re.I,
)

_RESUME_RX = re.compile(
    r"\b(?:resume\s+execution|continue\s+from\s+(?:the\s+)?(?:failed|last)\s+step)\b",
    re.I,
)


def is_workflow_execution_followup(text: str) -> bool:
    return bool(_EXECUTION_FOLLOWUP_RX.search(text or ""))


def has_active_workflow_lane_lifecycle(*, session_id: str = "default") -> bool:
    state = get_resolved_workflow_lane_state(session_id=session_id)
    return state is not None and str(state.get("stage") or "") in _ACTIVE_STAGES


def route_workflow_execution_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Route follow-up questions from durable workflow lane lifecycle state."""
    state = get_resolved_workflow_lane_state(session_id=session_id)
    if state is None:
        return None

    stage = str(state.get("stage") or "")
    if stage not in _ACTIVE_STAGES:
        return None

    raw = (text or "").strip()
    if not raw:
        return None

    if stage not in ("execution_blocked", "executed", "creation_plan_ready"):
        if not _EXECUTION_FOLLOWUP_RX.search(raw):
            return None

    blocker = state.get("blocker") or "unknown"
    repo = state.get("repo") or "unknown"
    file_path = state.get("file_path") or ".github/workflows/ci.yml"
    branch = state.get("branch") or "add-ci-workflow"
    progress = _merged_progress(state)

    bound = get_hydrated_workflow_lane_context()
    hydration = bound.hydration_source if bound else ""
    meta = _fmeta(session_id, stage=stage, hydration=hydration)

    if _CREDENTIAL_RX.search(raw):
        return _compose_credential_reply(file_path, branch), "workflow_execution_credential_guidance", meta

    if _WHAT_FAILED_RX.search(raw):
        return _compose_what_failed_reply(blocker, progress), "workflow_execution_blocked_followup", meta

    if _COMPLETED_RX.search(raw):
        return _compose_completed_reply(state, progress, blocker), "workflow_execution_blocked_followup", meta

    if _RESUME_RX.search(raw):
        return _compose_resume_execution_reply(blocker, progress), "workflow_execution_blocked_followup", meta

    if _SAFE_RETRY_RX.search(raw):
        return _compose_safe_retry_reply(progress, blocker), "workflow_execution_blocked_followup", meta

    if _PR_STATUS_RX.search(raw):
        return _compose_pr_status_reply(blocker, progress), "workflow_execution_blocked_followup", meta

    if _WORKFLOW_RUN_RX.search(raw):
        return _compose_workflow_run_reply(blocker, progress), "workflow_execution_blocked_followup", meta

    if _BOUNDARY_RX.search(raw):
        return _compose_boundary_reply(blocker, repo, file_path, progress), "workflow_execution_blocked_followup", meta

    return _compose_generic_blocked_reply(blocker, progress), "workflow_execution_blocked_followup", meta


def _merged_progress(state: dict[str, Any]) -> dict[str, Any]:
    progress = dict(state.get("execution_progress") or {})
    for key in (
        "branch_created",
        "file_committed",
        "pr_opened",
        "workflow_run_triggered",
        "last_successful_step",
        "last_failed_step",
        "execution_attempts",
        "branch_name",
        "commit_sha",
        "pr_url",
        "pr_number",
    ):
        if key in state and state[key] is not None:
            progress.setdefault(key, state[key])
    if state.get("workflow_run_triggered") and "workflow_run_detected" not in progress:
        progress["workflow_run_detected"] = state["workflow_run_triggered"]
    return progress


def _any_mutation_completed(progress: dict[str, Any]) -> bool:
    return bool(
        progress.get("branch_created")
        or progress.get("file_committed")
        or progress.get("pr_opened")
    )


def _compose_pr_status_reply(blocker: str, progress: dict[str, Any] | None = None) -> str:
    p = progress or {}
    if p.get("pr_opened"):
        pr_url = p.get("pr_url") or ""
        return (
            f"Yes — the PR was opened.\n\n"
            f"- PR: {pr_url}\n"
            f"- Branch: `{p.get('branch_name') or 'add-ci-workflow'}`"
        )
    return (
        "No — the PR did not open.\n\n"
        "The workflow creation plan was not fully executed.\n\n"
        "**Result:**\n"
        f"- Branch created: {'yes' if p.get('branch_created') else 'no'}\n"
        f"- Workflow file committed: {'yes' if p.get('file_committed') else 'no'}\n"
        "- PR opened: no\n"
        "- Workflow run triggered: no"
    )


def _compose_workflow_run_reply(blocker: str, progress: dict[str, Any] | None = None) -> str:
    p = progress or {}
    if p.get("workflow_run_detected"):
        return "Yes — a workflow run was detected for the pending change."
    return (
        "No — no workflow run was triggered.\n\n"
        "The workflow file was not created or pushed because execution did not complete."
    )


def _compose_boundary_reply(
    blocker: str, repo: str, file_path: str, progress: dict[str, Any] | None = None
) -> str:
    p = progress or {}
    if not _any_mutation_completed(p) and blocker == "missing_github_mutation_credential":
        return (
            "The failure boundary is **before GitHub mutation execution**.\n\n"
            f"AethOS prepared the workflow creation plan for `{repo}`, "
            "but GitHub mutation credentials are not configured, so:\n"
            "- No branch was created\n"
            "- No file was committed\n"
            "- No PR was opened\n"
            "- No CI run was triggered\n\n"
            "Configure the credential and retry approval, or cancel."
        )
    failed = p.get("last_failed_step") or _failed_step_from_blocker(blocker)
    lines = [
        f"The failure boundary is at step **`{failed}`**.",
        "",
        "**Completed before failure:**",
    ]
    if p.get("branch_created"):
        lines.append("- Branch created")
    if p.get("file_committed"):
        lines.append("- File committed")
    if p.get("pr_opened"):
        lines.append("- PR opened")
    if not _any_mutation_completed(p):
        lines.append("- None (blocked before mutation)")
    lines.extend(["", "Use `retry approval` to resume from the failed step."])
    return "\n".join(lines)


def _compose_credential_reply(file_path: str, branch: str) -> str:
    return (
        "GitHub mutation credential is missing.\n\n"
        "**Required:**\n"
        "- GitHub token with `repo` write access\n\n"
        "**Needed for:**\n"
        f"- Creating branch `{branch}`\n"
        f"- Committing `{file_path}`\n"
        "- Opening PR\n\n"
        "No mutation has been performed."
    )


def _compose_what_failed_reply(blocker: str, progress: dict[str, Any]) -> str:
    failed_step = progress.get("last_failed_step") or _failed_step_from_blocker(blocker)
    if blocker == "missing_github_mutation_credential":
        return (
            "Execution stopped during **credential resolution**.\n\n"
            "**Failed step:**\n"
            "- GitHub mutation credential lookup\n\n"
            "**Reason:**\n"
            "GitHub token with repo write access is not configured."
        )
    return (
        f"Execution stopped during **`{failed_step}`**.\n\n"
        f"**Reason:** {_blocker_reason(blocker)}"
    )


def _compose_completed_reply(
    state: dict[str, Any], progress: dict[str, Any], blocker: str
) -> str:
    stage = str(state.get("stage") or "")
    if not _any_mutation_completed(progress) and blocker == "missing_github_mutation_credential":
        return (
            "Workflow creation execution has not completed any mutation steps yet.\n\n"
            "**Current stage:**\n"
            "- Execution blocked before GitHub mutation execution\n\n"
            "**Completed:**\n"
            "- Proposal generated\n"
            "- Governed plan prepared\n\n"
            "**Not completed:**\n"
            "- Branch creation\n"
            "- File commit\n"
            "- PR creation\n"
            "- Workflow trigger"
        )

    completed: list[str] = ["- Proposal generated", "- Governed plan prepared"]
    if progress.get("branch_created"):
        completed.append(
            f"- Branch `{progress.get('branch_name') or state.get('branch') or 'add-ci-workflow'}`"
        )
    if progress.get("file_committed"):
        completed.append("- Workflow file committed")
    if progress.get("pr_opened"):
        completed.append("- PR opened")

    not_completed: list[str] = []
    if not progress.get("branch_created"):
        not_completed.append("- Branch creation")
    if not progress.get("file_committed"):
        not_completed.append("- File commit")
    if not progress.get("pr_opened"):
        not_completed.append("- PR creation")
    if not progress.get("workflow_run_detected"):
        not_completed.append("- Workflow trigger")

    lines = [
        "Workflow creation execution progress:",
        "",
        f"**Current stage:** `{stage}`",
        "",
        "**Completed:**",
    ]
    lines.extend(completed)
    if not_completed:
        lines.extend(["", "**Not completed:**"])
        lines.extend(not_completed)
    return "\n".join(lines)


def _compose_resume_execution_reply(blocker: str, progress: dict[str, Any]) -> str:
    resume_from = progress.get("last_failed_step") or _failed_step_from_blocker(blocker)
    if blocker == "missing_github_mutation_credential":
        resume_from = "credential resolution"
    return (
        "Execution can resume from:\n"
        f"- **{resume_from}**\n\n"
        "**Next step:**\n"
        "Configure GitHub repo-write token, then retry approval."
    )


def _compose_safe_retry_reply(progress: dict[str, Any], blocker: str) -> str:
    if not _any_mutation_completed(progress) and blocker == "missing_github_mutation_credential":
        return (
            "Yes — safe retry is available.\n\n"
            "No branch, commit, PR, or workflow run was created, so retry has **no duplicate-risk**.\n\n"
            "Configure GitHub repo-write token, then use `retry approval`."
        )

    safe_reasons: list[str] = []
    if progress.get("branch_created"):
        safe_reasons.append("Branch already exists — will be reused, not duplicated.")
    if progress.get("file_committed"):
        safe_reasons.append("File already committed — will be detected and skipped.")
    if progress.get("pr_opened"):
        safe_reasons.append("PR already exists — will be reused.")
    if not safe_reasons:
        safe_reasons.append("No partial state — clean retry.")

    lines = [
        "**Safe to retry: yes**",
        "",
        "**Idempotency:**",
    ]
    for s in safe_reasons:
        lines.append(f"- {s}")
    lines.extend(["", "Use `retry approval` to resume from the failed step."])
    return "\n".join(lines)


def _compose_generic_blocked_reply(blocker: str, progress: dict[str, Any]) -> str:
    return _compose_completed_reply(
        {"stage": "execution_blocked"},
        progress,
        blocker,
    )


def _failed_step_from_blocker(blocker: str) -> str:
    if blocker == "missing_github_mutation_credential":
        return "credential_resolution"
    if blocker.startswith("execution_failed_at_"):
        return blocker.removeprefix("execution_failed_at_")
    return blocker or "unknown"


def _blocker_reason(blocker: str) -> str:
    if blocker == "missing_github_mutation_credential":
        return "GitHub mutation credentials are not configured"
    if blocker.startswith("execution_failed_at_"):
        step = blocker.removeprefix("execution_failed_at_")
        return f"execution failed at step `{step}`"
    return blocker or "an unknown issue"


def _fmeta(session_id: str, *, stage: str, hydration: str = "") -> dict[str, str]:
    meta = {
        "route_id": "github_workflow_lane",
        "matched_module": "providers.github.workflow_lane.workflow_execution_followup",
        "provider": "github",
        "workflow_lane_stage": stage,
        "blocked_routes": (
            "active_thread,generic_workflow_planner,correlation_router,"
            "investigation_strategy,world_model,llm_fallback"
        ),
        "workflow_lane_hydrated": "true",
    }
    if hydration:
        meta["workflow_lane_hydration_source"] = hydration
    return meta
