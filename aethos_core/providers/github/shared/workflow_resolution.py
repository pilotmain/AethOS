# SPDX-License-Identifier: Apache-2.0
"""Shared GitHub workflow discovery — readonly + mutation convergence (Phase 9.6.5)."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import find_repository_by_name, parse_owner_repo
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs

_DEFAULT_QUERY_LIMIT = 20
_ACTIVE_RUN_STATUSES = frozenset({"queued", "in_progress", "waiting", "requested", "pending"})
_RERUNNABLE_CONCLUSIONS = frozenset(
    {"success", "failure", "cancelled", "timed_out", "action_required", "stale", "skipped", "neutral", ""}
)


def _parse_ts(value: Any) -> float:
    if not value:
        return 0.0
    raw = str(value)
    try:
        from datetime import datetime

        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return 0.0


def resolve_repository(token: str, *, repository: str) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        found = find_repository_by_name(token, repository)
        if found:
            owner, repo = parse_owner_repo(str(found.get("full_name") or ""))
            if owner and repo:
                return {
                    "ok": True,
                    "full_name": f"{owner}/{repo}",
                    "owner": owner,
                    "repo": repo,
                    "repository_id": found.get("repo_id"),
                    "default_branch": found.get("default_branch"),
                }
    if not owner or not repo:
        return {"ok": False, "error": f"Repository `{repository}` could not be resolved."}
    return {"ok": True, "full_name": f"{owner}/{repo}", "owner": owner, "repo": repo}


def _run_snapshot(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": run.get("id"),
        "workflow_id": run.get("workflow_id"),
        "name": run.get("name"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "run_number": run.get("run_number"),
        "created_at": run.get("created_at"),
        "head_branch": run.get("head_branch"),
    }


def _is_rerunnable_run(run: dict[str, Any]) -> tuple[bool, str | None]:
    status = str(run.get("status") or "").lower()
    if status in _ACTIVE_RUN_STATUSES:
        return False, "actively_running"
    if status == "completed":
        conclusion = str(run.get("conclusion") or "").lower()
        if conclusion in _RERUNNABLE_CONCLUSIONS or conclusion in ("none", "null"):
            return True, None
        return True, None
    return False, f"non_terminal_status_{status or 'unknown'}"


def _conclusion_priority(run: dict[str, Any]) -> int:
    conclusion = str(run.get("conclusion") or "").lower()
    if conclusion == "failure":
        return 0
    if conclusion == "cancelled":
        return 1
    if conclusion == "timed_out":
        return 2
    if conclusion == "success":
        return 3
    return 4


def _select_rerunnable_candidate(runs: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    rejections: list[dict[str, Any]] = []
    rerunnable: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        ok, reason = _is_rerunnable_run(run)
        snap = _run_snapshot(run)
        if ok:
            rerunnable.append(run)
        else:
            rejections.append({**snap, "rejection_reason": reason})
    if not rerunnable:
        return None, rejections
    rerunnable.sort(
        key=lambda r: (_parse_ts(r.get("created_at")), int(r.get("run_number") or 0)),
        reverse=True,
    )
    return rerunnable[0], rejections


def _build_discovery_diagnostics(
    *,
    repository: str | None,
    runs: list[dict[str, Any]],
    rerunnable: list[dict[str, Any]],
    rejections: list[dict[str, Any]],
    selected: dict[str, Any] | None,
    query_limit: int,
    discovery_failure_reason: str | None = None,
) -> dict[str, Any]:
    states: list[str] = []
    workflow_ids: list[Any] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        st = str(run.get("status") or "unknown")
        if st not in states:
            states.append(st)
        wf = run.get("workflow_id")
        if wf is not None and wf not in workflow_ids:
            workflow_ids.append(wf)
    return {
        "repository": repository,
        "workflow_candidates_found": len(runs),
        "rerunnable_candidates_found": len(rerunnable),
        "candidate_states": states,
        "workflow_scope": "all",
        "query_limit": query_limit,
        "workflow_ids_seen": workflow_ids,
        "discovery_failure_reason": discovery_failure_reason,
        "raw_candidates": [_run_snapshot(r) for r in runs if isinstance(r, dict)],
        "rejections": rejections,
        "selected_run_id": selected.get("id") if selected else None,
        "selected_status": selected.get("status") if selected else None,
        "selected_conclusion": selected.get("conclusion") if selected else None,
    }


def resolve_workflow_run_candidates(
    token: str,
    *,
    repository: str,
    limit: int = _DEFAULT_QUERY_LIMIT,
) -> dict[str, Any]:
    """Repo-scoped workflow run listing — identical path for readonly + mutation."""
    repo = resolve_repository(token, repository=repository)
    if not repo.get("ok"):
        return {
            "ok": False,
            "error": repo.get("error"),
            "runs": [],
            "repository": repository,
            "discovery_failure_reason": "repository_unresolved",
        }
    full_name = str(repo["full_name"])
    payload = fetch_workflow_runs(token, repository=full_name, limit=limit)
    if not payload.get("ok"):
        return {
            "ok": False,
            "error": str(payload.get("error") or "Could not list workflow runs."),
            "runs": [],
            "repository": full_name,
            "discovery_failure_reason": "workflow_runs_fetch_failed",
        }
    runs = payload.get("runs") or []
    return {
        "ok": True,
        "repository": full_name,
        "runs": runs,
        "run_count": len(runs),
        "workflow_scope": "all",
        "query_limit": limit,
    }


def discover_workflow_rerun_from_readonly_substrate(
    *,
    repository: str,
    auth: dict[str, Any],
    limit: int = _DEFAULT_QUERY_LIMIT,
    readonly_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mutation discovery via readonly adapter / artifact — same substrate as workflow_runs execution."""
    from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_readonly_adapter
    from aethos_core.providers.github.shared.auth_diagnostics import github_discovery_auth_diagnostics

    discovery_source = "readonly_adapter"
    candidates: dict[str, Any] | None = None

    if readonly_artifact and isinstance(readonly_artifact.get("runs"), list) and readonly_artifact.get("runs"):
        candidates = {
            "ok": True,
            "repository": readonly_artifact.get("repository") or repository,
            "runs": readonly_artifact.get("runs") or [],
            "run_count": len(readonly_artifact.get("runs") or []),
            "query_limit": limit,
        }
        discovery_source = str(readonly_artifact.get("discovery_source") or "readonly_execution_artifact")
    else:
        adapter = resolve_readonly_adapter(provider="github", auth=auth)
        if adapter:
            payload = adapter.get_workflow_runs(repository=repository, limit=limit)
            if payload.get("ok"):
                candidates = {
                    "ok": True,
                    "repository": payload.get("repository") or repository,
                    "runs": payload.get("runs") or [],
                    "run_count": len(payload.get("runs") or []),
                    "query_limit": limit,
                }
                discovery_source = "readonly_adapter"
            elif not payload.get("ok"):
                token = get_provider_api_token(provider="github", auth=auth)
                auth_diag = github_discovery_auth_diagnostics(token, repository=repository)
                debug = _build_discovery_diagnostics(
                    repository=payload.get("repository") or repository,
                    runs=[],
                    rerunnable=[],
                    rejections=[],
                    selected=None,
                    query_limit=limit,
                    discovery_failure_reason="workflow_runs_fetch_failed",
                )
                merged = {**auth_diag, **debug, "discovery_source": discovery_source}
                return {
                    "ok": False,
                    "error": str(payload.get("error") or "Could not list workflow runs."),
                    "repository": payload.get("repository") or repository,
                    "workflow_resolution_debug": merged,
                    "discovery_diagnostics": merged,
                    "discovery_failure_reason": "workflow_runs_fetch_failed",
                }

    if candidates is None:
        token = get_provider_api_token(provider="github", auth=auth)
        if not token:
            auth_diag = github_discovery_auth_diagnostics(None, repository=repository)
            debug = {
                "workflow_candidates_found": 0,
                "rerunnable_candidates_found": 0,
                "discovery_failure_reason": "provider_auth_failure",
                **auth_diag,
                "discovery_source": "unresolved",
            }
            return {
                "ok": False,
                "discovery_failure_reason": "provider_auth_failure",
                "workflow_resolution_debug": debug,
                "discovery_diagnostics": debug,
            }
        candidates = resolve_workflow_run_candidates(token, repository=repository, limit=limit)
        discovery_source = "workflow_resolution_fallback"

    if not candidates.get("ok"):
        debug = _build_discovery_diagnostics(
            repository=candidates.get("repository"),
            runs=[],
            rerunnable=[],
            rejections=[],
            selected=None,
            query_limit=limit,
            discovery_failure_reason=str(candidates.get("discovery_failure_reason") or "workflow_runs_fetch_failed"),
        )
        debug["discovery_source"] = discovery_source
        return {
            **candidates,
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
        }

    runs = candidates.get("runs") or []
    if not runs:
        debug = _build_discovery_diagnostics(
            repository=candidates.get("repository"),
            runs=[],
            rerunnable=[],
            rejections=[],
            selected=None,
            query_limit=limit,
            discovery_failure_reason="no_workflow_runs",
        )
        debug["discovery_source"] = discovery_source
        token = get_provider_api_token(provider="github", auth=auth)
        auth_diag = github_discovery_auth_diagnostics(token, repository=str(candidates.get("repository") or repository))
        merged = {**auth_diag, **debug}
        workflow_discovery = _maybe_diagnose_workflow_absence(
            token,
            repository=str(candidates.get("repository") or repository),
        )
        if workflow_discovery:
            merged["workflow_discovery"] = workflow_discovery
        return {
            "ok": False,
            "error": f"No workflow runs found for `{candidates.get('repository')}`.",
            "repository": candidates.get("repository"),
            "runs": [],
            "workflow_resolution_debug": merged,
            "discovery_diagnostics": merged,
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_discovery": workflow_discovery,
        }

    selected, rejections = _select_rerunnable_candidate(runs)
    rerunnable = [r for r in runs if isinstance(r, dict) and _is_rerunnable_run(r)[0]]
    failure_reason = None if selected else "no_rerunnable_candidate"
    debug = _build_discovery_diagnostics(
        repository=candidates.get("repository"),
        runs=runs,
        rerunnable=rerunnable,
        rejections=rejections,
        selected=selected,
        query_limit=limit,
        discovery_failure_reason=failure_reason,
    )
    debug["discovery_source"] = discovery_source
    if readonly_artifact and readonly_artifact.get("source_job_id"):
        debug["readonly_source_job_id"] = readonly_artifact.get("source_job_id")

    if not selected:
        return {
            "ok": False,
            "error": "No rerunnable workflow run found — all candidates are actively running or inaccessible.",
            "repository": candidates.get("repository"),
            "runs": runs,
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
            "discovery_failure_reason": "no_rerunnable_candidate",
        }

    result = _run_resolution_artifact(
        candidates.get("repository"),
        selected,
        candidates=runs,
        workflow_resolution_debug=debug,
    )
    result["discovery_source"] = discovery_source
    return result


