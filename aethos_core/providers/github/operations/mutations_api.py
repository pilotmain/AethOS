# SPDX-License-Identifier: Apache-2.0
"""GitHub governed mutations — workflow rerun (T2)."""

from __future__ import annotations

from typing import Any

from aethos_core.operations.mutations.failures import classify_github_rerun_failure
from aethos_core.providers.github.api_client import parse_owner_repo, request_github
from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs
from aethos_core.providers.github.shared.workflow_resolution import (
    resolve_latest_workflow_run,
    resolve_repository,
)


def _github_evidence(
    *,
    workflow_id: Any,
    workflow_name: Any,
    source_run_id: Any,
    http_status: Any,
    rerun_attempted: bool,
    new_run_id: Any = None,
    new_run_detected: bool = False,
    failure_reason: str | None = None,
    failure_classification: str | None = None,
    rerun_endpoint: str | None = None,
    source_created_at: Any = None,
    source_run_number: int | None = None,
    verification_attempts: int = 0,
    repository: str | None = None,
) -> dict[str, Any]:
    return {
        "provider": "github",
        "operation": "workflow_rerun",
        "repository": repository,
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "source_run_id": source_run_id,
        "source_created_at": source_created_at,
        "source_run_number": source_run_number,
        "http_status": http_status,
        "rerun_attempted": rerun_attempted,
        "rerun_endpoint": rerun_endpoint,
        "new_run_id": new_run_id,
        "new_run_detected": new_run_detected,
        "verification_result": "pending" if rerun_attempted else None,
        "verification_attempts": verification_attempts,
        "failure_reason": failure_reason,
        "failure_classification": failure_classification,
    }


def _attempt_rerun(token: str, *, owner: str, repo: str, run_id: int | str) -> dict[str, Any]:
    endpoints = [
        f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun",
        f"/repos/{owner}/{repo}/actions/runs/{run_id}/rerun-failed-jobs",
    ]
    last: dict[str, Any] = {"ok": False, "error": "No rerun endpoint attempted."}
    for path in endpoints:
        result = request_github(token, "POST", path)
        http_status = result.get("http_status")
        if result.get("ok") or http_status in (201, 204):
            return {**result, "ok": True, "http_status": http_status or 201, "rerun_endpoint": path}
        last = {**result, "http_status": http_status, "rerun_endpoint": path}
        err = str(result.get("error") or "").lower()
        if http_status not in (403, 422) and "already" not in err:
            break
    return last


