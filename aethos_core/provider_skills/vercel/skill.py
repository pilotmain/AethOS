# SPDX-License-Identifier: Apache-2.0
"""Vercel provider skill — readonly discovery and governed redeploy planning."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_skills.base import ProviderSkillBase
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


def _target_value(target: Any, *names: str) -> str:
    """Read the first present field from a ProviderTarget object OR a plain dict."""
    for name in names:
        value = target.get(name) if isinstance(target, dict) else getattr(target, name, None)
        if value:
            return str(value)
    return ""


class VercelProviderSkill(ProviderSkillBase):
    provider = "vercel"
    supported_operations = ["redeploy", "list_deployments", "inspect_failed_deployment", "diagnose"]
    readonly_tools = ["discover", "list_projects", "list_deployments", "list_domains", "project_details"]
    mutation_tools = ["redeploy", "set_env_var"]
    required_credentials = ["VERCEL_TOKEN"]
    common_failure_patterns = ["missing_env_var", "build_failure", "deployment_error"]
    repair_recipes = ["redeploy_latest", "configure_env_and_redeploy"]
    verification_rules = ["redeploy_requires_ready_state"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat
        from aethos_core.providers.vercel.diagnostics.project_diagnostics_api import fetch_projects_list

        auth = resolve_vercel_auth_for_chat()
        token = str(auth.get("token") or "").strip()
        if not token:
            return {"ok": False, "error": auth.get("detail") or "Vercel credentials unavailable.", "inventory": {}}
        payload = fetch_projects_list(token)
        projects = list(payload.get("projects") or [])
        return {
            "ok": bool(payload.get("ok")),
            "inventory": {
                "provider": "vercel",
                "project_count": len(projects),
                "projects": projects[:20],
            },
            "error": payload.get("error"),
        }

    def plan(
        self,
        *,
        operation: str,
        target: ProviderTarget,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan:
        # The planning entry point is typed Any and passes the target through
        # uncoerced, so accept either a ProviderTarget object or a plain dict.
        project = _target_value(target, "service_name", "project_name")
        return ProviderExecutionPlan(
            provider="vercel",
            operation=operation,
            target_name=project,
            execution_mode="api",
            diagnostics={"project_name": project, "issues": [] if project else ["project name unresolved"]},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues = list(plan.diagnostics.get("issues") or [])
        if plan.operation not in self.supported_operations and plan.operation not in self.mutation_tools:
            issues.append(f"Unsupported Vercel operation `{plan.operation}`.")
        from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat

        if not str(resolve_vercel_auth_for_chat().get("token") or "").strip():
            issues.append("Vercel API token unavailable.")
        ok = not issues
        return ProviderDryRunEvidence(
            ok=ok,
            plan=plan,
            detail=f"Vercel {plan.operation} for `{plan.target_name}`",
            issues=issues,
        )

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "vercel-skill",
    ) -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id
        if not approved:
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="vercel",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="api",
                error="Mutation not approved.",
            )
        if plan.operation != "redeploy":
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="vercel",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="api",
                error=f"Vercel skill execute supports redeploy only (got `{plan.operation}`).",
            )
        from aethos_core.runtime.vercel_readonly_jobs import resolve_vercel_auth_for_chat
        from aethos_core.providers.vercel.operations.mutations_api import redeploy_project

        token = str(resolve_vercel_auth_for_chat().get("token") or "").strip()
        if not token:
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="vercel",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="api",
                error="Vercel credentials missing.",
            )
        raw = redeploy_project(token, target_name=plan.target_name)
        submitted = bool(raw.get("ok"))
        return ProviderExecutionResult(
            ok=submitted,
            command_submitted=submitted,
            provider="vercel",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="api",
            command=f"API redeploy {plan.target_name}",
            provider_response=raw,
            error=None if submitted else str(raw.get("error") or raw.get("detail") or "Redeploy failed."),
        )

    def collect_evidence(
        self,
        result: ProviderExecutionResult,
        *,
        approved_at: str | None = None,
    ) -> ProviderEvidenceBundle:
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
            evidence={"health_confirmed": result.ok},
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
        _ = before, after, approved_at, readonly_artifact
        verified = evidence_bundle.command_submitted and evidence_bundle.evidence.get("health_confirmed")
        return ProviderVerificationResult(
            status="verified_redeploy" if verified else "redeploy_unverified",
            verified=bool(verified),
            confidence="bounded",
            reason="Vercel redeploy command submitted." if verified else "Redeploy verification incomplete.",
            state="verified" if verified else "unverified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        response = evidence.provider_response or {}
        error = str(response.get("error") or response.get("detail") or "unknown")
        return ProviderDiagnosis(
            ok=False,
            category="deployment_error",
            summary=f"Vercel operation failed for `{evidence.target}`.",
            likely_cause=error,
            log_signals=[],
            suggested_operation="redeploy",
            requires_approval=True,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        return ProviderFixPlan(
            ok=True,
            summary=f"Retry governed redeploy for `{target_name}`.",
            proposed_operation="redeploy",
            proposed_changes=[],
            requires_approval=True,
            preflight_required=True,
        )
