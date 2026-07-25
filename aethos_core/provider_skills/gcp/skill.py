# SPDX-License-Identifier: Apache-2.0
"""GCP provider skill — readonly inventory via gcloud or Application Default Credentials."""

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


class GcpProviderSkill(ProviderSkillBase):
    provider = "gcp"
    supported_operations = ["list_projects", "list_compute_instances", "list_cloud_run_services"]
    readonly_tools = ["discover", "gcloud_inventory"]
    mutation_tools = []
    required_credentials = ["GOOGLE_APPLICATION_CREDENTIALS", "GCP_PROJECT_ID"]
    common_failure_patterns = ["credentials_missing", "gcloud_not_installed"]
    repair_recipes = []
    verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        inventory = _gcp_inventory()
        return {"ok": inventory.get("ok", False), "inventory": inventory, "error": inventory.get("error")}

    def plan(self, *, operation: str, target: ProviderTarget, context: dict[str, Any] | None = None) -> ProviderExecutionPlan:
        _ = context
        return ProviderExecutionPlan(provider="gcp", operation=operation, target_name=str(target.project_name or ""), execution_mode="api", diagnostics={"issues": []})

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        creds_ok = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or shutil.which("gcloud"))
        issues = [] if creds_ok else ["GCP credentials or gcloud CLI required."]
        return ProviderDryRunEvidence(ok=not issues, plan=plan, detail=f"GCP {plan.operation}", issues=issues)

    def execute(self, plan: ProviderExecutionPlan, *, approved: bool, before_snapshot: dict[str, Any] | None = None, approved_at: str | None = None, request_id: str = "gcp-skill") -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id, approved, plan
        return ProviderExecutionResult(ok=False, command_submitted=False, provider="gcp", operation=plan.operation, target_name=plan.target_name, execution_mode="api", error="GCP skill is readonly.")

    def collect_evidence(self, result: ProviderExecutionResult, *, approved_at: str | None = None) -> ProviderEvidenceBundle:
        return ProviderEvidenceBundle(operation=result.operation, provider=result.provider, target=result.target_name, approved_at=approved_at, command=result.command, command_submitted=result.command_submitted, execution_mode=result.execution_mode, provider_response=result.provider_response, evidence={"readonly": True})

    def verify(self, *, operation: str, before: dict[str, Any], after: dict[str, Any], evidence_bundle: ProviderEvidenceBundle, approved_at: str | None = None, readonly_artifact: dict[str, Any] | None = None) -> ProviderVerificationResult:
        _ = operation, before, after, evidence_bundle, approved_at, readonly_artifact
        return ProviderVerificationResult(status="verified", verified=True, confidence="bounded", reason="GCP readonly.", state="verified", checks=[])

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(ok=False, category="gcp", summary="GCP inventory issue.", likely_cause=str((evidence.provider_response or {}).get("error") or "unavailable"), log_signals=[], suggested_operation="discover", requires_approval=False)

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis, target_name
        return ProviderFixPlan(ok=True, summary="Configure GOOGLE_APPLICATION_CREDENTIALS or install gcloud.", proposed_operation="discover", proposed_changes=[], requires_approval=False, preflight_required=False)


def _gcp_inventory() -> dict[str, Any]:
    from aethos_core.config import get_settings

    project_id = str(get_settings().gcp_project_id or os.environ.get("GCP_PROJECT_ID") or "").strip()
    gcloud = shutil.which("gcloud")
    if not gcloud:
        return {"ok": False, "error": "gcloud CLI not found.", "provider": "gcp"}
    try:
        projects_proc = subprocess.run([gcloud, "projects", "list", "--format=json"], capture_output=True, text=True, timeout=30, check=False)
        projects = json.loads(projects_proc.stdout or "[]") if projects_proc.returncode == 0 else []
        instances: list[dict[str, Any]] = []
        if project_id:
            inst_proc = subprocess.run(
                [gcloud, "compute", "instances", "list", "--project", project_id, "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if inst_proc.returncode == 0:
                instances = json.loads(inst_proc.stdout or "[]")[:20]
        return {
            "ok": projects_proc.returncode == 0,
            "provider": "gcp",
            "project_id": project_id or None,
            "project_count": len(projects) if isinstance(projects, list) else 0,
            "projects": projects[:15] if isinstance(projects, list) else [],
            "compute_instances": instances,
            "error": (projects_proc.stderr or "")[:200] or None,
        }
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "provider": "gcp"}
