# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun follow-ups when preflight ended without execution."""

from __future__ import annotations

import logging
import re
from typing import Any

from aethos_core.providers.github.context.github_context_store import (
    assert_valid_repo_context,
    get_active_github_context,
    get_github_rerun_context,
)
from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
    compose_workflow_discovery_next_steps,
    compose_workflow_proposal_reply,
    is_workflow_next_steps_intent,
    is_workflow_proposal_intent,
)

_NO_EXEC_PREFLIGHT_STATUSES = frozenset(
    {
        "no_action_available",
        "needs_workflow_resolution",
        "discovery_failed",
    }
)

_NO_EXEC_DISCOVERY_REASONS = frozenset(
    {
        "no_workflow_runs",
        "no_failed_workflow",
        "no_failed_workflow_found",
        "discovery_failed",
        "no_rerunnable_candidate",
    }
)

_NO_EXEC_FOLLOWUP_RX = re.compile(
    r"\b("
    r"what\s+happened\s+after\s+approval"
    r"|did\s+deployment\s+reach\s+runtime"
    r"|where\s+is\s+the\s+failure\s+boundary"
    r"|did\s+the\s+mutation\s+actually\s+(?:run|execute|happen)"
    r"|did\s+the\s+restart\s+actually\s+happen"
    r"|is\s+it\s+done"
    r"|did\s+it\s+deploy\s+after\s+(?:the\s+)?rerun"
    r"|why\s+no\s+workflow\s+runs?"
    r"|why\s+can'?t\s+rerun"
    r"|how\s+do\s+i\s+enable\s+workflow"
    r"|what\s+should\s+(?:i|we)\s+do\s+next"
    r"|what\s+next"
    r"|how\s+should\s+(?:i|we)\s+continue"
    r"|draft\s+(?:a\s+)?workflow\s+proposal"
    r"|create\s+(?:a\s+)?ci\s+workflow\s+proposal"
    r"|create\s+ci\s+(?:workflow\s+)?proposal"
    r"|create\s+ci\s+workflow"
    r"|prepare\s+(?:the\s+)?workflow\s+file"
    r"|propose\s+github\s+actions\s+workflow"
    r"|draft\s+ci\.yml"
    r"|generate\s+ci\s+workflow"
    r"|create\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|add\s+(?:the\s+|this\s+)?workflow\s+file"
    r"|write\s+(?:the\s+|this\s+)?ci\.yml"
    r"|add\s+ci\.yml"
    r"|create\s+(?:the\s+|this\s+)?ci\.yml"
    r"|implement\s+(?:the\s+|this\s+)?workflow"
    r"|set\s+up\s+(?:the\s+|this\s+)?workflow"
    r"|make\s+(?:the\s+|this\s+)?workflow\s+file"
    r")\b",
    re.I,
)


def is_rerun_no_execution_followup_intent(text: str) -> bool:
    if bool(_NO_EXEC_FOLLOWUP_RX.search(text or "")):
        return True
    return _is_workflow_discovery_delegation_intent(text)


def _is_workflow_discovery_delegation_intent(text: str) -> bool:
    from aethos_core.providers.github.workflow_discovery.workflow_creation_plan import (
        is_workflow_creation_intent,
    )
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        is_hard_workflow_discovery_next_steps_intent,
        is_hard_workflow_discovery_proposal_intent,
    )

    return (
        is_hard_workflow_discovery_next_steps_intent(text)
        or is_hard_workflow_discovery_proposal_intent(text)
        or is_workflow_creation_intent(text)
    )


def _discovery_from_job_params(params: dict[str, Any]) -> dict[str, Any] | None:
    pf = dict(params.get("mutation_preflight") or {})
    resolution = dict(params.get("workflow_resolution") or pf.get("workflow_resolution") or {})
    debug = dict(params.get("workflow_resolution_debug") or pf.get("workflow_resolution_debug") or {})
    for candidate in (
        params.get("workflow_discovery"),
        resolution.get("workflow_discovery"),
        debug.get("workflow_discovery"),
        pf.get("workflow_discovery"),
    ):
        if isinstance(candidate, dict) and candidate:
            return candidate
    return None


def _job_matches_session(job: Any, session_id: str) -> bool:
    params = dict(getattr(job, "params", None) or {})
    session = (session_id or "default").strip() or "default"
    ids = {
        str(getattr(job, "session_id", "") or "").strip(),
        str(params.get("session_id") or "").strip(),
    }
    return session in ids


