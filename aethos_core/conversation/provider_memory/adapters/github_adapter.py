# SPDX-License-Identifier: Apache-2.0
"""GitHub evidence adapter — workflow rerun and CI follow-ups."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.provider_memory.provider_evidence_adapter import (
    OperationStatus,
    OperationVerification,
    ProviderEvidenceAdapter,
    ProviderLogEntry,
)


class GitHubEvidenceAdapter(ProviderEvidenceAdapter):
    provider = "github"

    def get_operation_status(self, thread: Any, job: Any | None) -> OperationStatus:
        repo = _repository(thread, job)
        run = _latest_run(repo, job)
        status_label = str(run.get("conclusion") or run.get("status") or getattr(thread, "status", "unknown"))
        verified = status_label.lower() in {"success", "completed"}
        return OperationStatus(
            execution_job_id=str(getattr(job, "id", "") or getattr(thread, "execution_job_id", "") or "unknown"),
            provider_command=_command_state(job),
            restart_evidence="detected" if verified else "not detected",
            latest_log_timestamp=run.get("updated_at"),
            service_health="online" if verified else "unknown",
            status_label=status_label,
            verification_label="verified" if verified else "waiting for workflow conclusion",
        )

    def get_latest_logs(
        self,
        thread: Any,
        job: Any | None,
        *,
        limit: int = 5,
        level_filter: str | None = None,
    ) -> list[ProviderLogEntry]:
        _ = level_filter
        repo = _repository(thread, job)
        run = _latest_run(repo, job)
        run_id = str(run.get("id") or "")
        if not repo or not run_id:
            return []
        token = _resolve_token()
        if not token:
            return []
        from aethos_core.providers.github.operations.workflow_jobs_api import fetch_workflow_jobs

        payload = fetch_workflow_jobs(token, repository=repo, run_limit=1)
        jobs = list(payload.get("jobs") or [])
        rows: list[ProviderLogEntry] = []
        for row in jobs[:limit]:
            if not isinstance(row, dict):
                continue
            rows.append(
                ProviderLogEntry(
                    timestamp=str(row.get("completed_at") or row.get("started_at") or "") or None,
                    level=str(row.get("conclusion") or row.get("status") or "INFO"),
                    message=str(row.get("name") or row.get("title") or "")[:240],
                )
            )
        return rows

    def verify_operation(self, thread: Any, job: Any | None) -> OperationVerification:
        repo = _repository(thread, job)
        run = _latest_run(repo, job)
        conclusion = str(run.get("conclusion") or "").lower()
        status = str(run.get("status") or "").lower()
        verified = conclusion == "success" or (status == "completed" and conclusion in {"", "success"})
        outcome = "workflow_verified" if verified else "still_stabilizing" if status in {"in_progress", "queued", "pending"} else "inconclusive"
        return OperationVerification(
            conclusion=outcome,
            verified=verified,
            latest_log_timestamp=run.get("updated_at"),
            timestamps_available=bool(run.get("updated_at")),
            logs_unavailable=not run.get("ok"),
            service_health="online" if verified else "unknown",
            provider_command=_command_state(job),
            evidence=run,
        )

    def explain_failure(self, thread: Any, job: Any | None) -> str:
        repo = _repository(thread, job)
        run = _latest_run(repo, job)
        path = thread.service_path() if hasattr(thread, "service_path") else repo
        if run.get("conclusion") in {"failure", "cancelled", "timed_out"}:
            return (
                f"The latest GitHub **{getattr(thread, 'operation', 'workflow_rerun') or 'workflow'}** for **{path}** did not succeed.\n\n"
                f"Conclusion: **{run.get('conclusion')}**\n\n"
                f"Workflow: `{run.get('name') or 'unknown'}` · run `{run.get('id') or 'unknown'}`"
            )
        if job is not None:
            params = getattr(job, "params", None) or {}
            failure = params.get("failure_truth") or params.get("lifecycle_summary")
            if failure:
                return str(failure)
        return (
            f"I checked the active GitHub thread for **{path}**, but no structured failure reason is stored yet.\n\n"
            f"Current status: **{getattr(thread, 'status', 'unknown')}**."
        )


def _repository(thread: Any, job: Any | None) -> str:
    if job is not None:
        params = getattr(job, "params", None) or {}
        target = dict(params.get("target") or {})
        repo = str(params.get("target_name") or target.get("repository") or target.get("repo") or "")
        if repo:
            return repo
    evidence = dict(getattr(thread, "last_evidence", None) or {})
    return str(evidence.get("repository") or getattr(thread, "service", None) or "")


def _command_state(job: Any | None) -> str:
    if job is None:
        return "unknown"
    params = getattr(job, "params", None) or {}
    if params.get("executed") is True:
        return "submitted"
    if params.get("execution_state") == "execution_failed":
        return "failed"
    return str(params.get("execution_state") or "unknown")


def _resolve_token() -> str | None:
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token("github")
        return str(token).strip() if token else None
    except Exception:
        return None


def _latest_run(repository: str, job: Any | None) -> dict[str, Any]:
    repository = (repository or "").strip()
    if not repository:
        return {"ok": False}
    token = _resolve_token()
    if not token:
        return {"ok": False}
    from aethos_core.providers.github.operations.workflow_runs_api import fetch_workflow_runs

    payload = fetch_workflow_runs(token, repository=repository, limit=5)
    if not payload.get("ok"):
        return {"ok": False, "detail": payload.get("error")}
    runs = list(payload.get("runs") or [])
    if job is not None:
        params = getattr(job, "params", None) or {}
        run_id = str(params.get("workflow_run_id") or params.get("provider_run_id") or "")
        if run_id:
            match = next((row for row in runs if str(row.get("id") or "") == run_id), None)
            if match:
                return {"ok": True, **match}
    if runs:
        row = runs[0]
        return {"ok": True, **row}
    return {"ok": False}
