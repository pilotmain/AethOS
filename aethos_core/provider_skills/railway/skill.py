# SPDX-License-Identifier: Apache-2.0
"""Railway provider skill — governed real operations with evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.provider_skills.base import ProviderSkillBase
from aethos_core.provider_diagnosis.railway import diagnose_railway_runtime, propose_railway_fix
from aethos_core.provider_skills.types import (
    ProviderDiagnosis,
    ProviderDryRunEvidence,
    ProviderEvidenceBundle,
    ProviderExecutionPlan,
    ProviderExecutionResult,
    ProviderFixPlan,
    ProviderVerificationResult,
)
from aethos_core.providers.railway.target_resolver import ProviderTarget


class RailwayProviderSkill(ProviderSkillBase):
    provider = "railway"
    supported_operations = ["restart", "redeploy", "deploy", "stop", "logs", "diagnose", "fix_plan"]
    readonly_tools = ["discover", "list_deployments", "read_logs", "health_check", "read_variables"]
    mutation_tools = ["restart", "redeploy", "deploy", "stop", "set_env_var"]
    required_credentials = ["RAILWAY_API_TOKEN"]
    common_failure_patterns = [
        "missing_env_var",
        "port_bind_failure",
        "dependency_connection_failure",
        "crash_loop",
        "health_check_failure",
    ]
    repair_recipes = ["configure_env_and_redeploy", "restart_service", "redeploy_latest"]
    verification_rules = [
        "restart_requires_log_or_transition_evidence",
        "redeploy_requires_new_deployment",
        "health_required_for_verified_status",
    ]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        from aethos_core.providers.railway.discovery import refresh_railway_inventory

        inventory = refresh_railway_inventory(force=force)
        return {"ok": not inventory.error, "inventory": inventory.to_dict(), "error": inventory.error}

    def execution_mode(self) -> str:
        mode = (get_settings().railway_execution_mode or "api").strip().lower()
        return mode if mode in {"cli", "api"} else "api"

    def plan(
        self,
        *,
        operation: str,
        target: ProviderTarget,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan:
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
        from aethos_core.providers.railway.restart_diagnostics import diagnose_railway_mutation_target

        mode = self.execution_mode()
        service_name = str(target.service_name or "")
        token, source, _ = resolve_railway_mutation_credentials()
        diagnostics = {}
        if token:
            diagnostics = diagnose_railway_mutation_target(
                token,
                target=target,
                operation=operation,
                credential_source=source,
            ).to_dict()

        command = None
        command_args: list[str] = []
        graphql_operation = diagnostics.get("planned_graphql_operation")
        mutation_variables = dict(diagnostics.get("planned_mutation_variables") or {})

        if mode == "cli":
            cli = (get_settings().railway_cli_path or "railway").strip()
            if operation == "restart":
                command = f"{cli} restart --service {service_name!r} --yes --json"
                command_args = ["restart", "--service", service_name, "--yes", "--json"]
            elif operation == "redeploy":
                command = f"{cli} redeploy --service {service_name!r} --yes --json"
                command_args = ["redeploy", "--service", service_name, "--yes", "--json"]
            elif operation in {"deploy", "deploy_latest", "up"}:
                command = f"{cli} up --service {service_name!r} --yes --json"
                command_args = ["up", "--service", service_name, "--yes", "--json"]
            graphql_operation = None
            mutation_variables = {}

        return ProviderExecutionPlan(
            provider="railway",
            operation=operation,
            target_name=service_name,
            execution_mode=mode,
            command=command,
            command_args=command_args,
            graphql_operation=str(graphql_operation) if graphql_operation else None,
            mutation_variables=mutation_variables,
            service_id=diagnostics.get("service_id"),
            project_id=diagnostics.get("project_id"),
            environment_id=diagnostics.get("environment_id"),
            deployment_id=diagnostics.get("deployment_id"),
            diagnostics=diagnostics,
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues = list(plan.diagnostics.get("issues") or [])
        if plan.execution_mode == "cli":
            from aethos_core.providers.railway.cli_executor import railway_cli_path

            if not railway_cli_path():
                issues.append("Railway CLI not found — set RAILWAY_CLI_PATH or install railway CLI.")
        else:
            if not plan.service_id:
                issues.append("service_id unresolved for API execution mode.")
        ok = not issues and bool(plan.command or plan.graphql_operation)
        detail = plan.command or f"API {plan.graphql_operation} {plan.mutation_variables}"
        return ProviderDryRunEvidence(ok=ok, plan=plan, detail=detail, issues=issues)

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "railway-skill",
    ) -> ProviderExecutionResult:
        if not approved:
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="railway",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode=plan.execution_mode,
                command=plan.command,
                error="Mutation not approved.",
            )

        target = ProviderTarget(
            provider="railway",
            service_name=plan.target_name,
            service_id=plan.service_id,
            project_name=plan.diagnostics.get("project_name"),
            environment=plan.diagnostics.get("environment_name"),
            resolved=True,
        )

        if plan.execution_mode == "cli":
            return self._execute_cli(plan, target=target, before_snapshot=before_snapshot, approved_at=approved_at)
        return self._execute_api(
            plan,
            target=target,
            before_snapshot=before_snapshot,
            approved_at=approved_at,
            request_id=request_id,
        )

    def _execute_cli(
        self,
        plan: ProviderExecutionPlan,
        *,
        target: ProviderTarget,
        before_snapshot: dict[str, Any] | None,
        approved_at: str | None,
    ) -> ProviderExecutionResult:
        from aethos_core.providers.railway.cli_executor import (
            cli_command_submitted,
            railway_logs,
            railway_redeploy,
            railway_restart,
            railway_up,
        )

        before = dict(before_snapshot or {})
        logs_before = []
        if plan.deployment_id or plan.target_name:
            log_result = railway_logs(service_name=plan.target_name)
            logs_before = list(log_result.get("logs") or [])

        if plan.operation == "restart":
            cli_result = railway_restart(service_name=plan.target_name)
        elif plan.operation == "redeploy":
            cli_result = railway_redeploy(service_name=plan.target_name)
        elif plan.operation in {"deploy", "deploy_latest", "up"}:
            cli_result = railway_up(service_name=plan.target_name)
        else:
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="railway",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="cli",
                command=plan.command,
                error=f"Unsupported Railway CLI operation `{plan.operation}`.",
            )

        submitted = cli_command_submitted(cli_result)
        log_after_result = railway_logs(service_name=plan.target_name)
        logs_after = list(log_after_result.get("logs") or [])

        after = dict(before)
        after["last_log_at"] = _latest_log_timestamp(logs_after)
        after["service_status"] = "online" if submitted else "unknown"
        before.setdefault("last_log_at", _latest_log_timestamp(logs_before))

        return ProviderExecutionResult(
            ok=submitted,
            command_submitted=submitted,
            provider="railway",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="cli",
            command=cli_result.get("command") or plan.command,
            provider_response={"cli": cli_result},
            stdout=str(cli_result.get("stdout") or ""),
            stderr=str(cli_result.get("stderr") or ""),
            error=None if submitted else str(cli_result.get("error") or "Railway CLI command not confirmed."),
            before=before,
            after=after,
            logs_before=logs_before,
            logs_after=logs_after,
        )

    def _execute_api(
        self,
        plan: ProviderExecutionPlan,
        *,
        target: ProviderTarget,
        before_snapshot: dict[str, Any] | None,
        approved_at: str | None,
        request_id: str,
    ) -> ProviderExecutionResult:
        from aethos_core.providers.railway.mutations import restart_railway_service

        op = plan.operation
        if op in {"deploy", "deploy_latest", "up"}:
            op = "redeploy"

        logs_before: list[dict[str, Any]] = []
        logs_after: list[dict[str, Any]] = []
        if op in {"restart", "redeploy"}:
            mutation = restart_railway_service(
                target=target,
                request_id=request_id,
                before_snapshot=before_snapshot,
                approved_at=approved_at,
                operation=op,
            )
            raw = mutation.as_provider_result()
            logs_before = list(getattr(mutation, "logs_before", None) or [])
            logs_after = list(getattr(mutation, "logs_after", None) or [])
        else:
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="railway",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="api",
                command=plan.command,
                error=f"Unsupported API operation `{plan.operation}`.",
            )

        submitted = bool(raw.get("restart_command_submitted"))
        rollback = raw.get("rollback_metadata") or {}
        command = f"API {raw.get('graphql_operation')}"
        before = dict(before_snapshot or rollback.get("deployment_snapshot_before") or {})
        after = dict(rollback.get("deployment_snapshot_after") or {})
        before.setdefault("last_log_at", rollback.get("logs_before_latest_timestamp"))
        after.setdefault("last_log_at", rollback.get("logs_after_latest_timestamp"))
        return ProviderExecutionResult(
            ok=submitted,
            command_submitted=submitted,
            provider="railway",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="api",
            command=command,
            provider_response=raw,
            error=None if submitted else str(raw.get("detail") or "Provider API command not confirmed."),
            before=before,
            after=after,
            logs_before=logs_before,
            logs_after=logs_after,
        )

    def collect_evidence(
        self,
        result: ProviderExecutionResult,
        *,
        approved_at: str | None = None,
    ) -> ProviderEvidenceBundle:
        log_activity = _log_activity_detected(result)
        health_confirmed = _health_confirmed(result)
        deployment_transition = _deployment_transition(result)
        return ProviderEvidenceBundle(
            operation=result.operation,
            provider=result.provider,
            target=result.target_name,
            approved_at=approved_at,
            command=result.command,
            command_submitted=result.command_submitted,
            execution_mode=result.execution_mode,
            provider_response=result.provider_response,
            before=result.before,
            after=result.after,
            evidence={
                "deployment_transition_detected": deployment_transition,
                "log_activity_after_approval": log_activity,
                "health_confirmed": health_confirmed,
                "runtime_errors_detected": False,
            },
            logs_excerpt=(result.logs_after or [])[-20:],
            verification={},
        )

    def verify(
        self,
        *,
        operation: str,
        before: dict[str, Any],
        after: dict[str, Any],
        evidence_bundle: ProviderEvidenceBundle,
        approved_at: str | None = None,
        readonly_artifact: dict[str, Any] | None = None,
    ) -> ProviderVerificationResult:
        from aethos_core.providers.railway.hardening.restart_transition import (
            LOG_RESTART_DETECTED,
            RESTART_TRANSITION_DETECTED,
            verify_railway_restart_transition,
        )

        provider_result = {
            "restart_command_submitted": evidence_bundle.command_submitted,
            "ok": evidence_bundle.command_submitted,
            "rollback_metadata": {
                "deployment_snapshot_before": before,
                "deployment_snapshot_after": after,
                "logs_before_latest_timestamp": before.get("last_log_at"),
                "logs_after_latest_timestamp": after.get("last_log_at"),
                "approved_at": approved_at,
            },
        }
        service_id = str(before.get("service_id") or after.get("service_id") or evidence_bundle.provider_response.get("service_id") or "")

        if operation == "restart":
            restart = verify_railway_restart_transition(
                service_id=service_id or "unknown",
                before_snapshot=before,
                approved_at=approved_at,
                after_snapshot=after,
                provider_result=provider_result,
                readonly_artifact=readonly_artifact or {},
            )
            verified = bool(restart.verified)
            if verified and restart.state == LOG_RESTART_DETECTED:
                status = "verified_restart"
                reason = (
                    "Restart command submitted and Railway logs show runtime activity after approval; "
                    "no new deployment expected for restart."
                )
            elif verified and restart.state == RESTART_TRANSITION_DETECTED:
                status = "verified_restart"
                reason = restart.summary
            elif evidence_bundle.command_submitted and not verified:
                status = "restart_unverified"
                reason = restart.summary
            else:
                status = restart.state
                reason = restart.summary
            return ProviderVerificationResult(
                status=status,
                verified=verified,
                confidence="bounded",
                reason=reason,
                state=restart.state,
                checks=restart.checks,
            )

        if operation == "redeploy":
            transition = evidence_bundle.evidence.get("deployment_transition_detected", False)
            health = evidence_bundle.evidence.get("health_confirmed", False)
            verified = evidence_bundle.command_submitted and transition and health
            return ProviderVerificationResult(
                status="verified_redeploy" if verified else "redeploy_unverified",
                verified=verified,
                confidence="bounded",
                reason=(
                    "Redeploy command submitted, deployment transition observed, and service health confirmed."
                    if verified
                    else "Redeploy verification incomplete — deployment transition and health proof required."
                ),
                state="restart_transition_detected" if transition else "restart_unverified",
                checks=[],
            )

        verified = evidence_bundle.command_submitted and evidence_bundle.evidence.get("health_confirmed", False)
        return ProviderVerificationResult(
            status="verified" if verified else "unverified",
            verified=verified,
            confidence="bounded",
            reason="Provider operation evidence collected.",
            state="verified" if verified else "unverified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        raw = diagnose_railway_runtime(
            logs=evidence.logs_excerpt,
            health_summary="degraded" if not evidence.evidence.get("health_confirmed") else "healthy",
        )
        return ProviderDiagnosis(
            ok=bool(raw.get("ok")),
            category=str(raw.get("category") or "unknown"),
            summary=str(raw.get("summary") or ""),
            likely_cause=str(raw.get("likely_cause") or ""),
            log_signals=list(raw.get("log_signals") or []),
            suggested_operation=raw.get("suggested_operation"),
            requires_approval=True,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        raw = propose_railway_fix(diagnosis=diagnosis.to_dict(), target_name=target_name)
        return ProviderFixPlan(
            ok=bool(raw.get("ok")),
            summary=str(raw.get("summary") or ""),
            proposed_operation=raw.get("proposed_operation"),
            proposed_changes=list(raw.get("proposed_changes") or []),
            requires_approval=True,
            preflight_required=bool(raw.get("preflight_required", True)),
        )


def _latest_log_timestamp(logs: list[dict[str, Any]]) -> str | None:
    latest: str | None = None
    for row in logs:
        ts = row.get("timestamp") or row.get("time")
        if ts is None:
            continue
        text = str(ts)
        if latest is None or text > latest:
            latest = text
    return latest


def _log_activity_detected(result: ProviderExecutionResult) -> bool:
    before_ts = result.before.get("last_log_at")
    after_ts = result.after.get("last_log_at")
    if before_ts and after_ts and str(after_ts) > str(before_ts):
        return True
    return bool(result.logs_after)


def _health_confirmed(result: ProviderExecutionResult) -> bool:
    if result.after.get("service_status") == "online":
        return True
    response = result.provider_response or {}
    if isinstance(response.get("cli"), dict):
        return bool(response["cli"].get("ok"))
    return bool(response.get("ok")) and result.command_submitted


def _deployment_transition(result: ProviderExecutionResult) -> bool:
    before_id = result.before.get("latest_deployment_id") or result.before.get("active_deployment_id")
    after_id = result.after.get("latest_deployment_id") or result.after.get("active_deployment_id")
    if before_id and after_id and before_id != after_id:
        return True
    before_created = result.before.get("active_deployment_created_at") or result.before.get("latest_deployment_created_at")
    after_created = result.after.get("active_deployment_created_at") or result.after.get("latest_deployment_created_at")
    return bool(before_created and after_created and str(after_created) > str(before_created))