def is_rerun_no_execution_state(*, session_id: str = "default") -> bool:
    return find_latest_rerun_preflight_noop(session_id=session_id) is not None


def find_latest_rerun_preflight_noop(*, session_id: str = "default") -> dict[str, Any] | None:
    from aethos_core.runtime.jobs import job_store

    latest_preflight: dict[str, Any] | None = None
    latest_fallback: dict[str, Any] | None = None
    for job in reversed(job_store.list_all()):
        if job.job_type != "mutation_preflight":
            continue
        params = dict(job.params or {})
        if str(params.get("provider") or "") != "github":
            continue
        if str(params.get("operation_type") or "") != "workflow_rerun":
            continue
        preflight_status = _preflight_status(params)
        discovery_reason = _discovery_failure_reason(params)
        if not _is_no_execution_preflight(preflight_status, discovery_reason):
            continue
        entry = {
            "preflight_job_id": job.id,
            "repository": _resolve_repository(params, session_id=session_id),
            "preflight_status": preflight_status,
            "discovery_failure_reason": discovery_reason,
            "summary": str(params.get("summary") or getattr(job, "preview", "") or ""),
            "no_action_reason": str(params.get("no_action_reason") or ""),
            "workflow_discovery": _discovery_from_job_params(params),
        }
        if _job_matches_session(job, session_id):
            latest_preflight = entry
            break
        if latest_fallback is None:
            latest_fallback = entry

    if latest_preflight is None:
        latest_preflight = latest_fallback

    if latest_preflight is None:
        rerun_ctx = get_github_rerun_context(session_id) or {}
        status = str(rerun_ctx.get("verification_status") or "")
        reason = str(rerun_ctx.get("discovery_failure_reason") or "")
        if _is_no_execution_preflight(status, reason):
            cached = rerun_ctx.get("workflow_discovery")
            latest_preflight = {
                "preflight_job_id": str(rerun_ctx.get("preflight_job_id") or ""),
                "repository": str(rerun_ctx.get("rerun_target_repo") or ""),
                "preflight_status": status,
                "discovery_failure_reason": reason,
                "summary": "",
                "no_action_reason": "",
                "workflow_discovery": cached if isinstance(cached, dict) else None,
            }

    if latest_preflight is None:
        return None
    if _has_github_rerun_execution(session_id=session_id):
        return None
    return latest_preflight


def compose_rerun_no_execution_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    state = find_latest_rerun_preflight_noop(session_id=session_id)
    if state is not None:
        delegated = _try_workflow_discovery_delegation(text, session_id=session_id, state=state)
        if delegated is not None:
            return delegated

    if not is_rerun_no_execution_followup_intent(text):
        return None
    if state is None:
        return None

    repo = _validated_repo(
        state.get("repository"),
        (get_active_github_context(session_id) or {}).get("repo_full_name"),
        (get_github_rerun_context(session_id) or {}).get("rerun_target_repo"),
    ) or "the diagnosed repo"
    lower = (text or "").lower()
    discovery = _resolve_workflow_discovery(session_id=session_id, state=state, repository=repo)
    repo_context = get_active_github_context(session_id) or {}

    if is_workflow_proposal_intent(text) and discovery:
        body = compose_workflow_proposal_reply(discovery, repo_context=repo_context)
        intent = "github_workflow_proposal"
    elif is_workflow_next_steps_intent(text) and discovery:
        body = compose_workflow_discovery_next_steps(discovery, repo_context=repo_context)
        intent = "github_workflow_discovery_next_steps"
    elif _is_workflow_discovery_question(lower) and discovery:
        body = _compose_workflow_discovery_reply(discovery)
        intent = "github_workflow_rerun_no_execution_followup"
    elif "what happened after approval" in lower or "did the mutation actually" in lower or "is it done" in lower:
        body = _compose_after_approval_reply(repo=repo, state=state, discovery=discovery)
        intent = "github_workflow_rerun_no_execution_followup"
    elif "deployment reach runtime" in lower or "deploy after" in lower:
        body = _compose_deployment_reply(repo=repo, state=state, discovery=discovery)
        intent = "github_workflow_rerun_no_execution_followup"
    elif "failure boundary" in lower:
        body = _compose_boundary_reply(repo=repo, state=state, discovery=discovery)
        intent = "github_workflow_rerun_no_execution_followup"
    else:
        body = _compose_after_approval_reply(repo=repo, state=state, discovery=discovery)
        intent = "github_workflow_rerun_no_execution_followup"

    return (
        body,
        intent,
        {
            "route_id": "github_rerun_no_execution",
            "matched_module": "providers.github.mutations.rerun_no_execution_followup",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "repository": repo,
            "preflight_status": str(state.get("preflight_status") or ""),
            "discovery_failure_reason": str(state.get("discovery_failure_reason") or ""),
            "preflight_job_id": str(state.get("preflight_job_id") or ""),
            "rerun_executed": "false",
            "proposal_only": "true" if intent == "github_workflow_proposal" else "false",
        },
    )


