# SPDX-License-Identifier: Apache-2.0
"""Provider skill base contract — discover, plan, execute, verify, diagnose."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aethos_core.provider_skills.types import (
    ProviderDiagnosis,
    ProviderDryRunEvidence,
    ProviderEvidenceBundle,
    ProviderExecutionPlan,
    ProviderExecutionResult,
    ProviderFixPlan,
    ProviderVerificationResult,
)


class ProviderSkillBase(ABC):
    provider: str
    supported_operations: list[str] = []
    readonly_tools: list[str] = []
    mutation_tools: list[str] = []
    required_credentials: list[str] = []
    common_failure_patterns: list[str] = []
    repair_recipes: list[str] = []
    verification_rules: list[str] = []

    def skill_contract(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "supported_operations": list(self.supported_operations),
            "readonly_tools": list(self.readonly_tools),
            "mutation_tools": list(self.mutation_tools),
            "required_credentials": list(self.required_credentials),
            "common_failure_patterns": list(self.common_failure_patterns),
            "repair_recipes": list(self.repair_recipes),
            "verification_rules": list(self.verification_rules),
        }

    def resolve_target(self, *, user_request: str, target_hints: list[str] | None = None) -> dict[str, Any]:
        from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory
        from aethos_core.provider_discovery.target_resolution import resolve_target_from_inventory

        inventory = get_provider_inventory(provider=self.provider)
        resolution = resolve_target_from_inventory(
            inventory=inventory,
            user_request=user_request,
            target_hints=target_hints,
        )
        return resolution.to_provider_target_dict()

    def clarify_if_ambiguous(self, *, user_request: str, target_hints: list[str] | None = None) -> dict[str, Any] | None:
        resolved = self.resolve_target(user_request=user_request, target_hints=target_hints)
        if resolved.get("resolved"):
            return None
        return {"reason": resolved.get("reason"), "candidates": resolved.get("candidates") or []}
    def discover(self, *, force: bool = False) -> dict[str, Any]:
        """Return provider inventory snapshot."""

    @abstractmethod
    def plan(
        self,
        *,
        operation: str,
        target: Any,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan: ...

    @abstractmethod
    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence: ...

    @abstractmethod
    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "provider-skill",
    ) -> ProviderExecutionResult: ...

    @abstractmethod
    def collect_evidence(
        self,
        result: ProviderExecutionResult,
        *,
        approved_at: str | None = None,
    ) -> ProviderEvidenceBundle: ...

    @abstractmethod
    def verify(
        self,
        *,
        operation: str,
        before: dict[str, Any],
        after: dict[str, Any],
        evidence_bundle: ProviderEvidenceBundle,
        approved_at: str | None = None,
        readonly_artifact: dict[str, Any] | None = None,
    ) -> ProviderVerificationResult: ...

    @abstractmethod
    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis: ...

    @abstractmethod
    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan: ...
