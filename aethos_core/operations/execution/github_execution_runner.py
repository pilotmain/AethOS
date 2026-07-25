# SPDX-License-Identifier: Apache-2.0
"""GitHub read-only execution runner."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.adapters import provider_auth_source_phrase
from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact, format_execution_report
from aethos_core.operations.execution.execution_evidence import (
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_INSUFFICIENT,
    append_evidence,
    evidence_item,
)
from aethos_core.operations.execution.execution_permissions import assert_readonly_action
from aethos_core.operations.execution.execution_progress import ACTION_PROGRESS, emit_step, progress_emitter
from aethos_core.operations.execution.execution_runner import ExecutionOutcome, _append_timeline, _new_execution_id, _run_step
from aethos_core.operations.github_operation_capabilities import resolve_execution_auth


def run_github_readonly_execution(*, params: dict[str, Any], job_id: str | None = None) -> ExecutionOutcome:
    progress = progress_emitter(job_id)
    emit_step(progress, "Preparing read-only checks")
    actions = list(params.get("approved_actions") or [])
    target = str(params.get("target_name") or "")
    operation_type = str(params.get("operation_type") or "workflow_runs")
    emit_step(progress, "Building adapter")
    auth = resolve_execution_auth(operation_type, params)
    adapter = None
    if auth["auth_method"] == "api_token" and auth["credential_id"]:
        from aethos_core.operations.orchestration.registry_runtime import resolve_readonly_execution_adapter

        adapter = resolve_readonly_execution_adapter("github", auth["credential_id"])
    artifact = ExecutionArtifact(
        execution_id=_new_execution_id(),
        provider="github",
        operation_type=operation_type,
        target_name=target or None,
        approved_actions=actions,
    )
    artifact.auth_method = auth["auth_method"]
    artifact.auth_method_label = auth["auth_method_label"]
    artifact.data_source = "provider_api" if adapter else "unknown"
    _append_timeline(
        artifact,
        "started",
        f"Read-only GitHub {operation_type.replace('_', ' ')} for `{target}` "
        f"using your {provider_auth_source_phrase('github', auth['auth_method'])}",
    )

    for action in actions:
        assert_readonly_action(action)
        emit_step(progress, ACTION_PROGRESS.get(action, action.replace("_", " ")))
        _append_timeline(artifact, "running", action)
        try:
            if action == "github_api_workflow_runs" and adapter and target:
                payload = _run_step(
                    "github_api_workflow_runs",
                    lambda: adapter.get_workflow_runs(repository=target),
                    job_id=job_id,
                )
                artifact.findings.append(
                    {
                        "action": action,
                        "source": "provider_api",
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "runs": payload.get("runs"),
                        "repository": payload.get("repository"),
                    }
                )
                if payload.get("ok"):
                    for run in payload.get("runs") or []:
                        if not isinstance(run, dict):
                            continue
                        append_evidence(
                            artifact,
                            evidence_item(
                                source="github_api",
                                type="workflow_run",
                                confidence=CONFIDENCE_CONFIRMED,
                                message=(
                                    f"Workflow `{run.get('name') or 'run'}` "
                                    f"#{run.get('run_number')} · status `{run.get('status')}` · "
                                    f"conclusion `{run.get('conclusion') or '—'}`."
                                ),
                                service_id=run.get("id"),
                                project_id=target,
                            ),
                        )
                    artifact.confidence = CONFIDENCE_CONFIRMED
            elif action == "github_api_workflow_diagnostic" and adapter and target:
                payload = _run_step(
                    "github_api_workflow_diagnostic",
                    lambda: adapter.get_workflow_diagnostic(repository=target),
                    job_id=job_id,
                )
                artifact.findings.append(
                    {
                        "action": action,
                        "source": "provider_api",
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "repository": payload.get("repository"),
                        "latest_failed_run": payload.get("latest_failed_run"),
                        "failed_jobs": payload.get("failed_jobs"),
                        "no_failed_runs": payload.get("no_failed_runs"),
                        "likely_failure_job": payload.get("likely_failure_job"),
                        "likely_failure_step": payload.get("likely_failure_step"),
                        "logs_implemented": payload.get("logs_implemented"),
                    }
                )
                if payload.get("ok"):
                    confidence = str(payload.get("confidence") or CONFIDENCE_CONFIRMED)
                    artifact.confidence = confidence
                    if payload.get("no_failed_runs"):
                        append_evidence(
                            artifact,
                            evidence_item(
                                source="github_api",
                                type="workflow_diagnostic",
                                confidence=CONFIDENCE_CONFIRMED,
                                message=f"No failed workflow runs in recent history for `{target}`.",
                                project_id=target,
                            ),
                        )
                    else:
                        run = payload.get("latest_failed_run") if isinstance(payload.get("latest_failed_run"), dict) else {}
                        append_evidence(
                            artifact,
                            evidence_item(
                                source="github_api",
                                type="workflow_diagnostic",
                                confidence=CONFIDENCE_CONFIRMED,
                                message=(
                                    f"Latest failed workflow `{run.get('name') or 'run'}` "
                                    f"#{run.get('run_number')} on branch `{run.get('head_branch') or '—'}`."
                                ),
                                service_id=run.get("id"),
                                project_id=target,
                            ),
                        )
                        if payload.get("likely_failure_job"):
                            append_evidence(
                                artifact,
                                evidence_item(
                                    source="github_api",
                                    type="workflow_job_failure",
                                    confidence=CONFIDENCE_CONFIRMED,
                                    message=(
                                        f"Likely failure in job `{payload.get('likely_failure_job')}`"
                                        + (
                                            f", step `{payload.get('likely_failure_step')}`."
                                            if payload.get("likely_failure_step")
                                            else "."
                                        )
                                    ),
                                    project_id=target,
                                ),
                            )
                    artifact.diagnostic = {
                        "primary_finding": payload.get("output"),
                        "failure_confidence": confidence,
                        "logs_implemented": False,
                    }
                elif payload.get("auth_error"):
                    artifact.confidence = CONFIDENCE_INSUFFICIENT
                    artifact.diagnostic = {
                        "primary_finding": payload.get("output"),
                        "failure_confidence": CONFIDENCE_INSUFFICIENT,
                    }
            elif action == "github_api_workflow_jobs" and adapter and target:
                payload = _run_step(
                    "github_api_workflow_jobs",
                    lambda: adapter.get_workflow_jobs(repository=target),
                    job_id=job_id,
                )
                artifact.findings.append(
                    {
                        "action": action,
                        "source": "provider_api",
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "repository": payload.get("repository"),
                        "latest_failed_run": payload.get("latest_failed_run"),
                        "failed_jobs": payload.get("failed_jobs"),
                        "no_failed_jobs": payload.get("no_failed_jobs"),
                        "log_download_implemented": payload.get("log_download_implemented"),
                    }
                )
                if payload.get("ok"):
                    confidence = str(payload.get("confidence") or CONFIDENCE_CONFIRMED)
                    artifact.confidence = confidence
                    if payload.get("no_failed_jobs"):
                        append_evidence(
                            artifact,
                            evidence_item(
                                source="github_api",
                                type="workflow_jobs",
                                confidence=CONFIDENCE_CONFIRMED,
                                message=f"No failed workflow jobs in recent history for `{target}`.",
                                project_id=target,
                            ),
                        )
                    else:
                        run = payload.get("latest_failed_run") if isinstance(payload.get("latest_failed_run"), dict) else {}
                        append_evidence(
                            artifact,
                            evidence_item(
                                source="github_api",
                                type="workflow_run",
                                confidence=CONFIDENCE_CONFIRMED,
                                message=(
                                    f"Latest failed run `{run.get('name') or 'workflow'}` "
                                    f"#{run.get('run_number')} on `{run.get('head_branch') or '—'}`."
                                ),
                                service_id=run.get("id"),
                                project_id=target,
                            ),
                        )
                        for job in payload.get("failed_jobs") or []:
                            if not isinstance(job, dict):
                                continue
                            step_note = f", step `{job['failed_step']}`" if job.get("failed_step") else ""
                            append_evidence(
                                artifact,
                                evidence_item(
                                    source="github_api",
                                    type="workflow_job",
                                    confidence=CONFIDENCE_CONFIRMED,
                                    message=f"Failed job `{job.get('name')}` — {job.get('conclusion') or 'failure'}{step_note}.",
                                    service_id=job.get("id"),
                                    project_id=target,
                                ),
                            )
                    artifact.diagnostic = {
                        "primary_finding": payload.get("output"),
                        "failure_confidence": confidence,
                        "log_download_implemented": False,
                    }
                elif payload.get("auth_error"):
                    artifact.confidence = CONFIDENCE_INSUFFICIENT
                    artifact.diagnostic = {
                        "primary_finding": payload.get("output"),
                        "failure_confidence": CONFIDENCE_INSUFFICIENT,
                    }
        except Exception as exc:
            artifact.findings.append({"action": action, "output": f"error: {exc}"})

    emit_step(progress, "Formatting report")
    _append_timeline(artifact, "completed", "GitHub read-only execution finished")
    full = format_execution_report(artifact)
    auth_label = auth["auth_method_label"] or auth["auth_method"]
    summary = (
        f"Read-only GitHub {operation_type.replace('_', ' ')} for `{target}` "
        f"via {auth_label} · Provider API execution · confidence: {artifact.confidence}."
    )
    return ExecutionOutcome(artifact=artifact, summary=summary[:500], preview=summary[:240], full_result=full)