def _try_workflow_discovery_delegation(
    text: str,
    *,
    session_id: str,
    state: dict[str, Any],
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.workflow_discovery.workflow_creation_plan import (
        is_workflow_creation_intent,
        compose_governed_workflow_creation_plan,
    )
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        is_hard_workflow_discovery_proposal_intent,
    )

    proposal_matched = is_hard_workflow_discovery_proposal_intent(text) or is_workflow_proposal_intent(text)
    creation_matched = is_workflow_creation_intent(text)

    if not proposal_matched and not creation_matched and not _is_workflow_discovery_delegation_intent(text):
        return None

    repo = _validated_repo(
        state.get("repository"),
        (get_active_github_context(session_id) or {}).get("repo_full_name"),
        (get_github_rerun_context(session_id) or {}).get("rerun_target_repo"),
    ) or "the diagnosed repo"
    repo_context = get_active_github_context(session_id) or {}
    discovery = _resolve_workflow_discovery(session_id=session_id, state=state, repository=repo)

    forced = False
    if not discovery and (proposal_matched or creation_matched):
        discovery = _synthesize_minimal_discovery(state=state, repository=repo)
        forced = True

    if not discovery:
        return None

    if creation_matched:
        body = compose_governed_workflow_creation_plan(discovery, repo_context=repo_context, text=text)
        delegated_intent = "workflow_creation_governed_plan"
    elif proposal_matched:
        body = compose_workflow_proposal_reply(discovery, repo_context=repo_context)
        delegated_intent = "workflow_discovery_proposal"
    else:
        body = compose_workflow_discovery_next_steps(discovery, repo_context=repo_context)
        delegated_intent = "workflow_discovery_next_steps"

    if delegated_intent in ("workflow_discovery_proposal", "workflow_creation_governed_plan"):
        from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
            save_pending_workflow_proposal,
        )
        from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
            compose_generic_ci_workflow_yaml,
        )

        default_branch = str(discovery.get("default_branch") or "main")
        save_pending_workflow_proposal(
            session_id=session_id,
            repo=repo,
            file_path=".github/workflows/ci.yml",
            branch="add-ci-workflow",
            base_branch=default_branch,
            proposal_yaml=compose_generic_ci_workflow_yaml(default_branch=default_branch),
        )

    _log = logging.getLogger(__name__)
    _log.info(
        "workflow_proposal_delegation_executed repo=%s delegated_intent=%s forced=%s body_len=%d",
        repo,
        delegated_intent,
        forced,
        len(body or ""),
    )

    return (
        body,
        delegated_intent,
        {
            "route_id": "github_rerun_no_execution",
            "matched_module": "providers.github.mutations.rerun_no_execution_followup",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "repository": repo,
            "preflight_status": str(state.get("preflight_status") or ""),
            "discovery_failure_reason": str(state.get("discovery_failure_reason") or ""),
            "preflight_job_id": str(state.get("preflight_job_id") or ""),
            "rerun_executed": "false",
            "proposal_only": "true" if delegated_intent == "workflow_discovery_proposal" else "false",
            "governed_plan": "true" if delegated_intent == "workflow_creation_governed_plan" else "false",
            "workflow_discovery_delegated": "true",
            "workflow_discovery_delegation_executed": "true",
            "delegated_handler": delegated_intent,
            "workflow_discovery_proposal_forced": "true" if forced else "false",
            "blocked_handlers": "llm_fallback,project_template,generic_workflow_planner",
        },
    )