def resolve_workflow_by_name(
    token: str,
    *,
    repository: str,
    workflow_name: str,
    limit: int = _DEFAULT_QUERY_LIMIT,
) -> dict[str, Any]:
    candidates = resolve_workflow_run_candidates(token, repository=repository, limit=limit)
    if not candidates.get("ok"):
        return candidates
    name_lower = workflow_name.lower()
    matched = [
        r
        for r in candidates.get("runs") or []
        if name_lower in str(r.get("name") or "").lower()
    ]
    if not matched:
        debug = _build_discovery_diagnostics(
            repository=candidates.get("repository"),
            runs=matched,
            rerunnable=[],
            rejections=[],
            selected=None,
            query_limit=limit,
            discovery_failure_reason="workflow_name_not_found",
        )
        return {
            "ok": False,
            "error": f"No workflow runs matching `{workflow_name}`.",
            "repository": candidates.get("repository"),
            "runs": [],
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
        }
    selected, rejections = _select_rerunnable_candidate(matched)
    rerunnable = [r for r in matched if _is_rerunnable_run(r)[0]]
    debug = _build_discovery_diagnostics(
        repository=candidates.get("repository"),
        runs=matched,
        rerunnable=rerunnable,
        rejections=rejections,
        selected=selected,
        query_limit=limit,
        discovery_failure_reason=None if selected else "no_rerunnable_candidate",
    )
    if not selected:
        return {
            "ok": False,
            "error": f"No rerunnable workflow run for `{workflow_name}`.",
            "repository": candidates.get("repository"),
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
            "discovery_failure_reason": "no_rerunnable_candidate",
        }
    return _run_resolution_artifact(
        candidates.get("repository"),
        selected,
        candidates=matched,
        workflow_resolution_debug=debug,
    )


