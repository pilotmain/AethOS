# SPDX-License-Identifier: Apache-2.0
"""GitHub provider skill — workflow discovery and governed rerun planning."""

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


class GitHubProviderSkill(ProviderSkillBase):
    provider = "github"
    supported_operations = ["workflow_rerun", "workflow_dispatch", "inspect_repo", "workflow_diagnostic"]
    readonly_tools = ["discover", "list_repos", "workflow_runs", "workflow_jobs", "branch_status"]
    mutation_tools = ["workflow_rerun", "workflow_dispatch"]
    required_credentials = ["GITHUB_TOKEN"]
    common_failure_patterns = ["workflow_failure", "no_failed_workflow", "permission_denied"]
    repair_recipes = ["workflow_rerun"]
    verification_rules = ["rerun_requires_success_conclusion"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        token = _github_token()
        if not token:
            return {"ok": False, "error": "GitHub credentials unavailable.", "inventory": {}}
        from aethos_core.providers.github.api_client import list_repositories

        payload = list_repositories(token)
        repos = list(payload.get("repositories") or payload.get("items") or [])
        return {
            "ok": bool(payload.get("ok", True) and repos is not None),
            "inventory": {"provider": "github", "repository_count": len(repos), "repositories": repos[:20]},
            "error": payload.get("error"),
        }

    def plan(
        self,
        *,
        operation: str,
        target: ProviderTarget,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan:
        repo = str(target.service_name or target.project_name or "")
        return ProviderExecutionPlan(
            provider="github",
            operation=operation,
            target_name=repo,
            execution_mode="api",
            diagnostics={"repository": repo, "issues": [] if repo else ["repository unresolved"]},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues = list(plan.diagnostics.get("issues") or [])
        if not _github_token():
            issues.append("GitHub API token unavailable.")
        ok = not issues
        return ProviderDryRunEvidence(ok=ok, plan=plan, detail=f"GitHub {plan.operation} for `{plan.target_name}`", issues=issues)

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "github-skill",
    ) -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id
        if not approved:
            return ProviderExecutionResult(
                ok=False,
                command_submitted=False,
                provider="github",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="api",
                error="Mutation not approved.",
            )
        if plan.operation == "workflow_dispatch":
            from aethos_core.config import get_settings

            if not get_settings().github_workflow_dispatch_enabled:
                return ProviderExecutionResult(
                    ok=False,
                    command_submitted=False,
                    provider="github",
                    operation=plan.operation,
                    target_name=plan.target_name,
                    execution_mode="api",
                    error="GitHub workflow_dispatch lane disabled — set GITHUB_WORKFLOW_DISPATCH_ENABLED=true.",
                )
            token = _github_token()
            if not token:
                return ProviderExecutionResult(
                    ok=False,
                    command_submitted=False,
                    provider="github",
                    operation=plan.operation,
                    target_name=plan.target_name,
                    execution_mode="api",
                    error="GitHub credentials unavailable.",
                )
            diagnostics = dict(plan.diagnostics or {})
            workflow_id = diagnostics.get("workflow_id") or diagnostics.get("workflow_name") or "deploy.yml"
            ref = str(diagnostics.get("ref") or "main")
            from aethos_core.providers.github.operations.workflow_dispatch_api import dispatch_workflow

            payload = dispatch_workflow(
                token,
                repository=plan.target_name,
                workflow_id=str(workflow_id),
                ref=ref,
                inputs=diagnostics.get("inputs") if isinstance(diagnostics.get("inputs"), dict) else None,
            )
            return ProviderExecutionResult(
                ok=bool(payload.get("ok")),
                command_submitted=bool(payload.get("ok")),
                provider="github",
                operation=plan.operation,
                target_name=plan.target_name,
                execution_mode="api",
                provider_response=payload,
                error=None if payload.get("ok") else str(payload.get("detail") or "dispatch failed"),
            )
        return ProviderExecutionResult(
            ok=False,
            command_submitted=False,
            provider="github",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="api",
            error="Use governed mutation preflight for GitHub workflow rerun — skill execute is plan-only.",
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
            evidence={"command_submitted": result.command_submitted},
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
        _ = operation, before, after, approved_at, readonly_artifact
        verified = bool(evidence_bundle.evidence.get("command_submitted"))
        return ProviderVerificationResult(
            status="verified" if verified else "unverified",
            verified=verified,
            confidence="bounded",
            reason="GitHub workflow evidence collected.",
            state="verified" if verified else "unverified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(
            ok=False,
            category="workflow_failure",
            summary=f"GitHub workflow issue for `{evidence.target}`.",
            likely_cause=str((evidence.provider_response or {}).get("error") or "workflow failed"),
            log_signals=[],
            suggested_operation="workflow_rerun",
            requires_approval=True,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        return ProviderFixPlan(
            ok=True,
            summary=f"Retry governed workflow rerun for `{target_name}`.",
            proposed_operation="workflow_rerun",
            proposed_changes=[],
            requires_approval=True,
            preflight_required=True,
        )


def _github_token() -> str | None:
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token("github")
        return str(token).strip() if token else None
    except Exception:
        return None