def _compose_after_approval_reply(*, repo: str, state: dict[str, Any], discovery: dict[str, Any] | None) -> str:
    reason_detail = _discovery_detail(state, discovery)
    lines = [
        "There was no approval/execution step for this GitHub workflow rerun.",
        "",
        f"The preflight inspected **{repo}** but {reason_detail}.",
        "",
        "Result:",
        "- no rerun performed",
        "- no mutation executed",
        "- no downstream deployment expected",
    ]
    if discovery:
        lines.extend(["", *_workflow_discovery_block(discovery)])
    else:
        lines.extend(
            [
                "",
                "Next useful step:",
                "Inspect recent workflow runs or verify GitHub Actions is enabled for this repo.",
            ]
        )
    return "\n".join(lines)


def _compose_deployment_reply(*, repo: str, state: dict[str, Any], discovery: dict[str, Any] | None) -> str:
    reason_detail = _discovery_detail(state, discovery)
    lines = [
        "No deployment was expected because no GitHub workflow rerun was executed.",
        "",
        f"The preflight {reason_detail} for **{repo}**.",
        "",
        "Result:",
        "- no rerun performed",
        "- Vercel/Railway were not triggered by a governed rerun",
    ]
    if discovery:
        lines.extend(["", *_workflow_discovery_block(discovery, include_next_steps=False)])
    return "\n".join(lines)


def _compose_boundary_reply(*, repo: str, state: dict[str, Any], discovery: dict[str, Any] | None) -> str:
    reason_detail = _discovery_detail(state, discovery)
    github_boundary = "no workflow run available to rerun"
    if discovery and not discovery.get("workflows_dir_found"):
        github_boundary = "no workflow files configured"
    lines = [
        "There is no new failure boundary from a rerun because no rerun was executed.",
        "",
        f"The preflight inspected **{repo}** but {reason_detail}.",
        "",
        "Current boundary:",
        f"- GitHub: {github_boundary}",
        "- Vercel/Railway: not triggered",
    ]
    if discovery:
        lines.extend(["", f"Likely reason: {discovery.get('likely_reason') or 'Unknown.'}"])
    return "\n".join(lines)


def _compose_workflow_discovery_reply(discovery: dict[str, Any]) -> str:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_reply import (
        compose_workflow_discovery_reply,
    )

    return compose_workflow_discovery_reply(discovery)


def _workflow_discovery_block(discovery: dict[str, Any], *, include_next_steps: bool = True) -> list[str]:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_reply import (
        compose_workflow_discovery_sections,
    )

    sections = compose_workflow_discovery_sections(discovery)
    if not include_next_steps:
        trimmed: list[str] = []
        for line in sections:
            if line == "Next steps:":
                break
            trimmed.append(line)
        return trimmed
    return sections


def _synthesize_minimal_discovery(*, state: dict[str, Any], repository: str) -> dict[str, Any]:
    """Synthesize a minimal workflow_discovery when full context is unavailable.

    This ensures proposal replies can always be generated in no-execution state
    even if the live discovery context was lost between turns.
    """
    reason = str(state.get("discovery_failure_reason") or "no_workflow_runs")
    workflows_dir_found = reason not in ("no_workflow_files", "no_workflows_dir")
    return {
        "repository": repository,
        "workflows_dir_found": workflows_dir_found,
        "workflow_file_names": [],
        "workflow_files": [],
        "actions_status": "enabled",
        "default_branch": "main",
        "likely_reason": reason,
    }


def _is_workflow_discovery_question(lower: str) -> bool:
    return any(
        phrase in lower
        for phrase in (
            "why no workflow run",
            "why can't rerun",
            "why cant rerun",
            "how do i enable workflow",
        )
    )


def _resolve_workflow_discovery(
    *,
    session_id: str,
    state: dict[str, Any],
    repository: str,
) -> dict[str, Any] | None:
    cached = state.get("workflow_discovery")
    if isinstance(cached, dict) and cached:
        return cached

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        get_runtime_workflow_discovery,
        hydrate_workflow_discovery_context,
    )

    hydrate_workflow_discovery_context(session_id=session_id)
    hydrated = get_runtime_workflow_discovery(session_id=session_id)
    if isinstance(hydrated, dict) and hydrated:
        return hydrated

    from aethos_core.runtime.jobs import job_store

    job_id = str(state.get("preflight_job_id") or "")
    if job_id:
        job = job_store.get(job_id)
        if job:
            discovered = _discovery_from_job_params(dict(job.params or {}))
            if discovered:
                return discovered
    rerun_ctx = get_github_rerun_context(session_id) or {}
    cached = rerun_ctx.get("workflow_discovery")
    if isinstance(cached, dict) and cached:
        return cached
    if str(state.get("discovery_failure_reason") or "") != "no_workflow_runs":
        return None
    token = _resolve_github_token()
    if not token or not repository:
        return None
    try:
        from aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis import (
            diagnose_workflow_run_absence,
        )

        return diagnose_workflow_run_absence(token, repository=repository)
    except Exception:
        return None


