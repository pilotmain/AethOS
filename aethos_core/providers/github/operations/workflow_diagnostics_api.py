# SPDX-License-Identifier: Apache-2.0
"""GitHub Actions workflow failure diagnostics — readonly API evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.execution.execution_evidence import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_INSUFFICIENT,
)
from aethos_core.providers.github.api_client import parse_owner_repo, request_github
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs


def _normalize_run(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "status": row.get("status"),
        "conclusion": row.get("conclusion"),
        "event": row.get("event"),
        "head_branch": row.get("head_branch"),
        "head_sha": row.get("head_sha"),
        "html_url": row.get("html_url"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "run_number": row.get("run_number"),
    }


def fetch_run_jobs(token: str, *, owner: str, repo: str, run_id: int | str) -> dict[str, Any]:
    result = request_github(token, "GET", f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs")
    if not result.get("ok"):
        return {
            "ok": False,
            "error": str(result.get("error") or "GitHub Actions jobs request failed."),
            "jobs": [],
        }
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    jobs: list[dict[str, Any]] = []
    for row in data.get("jobs") or []:
        if not isinstance(row, dict):
            continue
        steps: list[dict[str, Any]] = []
        for step in row.get("steps") or []:
            if not isinstance(step, dict):
                continue
            steps.append(
                {
                    "name": step.get("name"),
                    "status": step.get("status"),
                    "conclusion": step.get("conclusion"),
                    "number": step.get("number"),
                }
            )
        jobs.append(
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "status": row.get("status"),
                "conclusion": row.get("conclusion"),
                "html_url": row.get("html_url"),
                "steps": steps,
            }
        )
    return {"ok": True, "jobs": jobs, "error": None}


def _find_failed_job_step(jobs: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for job in jobs:
        if str(job.get("conclusion") or "").lower() == "failure":
            for step in job.get("steps") or []:
                if str(step.get("conclusion") or "").lower() == "failure":
                    return str(job.get("name") or ""), str(step.get("name") or "")
            return str(job.get("name") or ""), None
    return None, None


def fetch_workflow_diagnostic(token: str, *, repository: str, run_limit: int = 30) -> dict[str, Any]:
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
            "no_failed_runs": True,
            "latest_failed_run": None,
            "failed_jobs": [],
            "likely_failure_job": None,
            "likely_failure_step": None,
            "logs_implemented": False,
        }

    latest = failed_runs[0]
    jobs_payload = fetch_run_jobs(token, owner=owner, repo=repo, run_id=latest.get("id") or "")
    failed_jobs = []
    if jobs_payload.get("ok"):
        failed_jobs = [
            j for j in (jobs_payload.get("jobs") or []) if str(j.get("conclusion") or "").lower() == "failure"
        ]
    likely_job, likely_step = _find_failed_job_step(jobs_payload.get("jobs") or [])

    return {
        "ok": True,
        "source": "provider_api",
        "repository": f"{owner}/{repo}",
        "confidence": CONFIDENCE_CONFIRMED,
        "no_failed_runs": False,
        "latest_failed_run": latest,
        "failed_jobs": failed_jobs,
        "likely_failure_job": likely_job,
        "likely_failure_step": likely_step,
        "logs_implemented": False,
    }


def format_workflow_diagnostic_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        error = str(payload.get("error") or "Workflow diagnostic failed.")
        lines = [
            "GitHub workflow diagnostics could not access Actions data.",
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
    lines = [f"GitHub workflow diagnostic for {repo}", ""]

    if payload.get("no_failed_runs"):
        lines.extend(
            [
                f"No failed workflow runs were found in the recent GitHub Actions history for {repo}.",
                "",
                "Evidence:",
                "- source: github_api",
                "- confidence: confirmed",
                "",
                "Step-level log download is not implemented in this phase.",
            ]
        )
        return "\n".join(lines)

    run = payload.get("latest_failed_run") if isinstance(payload.get("latest_failed_run"), dict) else {}
    lines.extend(
        [
            "Latest failed run:",
            f"- Workflow: {run.get('name') or '—'}",
            f"- Run: #{run.get('run_number') or '—'}",
            f"- Conclusion: {run.get('conclusion') or 'failure'}",
            f"- Branch: {run.get('head_branch') or '—'}",
            f"- Commit: {str(run.get('head_sha') or '—')[:12]}",
            f"- Event: {run.get('event') or '—'}",
            "",
        ]
    )
    likely_job = payload.get("likely_failure_job")
    likely_step = payload.get("likely_failure_step")
    if likely_job or likely_step:
        lines.append("Likely failure area:")
        if likely_job:
            lines.append(f"- Job: {likely_job}")
        if likely_step:
            lines.append(f"- Failed step: {likely_step}")
        else:
            lines.append("- Failed step: (step name unavailable from API metadata)")
        lines.append("")

    lines.extend(
        [
            "Evidence:",
            "- source: github_api",
            f"- confidence: {payload.get('confidence') or 'confirmed'}",
            "",
            "Step-level log download is not implemented in this phase.",
        ]
    )
    if run.get("html_url"):
        lines.extend(["", f"Run URL: {run['html_url']}"])
    return "\n".join(lines)
