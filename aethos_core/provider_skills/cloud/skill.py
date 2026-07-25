# SPDX-License-Identifier: Apache-2.0
"""Generic Mission Control token-backed provider skill."""

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


class TokenCloudProviderSkill(ProviderSkillBase):
    """Readonly discover via Mission Control vault token + optional list APIs."""

    def __init__(self, provider: str) -> None:
        self.provider = (provider or "").strip().lower()
        self.supported_operations = ["discover", "validate_connection"]
        self.readonly_tools = ["discover", "validate_connection"]
        self.mutation_tools: list[str] = []
        self.required_credentials = [f"{self.provider.upper()}_API_TOKEN"]
        self.common_failure_patterns = ["credentials_missing", "token_invalid"]
        self.repair_recipes = []
        self.verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        from aethos_core.execution_brain.cloud_agent_bridge import discover_provider_inventory

        return discover_provider_inventory(self.provider)

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
            provider=self.provider,
            operation=operation,
            target_name=name,
            execution_mode="api",
            diagnostics={"issues": [f"{self.provider} mutations are not implemented via generic token skill."]},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        return ProviderDryRunEvidence(
            ok=False,
            plan=plan,
            detail=f"{self.provider} generic skill is readonly-only.",
            issues=[f"{self.provider} governed mutations require provider-specific preflight."],
        )

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "token-cloud-skill",
    ) -> ProviderExecutionResult:
        _ = approved, before_snapshot, approved_at, request_id
        return ProviderExecutionResult(
            ok=False,
            command_submitted=False,
            provider=self.provider,
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="api",
            error=f"{self.provider} execute not available on generic token skill.",
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
            command_submitted=False,
            execution_mode="api",
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
        _ = operation, before, after, evidence_bundle, approved_at, readonly_artifact
        return ProviderVerificationResult(
            status="unverified",
            verified=False,
            confidence="bounded",
            reason=f"{self.provider} verification unavailable on generic token skill.",
            state="unverified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(
            ok=False,
            category="readonly_only",
            summary=f"{self.provider} generic skill is discover-only.",
            likely_cause=str((evidence.provider_response or {}).get("error") or "inventory unavailable"),
            requires_approval=False,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis, target_name
        return ProviderFixPlan(
            ok=True,
            summary=f"Add or revalidate {self.provider} token in Mission Control → Providers.",
            proposed_operation="validate_connection",
            requires_approval=False,
            preflight_required=False,
        )


def fetch_token_provider_inventory(provider: str, token: str) -> dict[str, Any]:
    from aethos_core.execution_brain.provider_inventory_registry import fetch_provider_inventory

    return fetch_provider_inventory(provider, token)