def _resolve_github_token() -> str:
    from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_execution_auth

    auth = resolve_execution_auth(provider="github", operation_type="workflow_runs", params={})
    return get_provider_api_token(provider="github", auth=auth) or ""


def _discovery_detail(state: dict[str, Any], discovery: dict[str, Any] | None = None) -> str:
    if discovery and discovery.get("likely_reason"):
        return str(discovery["likely_reason"]).rstrip(".")
    reason = str(state.get("discovery_failure_reason") or "").lower()
    status = str(state.get("preflight_status") or "").lower()
    if reason == "no_failed_workflow" or status == "no_action_available":
        return "could not find a failed workflow run available to rerun"
    if reason == "no_workflow_runs":
        return "could not find a workflow run available to rerun"
    if reason == "no_rerunnable_candidate":
        return "could not find a rerunnable workflow run"
    if reason in {"discovery_failed", "workflow_runs_fetch_failed", "provider_auth_failure"}:
        return f"could not complete workflow discovery ({reason.replace('_', ' ')})"
    if status == "needs_workflow_resolution":
        return "could not find a workflow run available to rerun"
    no_action = str(state.get("no_action_reason") or "").strip()
    if no_action:
        return no_action
    summary = str(state.get("summary") or "").strip()
    if "no workflow run" in summary.lower():
        return "could not find a workflow run available to rerun"
    if "no failed workflow" in summary.lower():
        return "could not find a failed workflow run available to rerun"
    return "could not find a workflow run available to rerun"


def _is_no_execution_preflight(preflight_status: str, discovery_reason: str) -> bool:
    status = str(preflight_status or "").lower()
    reason = str(discovery_reason or "").lower()
    if status in _NO_EXEC_PREFLIGHT_STATUSES:
        return True
    if reason in _NO_EXEC_DISCOVERY_REASONS:
        return True
    return False


def _preflight_status(params: dict[str, Any]) -> str:
    pf = dict(params.get("mutation_preflight") or {})
    return str(params.get("preflight_status") or pf.get("preflight_status") or "")


def _discovery_failure_reason(params: dict[str, Any]) -> str:
    pf = dict(params.get("mutation_preflight") or {})
    resolution = dict(params.get("workflow_resolution") or pf.get("workflow_resolution") or {})
    debug = dict(params.get("workflow_resolution_debug") or pf.get("workflow_resolution_debug") or {})
    return str(
        params.get("discovery_failure_reason")
        or pf.get("discovery_failure_reason")
        or resolution.get("discovery_failure_reason")
        or debug.get("discovery_failure_reason")
        or ""
    )


def _resolve_repository(params: dict[str, Any], *, session_id: str) -> str:
    pf = dict(params.get("mutation_preflight") or {})
    resolution = dict(params.get("workflow_resolution") or pf.get("workflow_resolution") or {})
    for candidate in (
        params.get("target_name"),
        pf.get("target_name"),
        resolution.get("repository"),
        (get_github_rerun_context(session_id) or {}).get("rerun_target_repo"),
        (get_active_github_context(session_id) or {}).get("repo_full_name"),
    ):
        repo = str(candidate or "").strip()
        valid, _ = assert_valid_repo_context(repo)
        if valid:
            return repo
    return ""


def _validated_repo(*candidates: Any) -> str:
    for candidate in candidates:
        repo = str(candidate or "").strip()
        valid, _ = assert_valid_repo_context(repo)
        if valid:
            return repo
    return ""


def _has_github_rerun_execution(*, session_id: str) -> bool:
    from aethos_core.runtime.jobs import job_store

    for job in reversed(job_store.list_all()):
        if not _job_matches_session(job, session_id):
            continue
        if job.job_type != "mutation_execution":
            continue
        params = dict(job.params or {})
        if str(params.get("provider") or "") != "github":
            continue
        if str(params.get("operation_type") or "") != "workflow_rerun":
            continue
        if params.get("executed") is False or str(params.get("execution_state") or "") == "execution_failed":
            continue
        return True
    return False
