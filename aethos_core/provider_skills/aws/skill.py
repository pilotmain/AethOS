# SPDX-License-Identifier: Apache-2.0
"""AWS provider skill — readonly inventory via boto3 when available."""

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


class AwsProviderSkill(ProviderSkillBase):
    provider = "aws"
    supported_operations = ["list_ecs_services", "list_lambda_functions", "fetch_cloudwatch_logs"]
    readonly_tools = ["discover", "cloudwatch_logs", "ecs_describe", "lambda_get"]
    mutation_tools = ["ecs_update_service", "lambda_update"]
    required_credentials = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    common_failure_patterns = ["credentials_missing", "permission_denied", "region_unavailable"]
    repair_recipes = []
    verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        creds = _aws_credentials()
        if not creds.get("ok"):
            return {"ok": False, "error": creds.get("error"), "inventory": {}}
        inventory = _readonly_inventory(region=str(creds.get("region") or "us-east-1"))
        return {"ok": inventory.get("ok", False), "inventory": inventory, "error": inventory.get("error")}

    def plan(
        self,
        *,
        operation: str,
        target: ProviderTarget,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan:
        _ = context
        name = str(target.service_name or target.project_name or "")
        return ProviderExecutionPlan(
            provider="aws",
            operation=operation,
            target_name=name,
            execution_mode="api",
            diagnostics={"target": name, "issues": [] if name else ["target unresolved"]},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues = list(plan.diagnostics.get("issues") or [])
        creds = _aws_credentials()
        if not creds.get("ok"):
            issues.append(str(creds.get("error") or "AWS credentials unavailable."))
        if plan.operation in self.mutation_tools:
            issues.append("AWS mutations require governed preflight — readonly discover only in skill lane.")
        return ProviderDryRunEvidence(
            ok=not issues,
            plan=plan,
            detail=f"AWS {plan.operation} for `{plan.target_name}`",
            issues=issues,
        )

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "aws-skill",
    ) -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id, approved
        return ProviderExecutionResult(
            ok=False,
            command_submitted=False,
            provider="aws",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="api",
            error="AWS skill is readonly — use governed mutation preflight for changes.",
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
            evidence={"readonly": True},
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
        return ProviderVerificationResult(
            status="verified",
            verified=True,
            confidence="bounded",
            reason="AWS readonly verification not required.",
            state="verified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(
            ok=False,
            category="aws_readonly",
            summary=f"AWS issue for `{evidence.target}`.",
            likely_cause=str((evidence.provider_response or {}).get("error") or "inventory unavailable"),
            log_signals=[],
            suggested_operation="discover",
            requires_approval=False,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis
        return ProviderFixPlan(
            ok=True,
            summary=f"Configure AWS credentials for `{target_name}`.",
            proposed_operation="discover",
            proposed_changes=[],
            requires_approval=False,
            preflight_required=False,
        )


def _aws_credentials() -> dict[str, Any]:
    import os

    from aethos_core.execution_brain.cloud_agent_bridge import parse_aws_vault_token

    try:
        from aethos_core.credentials import get_provider_api_token

        vault_token = get_provider_api_token("aws", require_validated=False)
        if vault_token:
            parsed = parse_aws_vault_token(vault_token)
            if parsed.get("ok"):
                return parsed
    except Exception:
        pass

    key = str(os.environ.get("AWS_ACCESS_KEY_ID") or "").strip()
    secret = str(os.environ.get("AWS_SECRET_ACCESS_KEY") or "").strip()
    region = str(os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1").strip()
    if not key or not secret:
        return {
            "ok": False,
            "error": "AWS credentials not configured in Mission Control → Providers (or AWS_ACCESS_KEY_ID env).",
        }
    return {"ok": True, "access_key": key, "secret_key": secret, "region": region}


def _readonly_inventory(*, region: str) -> dict[str, Any]:
    try:
        import boto3  # type: ignore
    except ImportError:
        return {
            "ok": False,
            "error": "boto3 not installed — add optional dependency `aethos[cloud]`.",
            "provider": "aws",
            "region": region,
        }

    creds = _aws_credentials()
    if not creds.get("ok"):
        return {"ok": False, "error": creds.get("error"), "provider": "aws", "region": region}

    session = boto3.Session(
        aws_access_key_id=str(creds["access_key"]),
        aws_secret_access_key=str(creds["secret_key"]),
        region_name=region,
    )
    ecs_services: list[str] = []
    lambda_functions: list[str] = []
    try:
        ecs = session.client("ecs")
        clusters = ecs.list_clusters(maxResults=5).get("clusterArns") or []
        for arn in clusters[:3]:
            svcs = ecs.list_services(cluster=arn, maxResults=10).get("serviceArns") or []
            ecs_services.extend(str(s).split("/")[-1] for s in svcs[:10])
    except Exception as exc:
        ecs_services = []
        ecs_error = str(exc)[:200]
    else:
        ecs_error = None

    try:
        lam = session.client("lambda")
        resp = lam.list_functions(MaxItems=20)
        lambda_functions = [str(fn.get("FunctionName") or "") for fn in resp.get("Functions") or [] if fn.get("FunctionName")]
    except Exception as exc:
        lambda_functions = []
        lambda_error = str(exc)[:200]
    else:
        lambda_error = None

    return {
        "ok": True,
        "provider": "aws",
        "region": region,
        "ecs_service_count": len(ecs_services),
        "ecs_services": ecs_services[:20],
        "lambda_function_count": len(lambda_functions),
        "lambda_functions": lambda_functions[:20],
        "ecs_error": ecs_error,
        "lambda_error": lambda_error,
    }
