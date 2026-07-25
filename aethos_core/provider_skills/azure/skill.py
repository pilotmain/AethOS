# SPDX-License-Identifier: Apache-2.0
"""Azure provider skill — readonly inventory via Azure CLI when available."""

from __future__ import annotations

import json
import os
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


class AzureProviderSkill(ProviderSkillBase):
    provider = "azure"
    supported_operations = ["list_resource_groups", "list_webapps", "list_containers"]
    readonly_tools = ["discover", "az_inventory"]
    mutation_tools = []
    required_credentials = ["AZURE_SUBSCRIPTION_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]
    common_failure_patterns = ["az_not_installed", "login_required"]
    repair_recipes = []
    verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        inventory = _azure_inventory()
        return {"ok": inventory.get("ok", False), "inventory": inventory, "error": inventory.get("error")}

    def plan(self, *, operation: str, target: ProviderTarget, context: dict[str, Any] | None = None) -> ProviderExecutionPlan:
        _ = context
        return ProviderExecutionPlan(provider="azure", operation=operation, target_name=str(target.project_name or ""), execution_mode="cli", diagnostics={"issues": []})

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues = [] if shutil.which("az") else ["Azure CLI (`az`) not found on PATH."]
        return ProviderDryRunEvidence(ok=not issues, plan=plan, detail=f"Azure {plan.operation}", issues=issues)

    def execute(self, plan: ProviderExecutionPlan, *, approved: bool, before_snapshot: dict[str, Any] | None = None, approved_at: str | None = None, request_id: str = "azure-skill") -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id, approved, plan
        return ProviderExecutionResult(ok=False, command_submitted=False, provider="azure", operation=plan.operation, target_name=plan.target_name, execution_mode="cli", error="Azure skill is readonly.")

    def collect_evidence(self, result: ProviderExecutionResult, *, approved_at: str | None = None) -> ProviderEvidenceBundle:
        return ProviderEvidenceBundle(operation=result.operation, provider=result.provider, target=result.target_name, approved_at=approved_at, command=result.command, command_submitted=result.command_submitted, execution_mode=result.execution_mode, provider_response=result.provider_response, evidence={"readonly": True})

    def verify(self, *, operation: str, before: dict[str, Any], after: dict[str, Any], evidence_bundle: ProviderEvidenceBundle, approved_at: str | None = None, readonly_artifact: dict[str, Any] | None = None) -> ProviderVerificationResult:
        _ = operation, before, after, evidence_bundle, approved_at, readonly_artifact
        return ProviderVerificationResult(status="verified", verified=True, confidence="bounded", reason="Azure readonly.", state="verified", checks=[])

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(ok=False, category="azure", summary="Azure inventory issue.", likely_cause=str((evidence.provider_response or {}).get("error") or "unavailable"), log_signals=[], suggested_operation="discover", requires_approval=False)

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis, target_name
        return ProviderFixPlan(ok=True, summary="Run `az login` and set AZURE_* service principal credentials.", proposed_operation="discover", proposed_changes=[], requires_approval=False, preflight_required=False)


def _azure_inventory() -> dict[str, Any]:
    az = shutil.which("az")
    if not az:
        return {"ok": False, "error": "Azure CLI not found.", "provider": "azure"}
    env = dict(os.environ)
    from aethos_core.config import get_settings

    settings = get_settings()
    if settings.azure_subscription_id:
        env["AZURE_SUBSCRIPTION_ID"] = settings.azure_subscription_id
    try:
        groups_proc = subprocess.run([az, "group", "list", "-o", "json"], capture_output=True, text=True, timeout=30, check=False, env=env)
        apps_proc = subprocess.run([az, "webapp", "list", "-o", "json"], capture_output=True, text=True, timeout=30, check=False, env=env)
        groups = json.loads(groups_proc.stdout or "[]") if groups_proc.returncode == 0 else []
        apps = json.loads(apps_proc.stdout or "[]") if apps_proc.returncode == 0 else []
        return {
            "ok": groups_proc.returncode == 0 or apps_proc.returncode == 0,
            "provider": "azure",
            "resource_group_count": len(groups) if isinstance(groups, list) else 0,
            "resource_groups": groups[:15] if isinstance(groups, list) else [],
            "webapp_count": len(apps) if isinstance(apps, list) else 0,
            "webapps": apps[:15] if isinstance(apps, list) else [],
            "error": (groups_proc.stderr or apps_proc.stderr or "")[:200] or None,
        }
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "provider": "azure"}
