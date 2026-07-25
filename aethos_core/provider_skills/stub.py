# SPDX-License-Identifier: Apache-2.0
"""Stub provider skills — contract placeholders until real operations are implemented."""

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


class StubProviderSkill(ProviderSkillBase):
    """Governed placeholder skill — dry-run fails honestly; no silent mutation."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        return {
            "ok": False,
            "error": f"{self.provider} discovery is not implemented yet.",
            "inventory": {"provider": self.provider, "projects": [], "freshness": "unsupported"},
        }

    def plan(
        self,
        *,
        operation: str,
        target: Any,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan:
        target_name = str(getattr(target, "service_name", None) or getattr(target, "name", None) or "unknown")
        return ProviderExecutionPlan(
            provider=self.provider,
            operation=operation,
            target_name=target_name,
            execution_mode="api",
            diagnostics={"issues": [f"{self.provider} provider skill is not implemented yet."]},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues = list(plan.diagnostics.get("issues") or [])
        issues.append(f"{self.provider} real operations are not available yet.")
        return ProviderDryRunEvidence(ok=False, plan=plan, detail=f"{self.provider} skill stub", issues=issues)

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "stub-skill",
    ) -> ProviderExecutionResult:
        return ProviderExecutionResult(
            ok=False,
            command_submitted=False,
            provider=self.provider,
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode=plan.execution_mode,
            error=f"{self.provider} provider skill is not implemented yet.",
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
            command_submitted=False,
            execution_mode=result.execution_mode,
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
        return ProviderVerificationResult(
            status="unverified",
            verified=False,
            confidence="bounded",
            reason=f"{self.provider} verification unavailable — skill not implemented.",
            state="unverified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(
            ok=False,
            category="skill_not_implemented",
            summary=f"{self.provider} diagnosis unavailable.",
            likely_cause="Provider skill not implemented.",
            requires_approval=True,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        return ProviderFixPlan(
            ok=False,
            summary=f"{self.provider} fix plans are not available yet.",
            requires_approval=True,
            preflight_required=True,
        )