def rerun_latest_workflow(
    token: str,
    *,
    repository: str,
    workflow_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolution = workflow_resolution if isinstance(workflow_resolution, dict) and workflow_resolution.get("ok") else None
    if resolution and resolution.get("repository"):
        full_name = str(resolution["repository"])
        owner, repo = parse_owner_repo(full_name)
        if not owner or not repo:
            repo_result = resolve_repository(token, repository=full_name)
            if not repo_result.get("ok"):
                full_name = str(repository)
                repo_result = resolve_repository(token, repository=full_name)
            else:
                full_name = str(repo_result["full_name"])
                owner, repo = str(repo_result["owner"]), str(repo_result["repo"])
    else:
        repo_result = resolve_repository(token, repository=repository)
        if not repo_result.get("ok"):
            fc = "target_unresolved"
            err = str(repo_result.get("error") or f"Repository `{repository}` could not be resolved.")
            return {
                "ok": False,
                "detail": err,
                "failure_type": fc,
                "failure_classification": fc,
                "evidence": _github_evidence(
                    workflow_id=None,
                    workflow_name=None,
                    source_run_id=None,
                    http_status=None,
                    rerun_attempted=False,
                    failure_reason=err,
                    failure_classification=fc,
                    repository=repository,
                ),
            }
        full_name = str(repo_result["full_name"])
        owner = str(repo_result["owner"])
        repo = str(repo_result["repo"])

    if not resolution:
        resolution = resolve_latest_workflow_run(token, repository=full_name, limit=20)

    if not resolution.get("ok"):
        err = str(resolution.get("error") or f"No workflow runs found for `{full_name}`.")
        fc = "workflow_not_found"
        return {
            "ok": False,
            "detail": err,
            "failure_type": fc,
            "failure_classification": fc,
            "repository": full_name,
            "evidence": _github_evidence(
                workflow_id=resolution.get("workflow_id"),
                workflow_name=resolution.get("workflow_name"),
                source_run_id=resolution.get("source_run_id"),
                http_status=None,
                rerun_attempted=False,
                failure_reason=err,
                failure_classification=fc,
                repository=full_name,
            ),
        }

    run = resolution.get("run") or {}
    run_id = resolution.get("source_run_id") or run.get("id")
    workflow_id = resolution.get("workflow_id") or run.get("workflow_id") or run.get("name")
    workflow_name = resolution.get("workflow_name") or run.get("name")
    source_created_at = resolution.get("source_created_at") or run.get("created_at")
    source_run_number = resolution.get("source_run_number") or run.get("run_number")

    if not run_id:
        fc = "workflow_not_found"
        return {
            "ok": False,
            "detail": "Latest workflow run id unavailable.",
            "failure_type": fc,
            "failure_classification": fc,
            "repository": full_name,
            "evidence": _github_evidence(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                source_run_id=None,
                http_status=None,
                rerun_attempted=False,
                failure_reason="Latest workflow run id unavailable.",
                failure_classification=fc,
                repository=full_name,
            ),
        }

    result = _attempt_rerun(token, owner=owner, repo=repo, run_id=run_id)
    http_status = result.get("http_status")
    rerun_endpoint = result.get("rerun_endpoint")
    if not result.get("ok"):
        err = str(result.get("error") or "Workflow rerun failed.")
        fc = classify_github_rerun_failure(error_text=err, http_status=http_status)
        evidence = _github_evidence(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            source_run_id=run_id,
            http_status=http_status,
            rerun_attempted=False,
            failure_reason=err,
            failure_classification=fc,
            rerun_endpoint=rerun_endpoint,
            source_created_at=source_created_at,
            source_run_number=source_run_number,
            repository=full_name,
        )
        return {
            "ok": False,
            "detail": err,
            "failure_type": fc,
            "failure_classification": fc,
            "http_status": http_status,
            "rerun_attempted": False,
            "repository": full_name,
            "provider": "github",
            "operation": "workflow_rerun",
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "source_run_id": run_id,
            "workflow_resolution": resolution,
            "evidence": evidence,
        }

    after = fetch_workflow_runs(token, repository=full_name, limit=10)
    new_run_id = None
    new_run_detected = False
    rerun_status = "queued"
    if after.get("ok"):
        for candidate in after.get("runs") or []:
            cid = candidate.get("id")
            if cid and str(cid) != str(run_id):
                new_run_id = cid
                new_run_detected = True
                rerun_status = str(candidate.get("status") or "queued")
                break

    evidence = _github_evidence(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        source_run_id=run_id,
        http_status=http_status,
        rerun_attempted=True,
        new_run_id=new_run_id,
        new_run_detected=new_run_detected,
        rerun_endpoint=rerun_endpoint,
        source_created_at=source_created_at,
        source_run_number=source_run_number,
        repository=full_name,
    )
    return {
        "ok": True,
        "detail": f"Workflow rerun requested for run #{run.get('run_number') or source_run_number} on `{full_name}`.",
        "repository": full_name,
        "provider": "github",
        "operation": "workflow_rerun",
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "source_run_id": run_id,
        "source_created_at": source_created_at,
        "source_run_number": source_run_number,
        "new_run_id": new_run_id,
        "new_run_detected": new_run_detected,
        "http_status": http_status,
        "rerun_attempted": True,
        "verification_result": "pending",
        "failure_reason": None,
        "failure_classification": None,
        "rerun_status": rerun_status,
        "rerun_endpoint": rerun_endpoint,
        "workflow_resolution": resolution,
        "evidence": evidence,
    }
