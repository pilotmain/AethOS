# SPDX-License-Identifier: Apache-2.0
"""Railway read-only execution runner."""

from __future__ import annotations

import logging
from typing import Any

from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact, format_execution_report
from aethos_core.operations.execution.execution_evidence import append_evidence, evidence_from_deployment, evidence_from_log_payload
from aethos_core.operations.execution.execution_permissions import assert_readonly_action
from aethos_core.operations.execution.execution_progress import ACTION_PROGRESS, emit_step, progress_emitter
from aethos_core.operations.execution.execution_runner import ExecutionOutcome, _append_timeline, _new_execution_id, _run_step
from aethos_core.connections.adapters import provider_auth_source_phrase
from aethos_core.operations.execution.execution_evidence import CONFIDENCE_CONFIRMED, evidence_item
from aethos_core.operations.railway_operation_capabilities import resolve_execution_auth

_log = logging.getLogger(__name__)


def run_railway_readonly_execution(*, params: dict[str, Any], job_id: str | None = None) -> ExecutionOutcome:
    progress = progress_emitter(job_id)
    emit_step(progress, "Preparing read-only checks")
    actions = list(params.get("approved_actions") or [])
    target = str(params.get("target_name") or "")
    operation_type = str(params.get("operation_type") or "check_logs")
    emit_step(progress, "Building adapter")
    auth = resolve_execution_auth(operation_type, params)
    adapter = None
    if auth["auth_method"] == "api_token" and auth["credential_id"]:
        from aethos_core.operations.orchestration.registry_runtime import resolve_readonly_execution_adapter

        adapter = resolve_readonly_execution_adapter("railway", auth["credential_id"])
    artifact = ExecutionArtifact(
        execution_id=_new_execution_id(),
        provider="railway",
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
        f"Read-only Railway {operation_type.replace('_', ' ')} for `{target}` "
        f"using your {provider_auth_source_phrase('railway', auth['auth_method'])}",
    )

    api_deployments: dict[str, Any] | None = None
    api_log_payload: dict[str, Any] | None = None

    for action in actions:
        assert_readonly_action(action)
        emit_step(progress, ACTION_PROGRESS.get(action, action.replace("_", " ")))
        _append_timeline(artifact, "running", action)
        try:
            if action == "railway_api_deployments" and adapter and target:
                payload = _run_step(
                    "railway_api_deployments",
                    lambda: adapter.get_deployments(project_name=target),
                    job_id=job_id,
                )
                api_deployments = payload
                artifact.findings.append(
                    {
                        "action": action,
                        "source": "provider_api",
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "deployments": payload.get("deployments"),
                    }
                )
                for dep in payload.get("deployments") or []:
                    if isinstance(dep, dict):
                        for item in evidence_from_deployment(dep, source="railway_api"):
                            append_evidence(artifact, item)
                if payload.get("ok"):
                    artifact.confidence = CONFIDENCE_CONFIRMED
            elif action == "railway_api_project_details" and adapter and target:
                payload = _run_step(
                    "railway_api_project_details",
                    lambda: adapter.get_project_details(project_name=target),
                    job_id=job_id,
                )
                artifact.findings.append(
                    {
                        "action": action,
                        "source": "provider_api",
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "details": payload.get("details"),
                    }
                )
                if payload.get("ok"):
                    details = payload.get("details") if isinstance(payload.get("details"), dict) else {}
                    service = str(details.get("service_name") or target)
                    project = str(details.get("project_name") or "—")
                    append_evidence(
                        artifact,
                        evidence_item(
                            source="railway_api",
                            type="service_details",
                            confidence=CONFIDENCE_CONFIRMED,
                            message=f"Service `{service}` in project `{project}`.",
                            service_id=details.get("service_id"),
                            project_id=details.get("project_id"),
                        ),
                    )
                    artifact.confidence = CONFIDENCE_CONFIRMED
            elif action == "railway_api_logs" and adapter and target:
                payload = _run_step(
                    "railway_api_logs",
                    lambda: adapter.get_deployment_logs(project_name=target),
                    job_id=job_id,
                )
                api_log_payload = payload
                artifact.findings.append(
                    {
                        "action": action,
                        "source": "provider_api",
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "deployment_id": payload.get("deployment_id"),
                    }
                )
                for item in evidence_from_log_payload(payload):
                    append_evidence(artifact, item)
                if payload.get("ok"):
                    artifact.confidence = CONFIDENCE_CONFIRMED
        except Exception as exc:
            artifact.findings.append({"action": action, "output": f"error: {exc}"})

    emit_step(progress, "Building evidence artifact")
    if operation_type in ("why_down", "inspect_failed_deployment"):
        from aethos_core.operations.execution.failure_diagnostic_artifact import enrich_failure_diagnostic_artifact

        enrich_failure_diagnostic_artifact(
            artifact,
            inventory_evidence=[],
            api_deployments=api_deployments,
            api_log_payload=api_log_payload,
            prod_url=None,
            reachability=None,
        )

    emit_step(progress, "Formatting report")
    _append_timeline(artifact, "completed", "Railway read-only execution finished")
    full = format_execution_report(artifact)
    auth_label = auth["auth_method_label"] or auth["auth_method"]
    summary = (
        f"Read-only Railway {operation_type.replace('_', ' ')} for `{target}` "
        f"via {auth_label} · Provider API execution · confidence: {artifact.confidence}."
    )
    if artifact.probable_root_cause:
        summary += f" {artifact.diagnostic.get('primary_finding', artifact.probable_root_cause)}"
    return ExecutionOutcome(artifact=artifact, summary=summary[:500], preview=summary[:240], full_result=full)
