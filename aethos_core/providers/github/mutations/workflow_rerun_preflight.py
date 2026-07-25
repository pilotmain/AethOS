# SPDX-License-Identifier: Apache-2.0
"""Governed GitHub workflow rerun preflight."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.mutations.risk import MutationRiskTier
from aethos_core.providers.github.context.github_context_store import (
    assert_valid_repo_context,
    compose_no_failed_workflow_guidance,
    get_active_github_context,
    resolve_rerun_repository,
    save_github_rerun_context,
)
from aethos_core.providers.github.shared.workflow_resolution import discover_workflow_rerun_from_readonly_substrate

_DEPLOY_WORDS = ("deploy", "release", "production", "vercel", "railway", "publish")


def detect_deploy_workflow_risk(*, workflow_name: str = "") -> dict[str, Any]:
    name = (workflow_name or "").lower()
    deploy = any(word in name for word in _DEPLOY_WORDS)
    return {
        "deploy_workflow": deploy,
        "risk_tier": MutationRiskTier.T3_PRODUCTION.value if deploy else MutationRiskTier.T2_LOW_RISK.value,
        "summary": "Workflow may trigger deploy steps — treat as T3 production-adjacent risk."
        if deploy
        else "Checks/tests only — T2 low blast-radius rerun.",
    }


def assess_correlation_gate(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state

    state = build_correlation_state(session_id=session_id)
    corr = dict(state.get("cross_provider_correlation") or {})
    boundary = str(corr.get("failure_boundary") or "unknown")
    gh = dict((state.get("graph") or {}).get("github") or {})
    gh_failed = str(gh.get("status") or "") == "failed"
    if boundary == "github" or gh_failed:
        return {"allowed": True, "boundary": boundary, "advisory": None}
    if boundary in {"vercel", "railway"}:
        return {
            "allowed": False,
            "boundary": boundary,
            "advisory": (
                f"Cross-provider correlation boundary is **{boundary}**, not GitHub. "
                "A workflow rerun is unlikely to fix the active failure — inspect downstream deploy/runtime evidence first."
            ),
        }
    return {
        "allowed": True,
        "boundary": boundary,
        "advisory": "GitHub failure boundary is not confirmed in correlation store — verify readonly diagnostics before approving rerun.",
    }


def _resolution_from_github_context(*, session_id: str) -> dict[str, Any] | None:
    active = get_active_github_context(session_id)
    if not active:
        return None
    failed = dict(active.get("latest_failed_run") or {})
    if not failed:
        for run in list(active.get("failed_workflow_runs") or []):
            if isinstance(run, dict):
                failed = run
                break
    if not failed:
        return None
    repo = str(active.get("repo_full_name") or "")
    valid, _ = assert_valid_repo_context(repo)
    if not valid:
        return None
    return {
        "ok": True,
        "repository": repo,
        "workflow_id": failed.get("workflow_id"),
        "workflow_name": failed.get("name"),
        "source_run_id": failed.get("id"),
        "selected_run_id": failed.get("id"),
        "source_run_number": failed.get("run_number"),
        "source_created_at": failed.get("created_at"),
        "source_status": failed.get("status"),
        "source_conclusion": failed.get("conclusion"),
        "head_branch": failed.get("head_branch") or active.get("active_branch"),
        "head_sha": failed.get("head_sha") or active.get("head_sha"),
        "run": failed,
        "discovery_source": "github_context",
    }


def _resolution_from_correlation_store(*, session_id: str, repository: str) -> dict[str, Any] | None:
    from aethos_core.cross_provider_correlation.correlation_store import get_session_snapshot

    snapshot = get_session_snapshot(session_id)
    gh = dict(snapshot.get("github") or {})
    if not gh:
        return None
    repo = str(gh.get("repo") or "")
    valid, _ = assert_valid_repo_context(repo)
    if not valid:
        return None
    if repository and repo.lower() != repository.lower() and repository.lower() not in repo.lower():
        return None
    metadata = dict(gh.get("metadata") or {})
    diagnostic = dict(metadata.get("workflow_diagnostic") or {})
    failed = dict(diagnostic.get("latest_failed_run") or {})
    if not failed and str(gh.get("status") or "") != "failed":
        return None
    if not failed:
        raw = dict((snapshot.get("raw") or {}).get("github") or {})
        runs = list((raw.get("workflow_runs") or {}).get("runs") or [])
        for run in runs:
            if str(run.get("conclusion") or "").lower() == "failure":
                failed = run
                break
    if not failed:
        return None
    return {
        "ok": True,
        "repository": repo or repository,
        "workflow_id": failed.get("workflow_id"),
        "workflow_name": failed.get("name"),
        "source_run_id": failed.get("id"),
        "selected_run_id": failed.get("id"),
        "source_run_number": failed.get("run_number"),
        "source_created_at": failed.get("created_at"),
        "source_status": failed.get("status"),
        "source_conclusion": failed.get("conclusion"),
        "head_branch": failed.get("head_branch"),
        "head_sha": failed.get("head_sha"),
        "run": failed,
        "discovery_source": "correlation_store",
    }


def discover_workflow_rerun_target(
    *,
    session_id: str = "default",
    repository: str = "",
    user_request: str = "",
    target_hints: list[str] | None = None,
) -> dict[str, Any]:
    from aethos_core.operations.orchestration.provider_runtime import resolve_execution_auth
    from aethos_core.providers.github.shared.readonly_workflow_artifact import find_recent_readonly_workflow_runs_artifact

    gate = assess_correlation_gate(session_id=session_id)
    repo_resolution = resolve_rerun_repository(
        session_id=session_id,
        user_request=user_request,
        target_hints=target_hints,
        repository=repository,
    )
    if repo_resolution.get("source") == "invalid":
        return {
            "ok": False,
            "preflight_blocked": True,
            "blocked_reason": "invalid_repo_context",
            "error": str(repo_resolution.get("error") or "Invalid GitHub repository context."),
            "discovery_failure_reason": "invalid_repo_context",
            "correlation_gate": gate,
        }
    if repo_resolution.get("source") == "missing":
        return {
            "ok": False,
            "needs_repo": True,
            "error": str(repo_resolution.get("error") or "No GitHub repository context available."),
            "discovery_failure_reason": "missing_repo_context",
            "correlation_gate": gate,
        }

    repo = str(repo_resolution.get("repo") or "")

    for resolver in (
        lambda: _resolution_from_github_context(session_id=session_id),
        lambda: _resolution_from_correlation_store(session_id=session_id, repository=repo),
    ):
        resolution = resolver()
        if resolution and resolution.get("ok"):
            resolution["correlation_gate"] = gate
            resolution["repo_resolution_source"] = repo_resolution.get("source")
            return resolution

    auth = resolve_execution_auth(provider="github", operation_type="workflow_runs", params={})
    readonly_artifact = find_recent_readonly_workflow_runs_artifact(
        repository=repo,
        target_hints=target_hints,
    )
    result = discover_workflow_rerun_from_readonly_substrate(
        repository=repo,
        auth=auth,
        limit=20,
        readonly_artifact=readonly_artifact,
    )
    result["correlation_gate"] = gate
    result["repo_resolution_source"] = repo_resolution.get("source")
    if not result.get("ok"):
        active = get_active_github_context(session_id)
        if active and str(active.get("repo_full_name") or "") == repo:
            return {
                **result,
                "ok": False,
                "no_failed_workflow": True,
                "repository": repo,
                "preflight_sections": compose_no_failed_workflow_guidance(repository=repo),
                "discovery_failure_reason": "no_failed_workflow",
            }
    return result


def compose_governed_rerun_preflight_sections(
    *,
    resolution: dict[str, Any],
    correlation_gate: dict[str, Any] | None = None,
    deploy_risk: dict[str, Any] | None = None,
) -> list[str]:
    gate = correlation_gate or dict(resolution.get("correlation_gate") or {})
    risk = deploy_risk or detect_deploy_workflow_risk(workflow_name=str(resolution.get("workflow_name") or ""))
    commit = str(resolution.get("head_sha") or "")[:12] or "—"
    lines = [
        "Created governed GitHub workflow rerun preflight.",
        "",
        "Target:",
        f"- Repo: **{resolution.get('repository') or '—'}**",
        f"- Workflow: **{resolution.get('workflow_name') or resolution.get('workflow_id') or '—'}**",
        f"- Run ID: `{resolution.get('source_run_id') or '—'}`",
        f"- Branch: `{resolution.get('head_branch') or '—'}`",
        f"- Commit: `{commit}`",
        "",
        "Risk:",
        "- Low risk readonly-adjacent mutation",
        "- Does not modify code",
        "- May consume CI minutes",
    ]
    if risk.get("deploy_workflow"):
        lines.append("- **May trigger deployment** if workflow includes deploy steps (T3)")
    else:
        lines.append("- Unlikely to deploy production unless workflow includes deploy steps (T2)")
    if gate.get("advisory"):
        lines.extend(["", "Correlation advisory:", f"- {gate['advisory']}"])
    lines.extend(
        [
            "",
            "Verification:",
            "- Poll workflow status after approval",
            "- Inspect failed jobs/logs if rerun fails",
            "- Correlate downstream Vercel/Railway deployment if triggered",
            "",
            "No rerun has been performed yet — approval required.",
        ]
    )
    return lines


def prepare_workflow_rerun_preflight(
    *,
    session_id: str = "default",
    target_name: str = "",
    user_request: str = "",
    target_hints: list[str] | None = None,
) -> dict[str, Any]:
    discovery = discover_workflow_rerun_target(
        session_id=session_id,
        repository=target_name,
        user_request=user_request,
        target_hints=target_hints,
    )
    gate = dict(discovery.get("correlation_gate") or assess_correlation_gate(session_id=session_id))
    if not gate.get("allowed"):
        return {
            **discovery,
            "ok": False,
            "preflight_blocked": True,
            "blocked_reason": "correlation_boundary",
            "error": gate.get("advisory"),
            "discovery_failure_reason": "correlation_boundary",
            "correlation_gate": gate,
        }
    if discovery.get("no_failed_workflow"):
        return discovery
    if discovery.get("ok"):
        deploy_risk = detect_deploy_workflow_risk(workflow_name=str(discovery.get("workflow_name") or ""))
        discovery["deploy_risk"] = deploy_risk
        discovery["preflight_sections"] = compose_governed_rerun_preflight_sections(
            resolution=discovery,
            correlation_gate=gate,
            deploy_risk=deploy_risk,
        )
        save_github_rerun_context(
            session_id,
            {
                "rerun_target_repo": discovery.get("repository"),
                "original_run_id": discovery.get("source_run_id"),
                "workflow_name": discovery.get("workflow_name"),
                "branch": discovery.get("head_branch"),
                "commit_sha": discovery.get("head_sha"),
                "verification_status": "preflight_ready",
            },
        )
    return discovery


def enrich_workflow_rerun_preflight(
    *,
    session_id: str,
    discovery: dict[str, Any],
    target_name: str,
    user_request: str = "",
    target_hints: list[str] | None = None,
) -> dict[str, Any]:
    return prepare_workflow_rerun_preflight(
        session_id=session_id,
        target_name=target_name,
        user_request=user_request,
        target_hints=target_hints,
    )
