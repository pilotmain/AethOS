# SPDX-License-Identifier: Apache-2.0
"""Kubernetes provider skill — kubectl inventory when available."""

from __future__ import annotations

import json
import shutil
import subprocess
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


class KubernetesProviderSkill(ProviderSkillBase):
    provider = "kubernetes"
    supported_operations = ["list_pods", "list_services", "list_deployments"]
    readonly_tools = ["discover", "get_pods", "get_services"]
    mutation_tools = ["rollout_restart"]
    required_credentials = []
    common_failure_patterns = ["kubectl_not_installed", "cluster_unreachable"]
    repair_recipes = []
    verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        inventory = _kubectl_inventory()
        return {"ok": inventory.get("ok", False), "inventory": inventory, "error": inventory.get("error")}

    def plan(
        self,
        *,
        operation: str,
        target: ProviderTarget,
        context: dict[str, Any] | None = None,
    ) -> ProviderExecutionPlan:
        _ = context
        return ProviderExecutionPlan(
            provider="kubernetes",
            operation=operation,
            target_name=str(target.service_name or ""),
            execution_mode="cli",
            diagnostics={"issues": []},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues: list[str] = []
        if not shutil.which("kubectl"):
            issues.append("kubectl not found on PATH.")
        if plan.operation in self.mutation_tools:
            issues.append("Kubernetes mutations require governed preflight.")
        return ProviderDryRunEvidence(ok=not issues, plan=plan, detail=f"Kubernetes {plan.operation}", issues=issues)

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "k8s-skill",
    ) -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id, approved, plan
        return ProviderExecutionResult(
            ok=False,
            command_submitted=False,
            provider="kubernetes",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="cli",
            error="Kubernetes skill is readonly.",
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
        _ = operation, before, after, evidence_bundle, approved_at, readonly_artifact
        return ProviderVerificationResult(
            status="verified",
            verified=True,
            confidence="bounded",
            reason="Kubernetes readonly.",
            state="verified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(
            ok=False,
            category="kubernetes",
            summary="Kubernetes inventory issue.",
            likely_cause=str((evidence.provider_response or {}).get("error") or "unavailable"),
            log_signals=[],
            suggested_operation="discover",
            requires_approval=False,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis, target_name
        return ProviderFixPlan(
            ok=True,
            summary="Install kubectl and configure cluster context.",
            proposed_operation="discover",
            proposed_changes=[],
            requires_approval=False,
            preflight_required=False,
        )


def _kubectl_inventory() -> dict[str, Any]:
    kubectl = shutil.which("kubectl")
    if not kubectl:
        return {"ok": False, "error": "kubectl not found.", "provider": "kubernetes"}

    def _get(resource: str) -> list[dict[str, Any]]:
        try:
            proc = subprocess.run(
                [kubectl, "get", resource, "-A", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=25,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return [{"error": str(exc)}]
        if proc.returncode != 0:
            return [{"error": (proc.stderr or proc.stdout or "")[:200]}]
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            return []
        items = payload.get("items") if isinstance(payload, dict) else []
        rows: list[dict[str, Any]] = []
        for item in items[:20] if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            rows.append({"name": meta.get("name"), "namespace": meta.get("namespace")})
        return rows

    pods = _get("pods")
    services = _get("services")
    deployments = _get("deployments")
    ok = not any(isinstance(row, dict) and row.get("error") for row in pods + services + deployments)
    return {
        "ok": ok,
        "provider": "kubernetes",
        "pods": pods,
        "services": services,
        "deployments": deployments,
    }