def resolve_latest_workflow_run(
    token: str,
    *,
    repository: str,
    limit: int = _DEFAULT_QUERY_LIMIT,
    workflow_name: str | None = None,
) -> dict[str, Any]:
    if workflow_name:
        return resolve_workflow_by_name(
            token, repository=repository, workflow_name=workflow_name, limit=limit
        )

    candidates = resolve_workflow_run_candidates(token, repository=repository, limit=limit)
    if not candidates.get("ok"):
        debug = _build_discovery_diagnostics(
            repository=candidates.get("repository"),
            runs=[],
            rerunnable=[],
            rejections=[],
            selected=None,
            query_limit=limit,
            discovery_failure_reason=str(candidates.get("discovery_failure_reason") or "workflow_runs_fetch_failed"),
        )
        return {
            **candidates,
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
        }

    runs = candidates.get("runs") or []
    if not runs:
        debug = _build_discovery_diagnostics(
            repository=candidates.get("repository"),
            runs=[],
            rerunnable=[],
            rejections=[],
            selected=None,
            query_limit=limit,
            discovery_failure_reason="no_workflow_runs",
        )
        return {
            "ok": False,
            "error": f"No workflow runs found for `{candidates.get('repository')}`.",
            "repository": candidates.get("repository"),
            "runs": [],
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
            "discovery_failure_reason": "no_workflow_runs",
        }

    selected, rejections = _select_rerunnable_candidate(runs)
    rerunnable = [r for r in runs if isinstance(r, dict) and _is_rerunnable_run(r)[0]]
    failure_reason = None if selected else "no_rerunnable_candidate"
    debug = _build_discovery_diagnostics(
        repository=candidates.get("repository"),
        runs=runs,
        rerunnable=rerunnable,
        rejections=rejections,
        selected=selected,
        query_limit=limit,
        discovery_failure_reason=failure_reason,
    )

    if not selected:
        return {
            "ok": False,
            "error": "No rerunnable workflow run found — all candidates are actively running or inaccessible.",
            "repository": candidates.get("repository"),
            "runs": runs,
            "workflow_resolution_debug": debug,
            "discovery_diagnostics": debug,
            "discovery_failure_reason": "no_rerunnable_candidate",
        }

    return _run_resolution_artifact(
        candidates.get("repository"),
        selected,
        candidates=runs,
        workflow_resolution_debug=debug,
    )


