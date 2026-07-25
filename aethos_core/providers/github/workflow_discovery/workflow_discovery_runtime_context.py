# SPDX-License-Identifier: Apache-2.0
"""Request-scoped workflow discovery runtime binding for live chat routing."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.github.context.github_context_store import (
    assert_valid_repo_context,
    get_active_github_context,
    get_github_rerun_context,
    save_github_rerun_context,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
    is_hard_workflow_discovery_next_steps_intent,
    is_hard_workflow_discovery_proposal_intent,
    is_no_workflow_files_discovery,
)

_RUNTIME_CTX: ContextVar["WorkflowDiscoveryRuntimeContext | None"] = ContextVar(
    "_workflow_discovery_runtime_ctx",
    default=None,
)

_BLOCKED_HANDLERS = (
    "project_template",
    "llm_fallback",
    "thread_continuation",
    "investigation_strategy",
    "capability_intro",
    "generative_fallback",
)


@dataclass
class WorkflowDiscoveryRuntimeContext:
    session_id: str = "default"
    workflow_discovery: dict[str, Any] | None = None
    has_no_workflows: bool = False
    github_repo: str = ""
    hydrated: bool = False
    hydration_source: str = ""
    hydration_trace: list[str] = field(default_factory=list)


def get_hydrated_runtime_context() -> WorkflowDiscoveryRuntimeContext | None:
    return _RUNTIME_CTX.get()


def clear_runtime_context_for_tests() -> None:
    _RUNTIME_CTX.set(None)


def _discovery_from_params(params: dict[str, Any]) -> dict[str, Any] | None:
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


def _job_session_ids(job: Any) -> set[str]:
    params = dict(getattr(job, "params", None) or {})
    ids = {
        str(getattr(job, "session_id", "") or "").strip(),
        str(params.get("session_id") or "").strip(),
    }
    return {item for item in ids if item}


def _repo_from_discovery(discovery: dict[str, Any]) -> str:
    return str(discovery.get("repository") or "").strip()


def _bind_runtime_context(ctx: WorkflowDiscoveryRuntimeContext) -> WorkflowDiscoveryRuntimeContext:
    _RUNTIME_CTX.set(ctx)
    return ctx


def _collect_from_job_store(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    from aethos_core.runtime.jobs import job_store

    session = (session_id or "default").strip() or "default"
    latest_any: tuple[dict[str, Any], str] | None = None

    for job in job_store.list_all():
        params = dict(job.params or {})
        discovery = _discovery_from_params(params)
        if not discovery:
            continue

        source = f"job_store:{getattr(job, 'id', 'unknown')}"
        job_sessions = _job_session_ids(job)
        if session in job_sessions:
            return discovery, source

        if latest_any is None:
            latest_any = (discovery, source)

    if latest_any is not None:
        return latest_any
    return None, ""


def _collect_from_durable_jobs(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    try:
        from aethos_core.jobs.job_state import list_jobs
    except Exception:
        return None, ""

    session = (session_id or "default").strip() or "default"
    latest_any: tuple[dict[str, Any], str] | None = None
    for job in list_jobs(limit=200):
        params = dict(job.get("params") or {})
        discovery = _discovery_from_params(params)
        if not discovery:
            continue
        source = f"durable_jobs:{job.get('job_id') or 'unknown'}"
        job_session = str(job.get("session_id") or params.get("session_id") or "").strip()
        if job_session == session:
            return discovery, source
        if latest_any is None:
            latest_any = (discovery, source)
    if latest_any is not None:
        return latest_any
    return None, ""


def _collect_from_rerun_context(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    rerun_ctx = get_github_rerun_context(session_id) or {}
    cached = rerun_ctx.get("workflow_discovery")
    if isinstance(cached, dict) and cached:
        return cached, "github_rerun_context"
    return None, ""


def _collect_from_route_trace(*, session_id: str) -> tuple[dict[str, Any] | None, str]:
    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id) or {}
        if str(trace.get("intent") or "") not in {
            "github_workflow_discovery_next_steps",
            "github_workflow_proposal",
            "workflow_discovery_next_steps",
            "workflow_discovery_proposal",
            "github_workflow_rerun_no_execution_followup",
        }:
            return None, ""
        repo = str(trace.get("repository") or "")
        if not repo:
            return None, ""
        return (
            {
                "repository": repo,
                "workflows_dir_found": False,
                "workflow_file_names": [],
                "workflow_files": [],
                "actions_status": str(trace.get("actions_status") or "unknown"),
                "default_branch": "main",
            },
            "route_trace",
        )
    except Exception:
        return None, ""


def _persist_hydrated_discovery(*, session_id: str, discovery: dict[str, Any], source: str) -> None:
    repo = _repo_from_discovery(discovery)
    valid, _ = assert_valid_repo_context(repo)
    payload: dict[str, Any] = {
        "workflow_discovery": discovery,
        "discovery_failure_reason": "no_workflow_runs",
        "hydration_source": source,
    }
    if valid:
        payload["rerun_target_repo"] = repo
    save_github_rerun_context(session_id, payload)


def hydrate_workflow_discovery_context(*, session_id: str = "default") -> WorkflowDiscoveryRuntimeContext:
    """Bind workflow discovery onto the active runtime turn before routing."""
    session = (session_id or "default").strip() or "default"
    trace: list[str] = []
    discovery: dict[str, Any] | None = None
    source = ""

    for collector in (
        lambda: _collect_from_rerun_context(session_id=session),
        lambda: _collect_from_job_store(session_id=session),
        lambda: _collect_from_durable_jobs(session_id=session),
        lambda: _collect_from_route_trace(session_id=session),
    ):
        found, found_source = collector()
        if found:
            discovery = found
            source = found_source
            trace.append(found_source)
            break

    if discovery is None:
        ctx = WorkflowDiscoveryRuntimeContext(session_id=session, hydrated=False, hydration_trace=["empty"])
        return _bind_runtime_context(ctx)

    if source not in {"github_rerun_context"}:
        _persist_hydrated_discovery(session_id=session, discovery=discovery, source=source)
        trace.append("github_rerun_context_rebound")

    repo = _repo_from_discovery(discovery)
    if not repo:
        active = get_active_github_context(session) or {}
        repo = str(active.get("repo_full_name") or "")

    ctx = WorkflowDiscoveryRuntimeContext(
        session_id=session,
        workflow_discovery=discovery,
        has_no_workflows=is_no_workflow_files_discovery(discovery),
        github_repo=repo,
        hydrated=True,
        hydration_source=source,
        hydration_trace=trace,
    )
    return _bind_runtime_context(ctx)


def get_runtime_workflow_discovery(*, session_id: str = "default") -> dict[str, Any] | None:
    bound = get_hydrated_runtime_context()
    if bound is not None and bound.session_id == ((session_id or "default").strip() or "default"):
        return bound.workflow_discovery
    hydrate_workflow_discovery_context(session_id=session_id)
    bound = get_hydrated_runtime_context()
    if bound is None:
        return None
    return bound.workflow_discovery


def runtime_has_no_workflows(*, session_id: str = "default") -> bool:
    bound = get_hydrated_runtime_context()
    session = (session_id or "default").strip() or "default"
    if bound is None or bound.session_id != session:
        bound = hydrate_workflow_discovery_context(session_id=session)
    return bool(bound.has_no_workflows)


def _preempted_handler_for_text(text: str) -> str | None:
    if is_hard_workflow_discovery_proposal_intent(text):
        return "workflow_discovery_proposal"
    if is_hard_workflow_discovery_next_steps_intent(text):
        return "workflow_discovery_next_steps"
    return None


def enforce_workflow_discovery_absolute_lane(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Force workflow discovery ownership when runtime says no workflow files exist."""
    bound = hydrate_workflow_discovery_context(session_id=session_id)
    handler = _preempted_handler_for_text(text)
    if not bound.has_no_workflows or handler is None:
        return None

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_hard_preemption,
    )

    routed = route_workflow_discovery_hard_preemption(text, session_id=session_id)
    if routed is None:
        return None
    body, intent, meta = routed
    meta.update(
        {
            "workflow_discovery_hydrated": "true",
            "workflow_discovery_hydration_source": bound.hydration_source,
            "has_no_workflows": "true",
            "github_repo": bound.github_repo,
            "workflow_discovery_preempted": "true",
            "preempted_handler": handler,
            "blocked_handlers": ",".join(_BLOCKED_HANDLERS),
            "workflow_discovery_runtime_binding": "absolute_lane",
        }
    )
    if bound.hydration_trace:
        meta["workflow_discovery_hydration_trace"] = " → ".join(bound.hydration_trace)
    return body, intent, meta


def enforce_workflow_discovery_absolute_lane_turn(
    text: str,
    *,
    session_id: str = "default",
):
    routed = enforce_workflow_discovery_absolute_lane(text, session_id=session_id)
    if routed is None:
        return None
    from aethos_core.chat.service import ChatTurnResult

    reply, intent, meta = routed
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )
