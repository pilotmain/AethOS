# SPDX-License-Identifier: Apache-2.0
"""Railway governed mutations — restart/redeploy with provider truth."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.target_resolver import ProviderTarget


@dataclass
class RailwayMutationResult:
    provider: str
    operation: str
    target_name: str
    target_id: str | None
    success: bool
    provider_request_id: str | None
    deployment_id: str | None
    raw_response: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    executed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "target_name": self.target_name,
            "target_id": self.target_id,
            "success": self.success,
            "provider_request_id": self.provider_request_id,
            "deployment_id": self.deployment_id,
            "raw_response": dict(self.raw_response),
            "error": self.error,
            "executed_at": self.executed_at,
            "restart_command_submitted": getattr(self, "restart_command_submitted", False),
            "graphql_operation": getattr(self, "graphql_operation", None),
            "environment_id": getattr(self, "environment_id", None),
            "project_id": getattr(self, "project_id", None),
        }

    def as_provider_result(self) -> dict[str, Any]:
        """Adapter-compatible result for mutation execution orchestration."""
        restart_command_submitted = bool(getattr(self, "restart_command_submitted", False))
        graphql_operation = str(getattr(self, "graphql_operation", "") or "unknown")
        mutation_diagnostics = getattr(self, "mutation_diagnostics", None)
        environment_id = getattr(self, "environment_id", None)
        project_id = getattr(self, "project_id", None)
        logs_before = getattr(self, "logs_before", None)
        logs_after = getattr(self, "logs_after", None)

        if not self.success:
            failure = "provider_auth_failure" if self.error and "credential" in self.error.lower() else "mutation_failed"
            return {
                "ok": False,
                "detail": self.error or "Railway mutation failed.",
                "failure_type": failure,
                "failure_classification": failure,
                "restart_command_submitted": False,
                "provider_result": self.to_dict(),
                "railway_mutation_result": self.to_dict(),
                "mutation_diagnostics": mutation_diagnostics,
            }

        rollback_metadata: dict[str, Any] = {
            "deployment_id": self.deployment_id,
            "service_id": self.target_id,
            "environment_id": environment_id,
            "project_id": project_id,
            "recovery_guidance": [
                "Redeploy prior deployment if service remains unhealthy",
                "Inspect Railway deployment logs and failed deployment history",
                "Inspect readonly list_deployments verification evidence",
            ],
        }
        before_snapshot = getattr(self, "before_snapshot", None)
        after_snapshot = getattr(self, "after_snapshot", None)
        approved_at = getattr(self, "approved_at", None)
        if isinstance(before_snapshot, dict):
            rollback_metadata["deployment_snapshot_before"] = before_snapshot
        if isinstance(after_snapshot, dict):
            rollback_metadata["deployment_snapshot_after"] = after_snapshot
            rollback_metadata["deployment_state_after"] = after_snapshot.get("latest_deployment_status")
        if before_snapshot and isinstance(before_snapshot, dict):
            rollback_metadata["deployment_state_before"] = before_snapshot.get("latest_deployment_status")
        if approved_at:
            rollback_metadata["approved_at"] = approved_at
        if isinstance(logs_before, list):
            rollback_metadata["logs_before_latest_timestamp"] = _latest_log_timestamp(logs_before)
        if isinstance(logs_after, list):
            rollback_metadata["logs_after_latest_timestamp"] = _latest_log_timestamp(logs_after)

        detail = (
            f"Railway restart command submitted via `{graphql_operation}` for `{self.target_name}`."
            if restart_command_submitted
            else f"Railway GraphQL call completed but restart command was not confirmed for `{self.target_name}`."
        )

        return {
            "ok": restart_command_submitted,
            "detail": detail,
            "service_id": self.target_id,
            "service_name": self.target_name,
            "project_id": project_id,
            "environment_id": environment_id,
            "deployment_id": self.deployment_id,
            "deployment_or_restart_id": self.deployment_id,
            "provider_request_id": self.provider_request_id,
            "operation": self.operation,
            "graphql_operation": graphql_operation,
            "http_status": 200,
            "railway_response": self.raw_response.get("graphql") or self.raw_response,
            "restart_requested_at": self.executed_at,
            "restart_command_submitted": restart_command_submitted,
            "execution_state": "provider_mutation_requested" if restart_command_submitted else "execution_failed",
            "provider_result": self.to_dict(),
            "railway_mutation_result": self.to_dict(),
            "mutation_diagnostics": mutation_diagnostics,
            "evidence": {
                "provider": "railway",
                "operation": self.operation,
                "executed": restart_command_submitted,
                "provider_mutation_requested": restart_command_submitted,
                "restart_command_submitted": restart_command_submitted,
                "service_name": self.target_name,
                "service_id": self.target_id,
                "project_id": project_id,
                "environment_id": environment_id,
                "deployment_id": self.deployment_id,
                "provider_request_id": self.provider_request_id,
                "graphql_operation": graphql_operation,
                "executed_at": self.executed_at,
                "mutation_diagnostics": mutation_diagnostics,
                "logs_before_latest_timestamp": rollback_metadata.get("logs_before_latest_timestamp"),
                "logs_after_latest_timestamp": rollback_metadata.get("logs_after_latest_timestamp"),
            },
            "rollback_metadata": rollback_metadata,
        }


def _latest_log_timestamp(logs: list[dict[str, Any]]) -> str | None:
    latest: str | None = None
    for row in logs:
        ts = row.get("timestamp")
        if ts is None:
            continue
        text = str(ts)
        if latest is None or text > latest:
            latest = text
    return latest


def resolve_railway_mutation_credentials() -> tuple[str | None, str, str | None]:
    """Return (token, source, error_message) via canonical credential truth."""
    from aethos_core.providers.railway.credential_truth import resolve_railway_credential

    resolved = resolve_railway_credential()
    if not resolved.ok or not resolved.token:
        return None, resolved.source, resolved.detail or "Railway mutation credentials are not configured."
    source = {"validated_vault": "vault", "explicit_credential": "vault", "environment": "env"}.get(
        resolved.source, resolved.source
    )
    return resolved.token, source, None


def _provider_target_from_params(params: dict[str, Any]) -> ProviderTarget:
    raw = params.get("target")
    if isinstance(raw, dict):
        return ProviderTarget(
            provider="railway",
            service_name=str(raw.get("service_name") or params.get("target_name") or ""),
            project_name=raw.get("project_name"),
            environment=raw.get("environment"),
            service_id=raw.get("service_id"),
            confidence=float(raw.get("confidence") or 0.0),
            resolved=bool(raw.get("resolved")),
            source=str(raw.get("source") or "job_params"),
        )
    name = str(params.get("target_name") or "")
    return ProviderTarget(
        provider="railway",
        service_name=name or None,
        resolved=bool(name),
        source="job_params",
    )


def _failure_result(
    *,
    target: ProviderTarget,
    request_id: str,
    source: str,
    error: str,
    executed_at: str,
    mutation_diagnostics: dict[str, Any] | None = None,
    deployment_id: str | None = None,
    service_id: str | None = None,
) -> RailwayMutationResult:
    result = RailwayMutationResult(
        provider="railway",
        operation="restart",
        target_name=str(target.service_name or ""),
        target_id=service_id or target.service_id,
        success=False,
        provider_request_id=None,
        deployment_id=deployment_id,
        error=error,
        executed_at=executed_at,
        raw_response={"request_id": request_id, "credential_source": source},
    )
    result.restart_command_submitted = False
    result.mutation_diagnostics = mutation_diagnostics
    return result


def restart_railway_service(
    *,
    target: ProviderTarget,
    request_id: str,
    before_snapshot: dict[str, Any] | None = None,
    approved_at: str | None = None,
    operation: str = "restart",
) -> RailwayMutationResult:
    now = datetime.now(UTC).isoformat()
    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return _failure_result(
            target=target,
            request_id=request_id,
            source=source,
            error=cred_error or "Railway mutation credentials are not configured.",
            executed_at=now,
        )

    from aethos_core.providers.railway.api_client import fetch_deployment_logs, list_service_deployments
    from aethos_core.providers.railway.hardening.restart_transition import (
        RailwayDeploymentSnapshot,
        capture_railway_deployment_snapshot,
        snapshot_from_deployments,
    )
    from aethos_core.providers.railway.operations.mutations_api import (
        submit_deployment_restart,
        submit_service_instance_redeploy,
    )
    from aethos_core.providers.railway.restart_diagnostics import diagnose_railway_mutation_target

    governed_operation = operation if operation in {"restart", "redeploy"} else "restart"
    diagnostics = diagnose_railway_mutation_target(
        token,
        target=target,
        operation=governed_operation,
        credential_source=source,
    )
    diagnostics_dict = diagnostics.to_dict()
    if not diagnostics.ok:
        issue_text = "; ".join(diagnostics.issues) or "Railway restart target diagnostics failed."
        return _failure_result(
            target=target,
            request_id=request_id,
            source=source,
            error=issue_text,
            executed_at=now,
            mutation_diagnostics=diagnostics_dict,
            service_id=diagnostics.service_id,
            deployment_id=diagnostics.deployment_id,
        )

    service_id = str(diagnostics.service_id or "")
    service_name = str(diagnostics.service_name or target.service_name or "")
    deployment_id = str(diagnostics.deployment_id or "")
    environment_id = str(diagnostics.environment_id or "")
    project_id = str(diagnostics.project_id or "")

    if isinstance(before_snapshot, dict) and before_snapshot.get("service_id"):
        before_snap = RailwayDeploymentSnapshot.from_dict(before_snapshot)
    else:
        before_snap = capture_railway_deployment_snapshot(
            token,
            service_id,
            captured_at=approved_at or now,
        )

    logs_before = fetch_deployment_logs(token, deployment_id=deployment_id) if deployment_id else []

    provider_operation = (get_settings().railway_restart_provider_operation or "service_instance_redeploy").strip().lower()
    if provider_operation in {"service_instance_redeploy", "serviceinstanceredeploy"}:
        submitted = submit_service_instance_redeploy(
            token,
            environment_id=environment_id,
            service_id=service_id,
        )
        graphql_operation = "serviceInstanceRedeploy"
    else:
        submitted = submit_deployment_restart(token, deployment_id=deployment_id)
        graphql_operation = "deploymentRestart"

    restart_command_submitted = bool(submitted.get("restart_command_submitted"))
    after_deployments = list_service_deployments(token, service_id=service_id, limit=5)
    after_snap = capture_railway_deployment_snapshot(token, service_id, captured_at=datetime.now(UTC).isoformat())
    captured_at = getattr(after_snap, "captured_at", None) or datetime.now(UTC).isoformat()
    if after_deployments:
        after_snap = snapshot_from_deployments(service_id, after_deployments, captured_at)
    logs_after = fetch_deployment_logs(token, deployment_id=deployment_id) if deployment_id else []

    if not restart_command_submitted:
        err = str(submitted.get("detail") or "Railway restart command was not confirmed by provider response.")
        result = _failure_result(
            target=target,
            request_id=request_id,
            source=source,
            error=err,
            executed_at=now,
            mutation_diagnostics=diagnostics_dict,
            deployment_id=deployment_id or None,
            service_id=service_id or None,
        )
        result.raw_response = {
            "request_id": request_id,
            "credential_source": source,
            "graphql": submitted.get("railway_response"),
            "graphql_errors": submitted.get("graphql_errors"),
            "mutation_variables": submitted.get("mutation_variables"),
            "http_status": 200 if submitted.get("graphql_ok") else None,
        }
        result.graphql_operation = graphql_operation
        result.environment_id = environment_id or None
        result.project_id = project_id or None
        result.before_snapshot = before_snap.to_dict() if before_snap else None
        result.after_snapshot = after_snap.to_dict()
        result.approved_at = approved_at
        result.logs_before = logs_before
        result.logs_after = logs_after
        return result

    result = RailwayMutationResult(
        provider="railway",
        operation=governed_operation,
        target_name=service_name,
        target_id=service_id or None,
        success=True,
        provider_request_id=submitted.get("provider_request_id"),
        deployment_id=deployment_id or None,
        raw_response={
            "request_id": request_id,
            "credential_source": source,
            "graphql": submitted.get("railway_response"),
            "mutation_variables": submitted.get("mutation_variables"),
            "http_status": 200,
        },
        executed_at=now,
    )
    result.restart_command_submitted = True
    result.graphql_operation = graphql_operation
    result.environment_id = environment_id or None
    result.project_id = project_id or None
    result.mutation_diagnostics = diagnostics_dict
    result.before_snapshot = before_snap.to_dict() if before_snap else None
    result.after_snapshot = after_snap.to_dict()
    result.approved_at = approved_at
    result.logs_before = logs_before
    result.logs_after = logs_after
    return result


def _provider_result_from_skill(skill_payload: dict[str, Any], *, operation: str, target: ProviderTarget) -> dict[str, Any]:
    bundle = skill_payload.get("evidence_bundle") or {}
    verification = skill_payload.get("verification") or {}
    exec_result = skill_payload.get("execution_result") or {}
    submitted = bool(skill_payload.get("command_submitted"))
    provider_response = exec_result.get("provider_response") or {}
    if isinstance(provider_response, dict) and provider_response.get("cli"):
        cli = provider_response["cli"]
        detail = (
            f"Railway restart command submitted via CLI for `{target.service_name}`."
            if submitted
            else str(cli.get("error") or skill_payload.get("error") or "Railway CLI command not confirmed.")
        )
    else:
        detail = (
            f"Railway {operation} command submitted."
            if submitted
            else str(exec_result.get("error") or "Provider command not confirmed.")
        )
    rollback_metadata = {
        "deployment_snapshot_before": bundle.get("before") or {},
        "deployment_snapshot_after": bundle.get("after") or {},
        "logs_before_latest_timestamp": (bundle.get("before") or {}).get("last_log_at"),
        "logs_after_latest_timestamp": (bundle.get("after") or {}).get("last_log_at"),
        "approved_at": bundle.get("approved_at"),
        "service_id": (bundle.get("before") or {}).get("service_id") or target.service_id,
    }
    return {
        "ok": submitted,
        "detail": detail,
        "restart_command_submitted": submitted,
        "execution_state": "provider_mutation_requested" if submitted else "execution_failed",
        "execution_mode": skill_payload.get("execution_mode"),
        "command": skill_payload.get("command"),
        "service_id": target.service_id,
        "service_name": target.service_name,
        "graphql_operation": provider_response.get("graphql_operation") if isinstance(provider_response, dict) else None,
        "provider_result": exec_result,
        "railway_mutation_result": exec_result,
        "provider_evidence_bundle": bundle,
        "verification_preview": verification,
        "rollback_metadata": rollback_metadata,
        "evidence": {
            "provider": "railway",
            "operation": operation,
            "executed": submitted,
            "restart_command_submitted": submitted,
            "command": skill_payload.get("command"),
            "execution_mode": skill_payload.get("execution_mode"),
        },
    }


def execute_railway_mutation(*, operation: str, params: dict[str, Any], request_id: str) -> dict[str, Any]:
    target = _provider_target_from_params(params)
    before_snapshot = params.get("railway_before_snapshot")
    approved_at = params.get("mutation_execution_approved_at_iso")
    normalized_op = operation
    if operation in {"deploy_latest", "up"}:
        normalized_op = "deploy"

    if normalized_op in {"restart", "redeploy", "deploy"}:
        from aethos_core.provider_skills.runtime import execute_provider_operation

        skill_payload = execute_provider_operation(
            provider="railway",
            operation=normalized_op,
            target=target,
            approved=bool(params.get("mutation_execution_approved", True)),
            job_id=str(params.get("mutation_execution_job_id") or request_id),
            before_snapshot=before_snapshot if isinstance(before_snapshot, dict) else None,
            approved_at=str(approved_at) if approved_at else None,
            request_id=request_id,
        )
        return _provider_result_from_skill(skill_payload, operation=operation, target=target)

    if operation == "stop":
        from aethos_core.providers.railway.operations.mutations_api import stop_service

        token, source, cred_error = resolve_railway_mutation_credentials()
        if not token:
            return {"ok": False, "detail": cred_error or "Railway credentials not configured.", "failure_type": "provider_auth_failure"}
        target_name = str(params.get("target_name") or target.service_name or "")
        raw = stop_service(token, target_name=target_name)
        raw["credential_source"] = source
        return raw

    if operation == "set_env_var":
        return execute_railway_set_env_var(params=params, request_id=request_id, target=target)

    return {"ok": False, "detail": f"Unsupported Railway operation `{operation}`.", "failure_type": "unsupported_mutation"}


def execute_railway_set_env_var(
    *,
    params: dict[str, Any],
    request_id: str,
    target: ProviderTarget,
) -> dict[str, Any]:
    """Governed Railway env var write — stage + commit (skipDeploys), never log values."""
    now = datetime.now(UTC).isoformat()
    token, source, cred_error = resolve_railway_mutation_credentials()
    if not token:
        return {"ok": False, "detail": cred_error or "Railway credentials not configured.", "failure_type": "provider_auth_failure"}

    env_name = str(params.get("env_var_name") or "").strip()
    env_value = str(params.get("env_var_value") or "").strip()
    if not env_name or not env_value:
        return {"ok": False, "detail": "Env var name and value required via secure preflight reference."}

    from aethos_core.providers.railway.greenfield_adapters.env_configure_graphql import (
        commit_staged_env_changes_skip_deploy,
        stage_service_env_variables,
    )
    from aethos_core.providers.railway.restart_diagnostics import diagnose_railway_mutation_target

    diagnostics = diagnose_railway_mutation_target(token, target=target, operation="set_env_var", credential_source=source)
    if not diagnostics.ok:
        return {
            "ok": False,
            "detail": "; ".join(diagnostics.issues) or "Target resolution failed.",
            "failure_type": "target_resolution_failed",
        }

    environment_id = str(diagnostics.environment_id or "")
    service_id = str(diagnostics.service_id or "")
    if not environment_id or not service_id:
        return {"ok": False, "detail": "Railway environment/service IDs unavailable for env write."}

    staged = stage_service_env_variables(
        token,
        environment_id=environment_id,
        service_id=service_id,
        variables={env_name: env_value},
    )
    if not staged.get("ok"):
        return {"ok": False, "detail": str(staged.get("detail") or "Env stage failed.")}

    committed = commit_staged_env_changes_skip_deploy(
        token,
        environment_id=environment_id,
        commit_message=f"AethOS governed set_env_var {env_name} ({request_id})",
    )
    if not committed.get("ok"):
        return {"ok": False, "detail": str(committed.get("detail") or "Env commit failed.")}

    return {
        "ok": True,
        "detail": f"Railway env var `{env_name}` staged and committed (skipDeploys). Redeploy separately if required.",
        "operation": "set_env_var",
        "service_id": service_id,
        "environment_id": environment_id,
        "env_var_name": env_name,
        "executed_at": now,
        "request_id": request_id,
    }