def _run_resolution_artifact(
    repository: str | None,
    run: dict[str, Any],
    *,
    candidates: list[dict[str, Any]] | None = None,
    workflow_resolution_debug: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rerunnable = [r for r in (candidates or [run]) if isinstance(r, dict) and _is_rerunnable_run(r)[0]]
    debug = workflow_resolution_debug or _build_discovery_diagnostics(
        repository=repository,
        runs=candidates or [run],
        rerunnable=rerunnable,
        rejections=[],
        selected=run,
        query_limit=_DEFAULT_QUERY_LIMIT,
        discovery_failure_reason=None,
    )
    return {
        "ok": True,
        "repository": repository,
        "workflow_id": run.get("workflow_id"),
        "workflow_name": run.get("name"),
        "source_run_id": run.get("id"),
        "selected_run_id": run.get("id"),
        "source_run_number": run.get("run_number"),
        "source_created_at": run.get("created_at"),
        "source_status": run.get("status"),
        "source_conclusion": run.get("conclusion"),
        "head_branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
        "run": run,
        "candidates": candidates or [run],
        "candidate_count": len(candidates or [run]),
        "workflow_candidates_found": debug.get("workflow_candidates_found"),
        "rerunnable_candidates_found": debug.get("rerunnable_candidates_found"),
        "workflow_resolution_debug": debug,
        "discovery_diagnostics": debug,
    }


def _maybe_diagnose_workflow_absence(token: str | None, *, repository: str) -> dict[str, Any] | None:
    if not token or not repository:
        return None
    try:
        from aethos_core.providers.github.workflow_discovery.workflow_run_absence_diagnosis import (
            diagnose_workflow_run_absence,
        )

        diagnosis = diagnose_workflow_run_absence(token, repository=repository)
        return diagnosis if diagnosis.get("ok") is not False or diagnosis.get("likely_reason") else None
    except Exception:
        return None


def resolution_to_mutation_params(resolution: dict[str, Any]) -> dict[str, Any]:
    """Extract mutation execution params from a preflight resolution artifact."""
    if not resolution.get("ok"):
        return {}
    return {
        "workflow_resolution": resolution,
        "workflow_id": resolution.get("workflow_id"),
        "workflow_name": resolution.get("workflow_name"),
        "source_run_id": resolution.get("source_run_id"),
        "source_run_number": resolution.get("source_run_number"),
        "source_created_at": resolution.get("source_created_at"),
    }
