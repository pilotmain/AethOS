# SPDX-License-Identifier: Apache-2.0
"""GitHub Actions failed workflow job evidence — readonly API metadata."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.execution.execution_evidence import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_INSUFFICIENT,
)
from aethos_core.providers.github.api_client import parse_owner_repo
from aethos_core.providers.github.operations.workflow_diagnostics_api import fetch_run_jobs
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs


def _download_job_log_excerpt(token: str, *, owner: str, repo: str, job_id: Any, limit: int = 4000) -> str:
    import httpx

    from aethos_core.providers.github.api_client import _auth_headers

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
    headers = _auth_headers(token)
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
        if response.status_code >= 400:
            return ""
        return (response.text or "")[:limit]
    except httpx.HTTPError:
        return ""


def _failed_step_name(job: dict[str, Any]) -> str | None:
    for step in job.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if str(step.get("conclusion") or "").lower() == "failure":
            return str(step.get("name") or "") or None
    return None


def fetch_workflow_jobs(token: str, *, repository: str, run_limit: int = 30) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Repository `{repository}` is not a valid owner/repo target.",
            "repository": repository,
            "confidence": CONFIDENCE_INSUFFICIENT,
        }

    runs_payload = fetch_workflow_runs(token, repository=f"{owner}/{repo}", limit=run_limit)
    if not runs_payload.get("ok"):
        error = str(runs_payload.get("error") or "GitHub Actions API request failed.")
        auth_hint = "403" in error or "401" in error or "Bad credentials" in error or "Resource not accessible" in error
        return {
            "ok": False,
            "source": "provider_api",
            "error": error,
            "repository": f"{owner}/{repo}",
            "confidence": CONFIDENCE_INSUFFICIENT,
            "auth_error": auth_hint,
        }

    runs = runs_payload.get("runs") if isinstance(runs_payload.get("runs"), list) else []
    failed_runs = [r for r in runs if str(r.get("conclusion") or "").lower() == "failure"]
    if not failed_runs:
        return {
            "ok": True,
            "source": "provider_api",
            "repository": f"{owner}/{repo}",
            "confidence": CONFIDENCE_CONFIRMED,
            "no_failed_jobs": True,
            "latest_failed_run": None,
            "failed_jobs": [],
            "log_download_implemented": False,
        }

    latest = failed_runs[0]
    jobs_payload = fetch_run_jobs(token, owner=owner, repo=repo, run_id=latest.get("id") or "")
    if not jobs_payload.get("ok"):
        return {
            "ok": False,
            "source": "provider_api",
            "error": str(jobs_payload.get("error") or "GitHub Actions jobs request failed."),
            "repository": f"{owner}/{repo}",
            "confidence": CONFIDENCE_INSUFFICIENT,
        }

    all_jobs = jobs_payload.get("jobs") if isinstance(jobs_payload.get("jobs"), list) else []
    failed_jobs = [j for j in all_jobs if str(j.get("conclusion") or "").lower() == "failure"]
    enriched: list[dict[str, Any]] = []
    log_excerpt = ""
    for job in failed_jobs:
        if not isinstance(job, dict):
            continue
        row = {
            **job,
            "failed_step": _failed_step_name(job),
            "logs_available_metadata": bool(job.get("html_url")),
        }
        if not log_excerpt and job.get("id"):
            log_excerpt = _download_job_log_excerpt(token, owner=owner, repo=repo, job_id=job.get("id"))
            if log_excerpt:
                row["log_excerpt"] = log_excerpt[:1200]
        enriched.append(row)

    return {
        "ok": True,
        "source": "provider_api",
        "repository": f"{owner}/{repo}",
        "confidence": CONFIDENCE_CONFIRMED if enriched else CONFIDENCE_CONFIRMED,
        "no_failed_jobs": len(enriched) == 0,
        "latest_failed_run": latest,
        "failed_jobs": enriched,
        "log_download_implemented": bool(log_excerpt),
        "log_excerpt": log_excerpt[:2000] if log_excerpt else "",
    }


def format_workflow_jobs_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        error = str(payload.get("error") or "Workflow job evidence fetch failed.")
        lines = [
            "GitHub workflow job evidence could not access Actions data.",
            "",
            f"Reason: {error}",
            "",
            "Possible causes:",
            "- token missing `actions:read` permission",
            "- repository access not granted",
            "- GitHub API returned authorization error",
        ]
        return "\n".join(lines)

    repo = str(payload.get("repository") or "—")
    lines = [f"Failed workflow jobs for {repo}", ""]

    if payload.get("no_failed_jobs") and not payload.get("failed_jobs"):
        lines.extend(
            [
                f"No failed workflow jobs were found in recent GitHub Actions history for {repo}.",
                "",
                "Evidence:",
                "- source: github_api",
                "- confidence: confirmed",
                "",
                "Raw workflow log download is not implemented in this phase.",
            ]
        )
        return "\n".join(lines)

    run = payload.get("latest_failed_run") if isinstance(payload.get("latest_failed_run"), dict) else {}
    lines.extend(
        [
            "Latest failed run:",
            f"- Workflow: {run.get('name') or '—'}",
            f"- Run: #{run.get('run_number') or '—'}",
            f"- Branch: {run.get('head_branch') or '—'}",
            f"- Commit: {str(run.get('head_sha') or '—')[:12]}",
            f"- Event: {run.get('event') or '—'}",
            "",
            "Failed jobs:",
        ]
    )
    failed_jobs = payload.get("failed_jobs") if isinstance(payload.get("failed_jobs"), list) else []
    if not failed_jobs:
        lines.append("- (failed run found, but no failed jobs returned by GitHub API)")
    else:
        for job in failed_jobs:
            if not isinstance(job, dict):
                continue
            name = str(job.get("name") or "job")
            conclusion = str(job.get("conclusion") or "failure")
            lines.append(f"- {name} — {conclusion}")
            failed_step = job.get("failed_step")
            if failed_step:
                lines.append(f"  - failed step: {failed_step}")
            elif job.get("steps"):
                lines.append("  - failed step: (step metadata unavailable)")

    lines.extend(
        [
            "",
            "Evidence:",
            "- source: github_api",
            f"- confidence: {payload.get('confidence') or 'confirmed'}",
            "",
        ]
    )
    if payload.get("log_download_implemented"):
        lines.append("Raw workflow logs were downloaded and parsed.")
    else:
        lines.append("Raw workflow log download is not implemented in this phase.")
        if any(isinstance(j, dict) and j.get("logs_available_metadata") for j in failed_jobs):
            lines.append(
                "GitHub reported job metadata is available, but log download/parsing is not implemented in this phase."
            )
    return "\n".join(lines)
