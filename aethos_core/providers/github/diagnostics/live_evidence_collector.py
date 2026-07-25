# SPDX-License-Identifier: Apache-2.0
"""Collect multi-source GitHub live readonly evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.diagnostics.repo_diagnostics_api import (
    detect_pending_local_changes_note,
    fetch_branch_divergence,
    fetch_open_pull_requests,
    fetch_releases_and_tags,
)
from aethos_core.providers.github.operations.repo_readonly_api import (
    fetch_branch_status,
    fetch_failed_checks,
    fetch_recent_commits,
    inspect_repo,
)
from aethos_core.providers.github.operations.workflow_diagnostics_api import fetch_workflow_diagnostic
from aethos_core.providers.github.operations.workflow_jobs_api import fetch_workflow_jobs
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs


def collect_github_live_evidence(
    token: str,
    *,
    repository: str,
    session_id: str = "default",
    operation: str = "live_diagnosis",
) -> dict[str, Any]:
    repo = inspect_repo(token, repository=repository)
    branch = fetch_branch_status(token, repository=repository)
    default_branch = str(repo.get("default_branch") or branch.get("branch") or "main")
    divergence = fetch_branch_divergence(token, repository=repository, base=default_branch, head=default_branch)
    commits = fetch_recent_commits(token, repository=repository, limit=8)
    checks = fetch_failed_checks(token, repository=repository)
    workflow_runs = fetch_workflow_runs(token, repository=repository, limit=10)
    workflow_diagnostic = fetch_workflow_diagnostic(token, repository=repository, run_limit=15)
    workflow_jobs = fetch_workflow_jobs(token, repository=repository, run_limit=10)
    pull_requests = fetch_open_pull_requests(token, repository=repository, limit=5)
    releases = fetch_releases_and_tags(token, repository=repository, limit=5)
    deploy_correlation = _correlate_deploy_failures(
        repository=repository,
        session_id=session_id,
        workflow_diagnostic=workflow_diagnostic,
        workflow_runs=workflow_runs,
    )
    local_changes_note = detect_pending_local_changes_note(
        ahead_by=int(divergence.get("ahead_by") or 0) if divergence.get("ok") else 0,
        behind_by=int(divergence.get("behind_by") or 0) if divergence.get("ok") else 0,
    )

    evidence = {
        "ok": repo.get("ok", False),
        "repository": str(repo.get("repository") or repository),
        "operation": operation,
        "repo": repo,
        "branch": branch,
        "divergence": divergence,
        "local_changes_note": local_changes_note,
        "commits": commits,
        "checks": checks,
        "workflow_runs": workflow_runs,
        "workflow_diagnostic": workflow_diagnostic,
        "workflow_jobs": workflow_jobs,
        "pull_requests": pull_requests,
        "releases": releases,
        "deploy_correlation": deploy_correlation,
    }

    from aethos_core.cross_provider_correlation.evidence_publisher import ingest_github_live_evidence

    cross_corr = ingest_github_live_evidence(session_id, evidence)
    evidence["deploy_correlation"] = {
        **deploy_correlation,
        "lines": cross_corr.get("lines") or deploy_correlation.get("lines") or [],
        "failure_boundary": cross_corr.get("failure_boundary"),
        "confidence": cross_corr.get("confidence"),
    }
    evidence["cross_provider_correlation"] = cross_corr

    from aethos_core.providers.github.context.github_context_store import save_github_context_from_evidence

    save_github_context_from_evidence(session_id, evidence)
    return evidence


def _correlate_deploy_failures(
    *,
    repository: str,
    session_id: str,
    workflow_diagnostic: dict[str, Any],
    workflow_runs: dict[str, Any],
) -> dict[str, Any]:
    lines: list[str] = []
    repo_key = repository.split("/")[-1].lower()

    failed_runs = [
        run
        for run in (workflow_runs.get("runs") or [])
        if isinstance(run, dict) and str(run.get("conclusion") or "").lower() == "failure"
    ]
    deploy_related = [
        run
        for run in failed_runs
        if any(word in str(run.get("name") or "").lower() for word in ("deploy", "release", "build", "ci", "vercel", "railway"))
    ]
    if deploy_related:
        latest = deploy_related[0]
        lines.append(
            f"GitHub Actions failure `{latest.get('name')}` on branch `{latest.get('head_branch')}` may block downstream deploy."
        )

    try:
        from aethos_core.failed_service_investigation.failed_service_memory import get_failed_health_rows

        for row in get_failed_health_rows(session_id=session_id):
            service = str(row.get("service") or "").lower()
            project = str(row.get("project") or "").lower()
            if repo_key in service or repo_key in project or service in repo_key:
                lines.append(
                    f"Cached provider health shows **{row.get('project')} / {row.get('service')}** still **{row.get('status') or row.get('health')}** — correlate with latest failed GitHub workflow/check."
                )
    except Exception:
        pass

    diag = dict(workflow_diagnostic.get("latest_failed_run") or {})
    if diag.get("name"):
        lines.append(f"Latest failed workflow: **{diag.get('name')}** run #{diag.get('run_number')} on `{diag.get('head_branch')}`.")
    elif not lines:
        lines.append("No cached Railway/Vercel failure correlated with this repo yet — inspect provider deploy logs if CI is green.")

    return {"lines": lines, "deploy_related_failures": len(deploy_related)}
