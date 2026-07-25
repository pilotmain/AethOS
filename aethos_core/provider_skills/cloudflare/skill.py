# SPDX-License-Identifier: Apache-2.0
"""Cloudflare provider skill — readonly zone inventory when API token is configured."""

from __future__ import annotations

import os
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


class CloudflareProviderSkill(ProviderSkillBase):
    provider = "cloudflare"
    supported_operations = ["list_zones", "list_dns_records"]
    readonly_tools = ["discover", "zones_inventory"]
    mutation_tools = []
    required_credentials = ["CLOUDFLARE_API_TOKEN"]
    common_failure_patterns = ["credentials_missing"]
    repair_recipes = []
    verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        inventory = _cloudflare_inventory()
        return {"ok": inventory.get("ok", False), "inventory": inventory, "error": inventory.get("error")}

    def plan(self, *, operation: str, target: ProviderTarget, context: dict[str, Any] | None = None) -> ProviderExecutionPlan:
        _ = context
        return ProviderExecutionPlan(provider="cloudflare", operation=operation, target_name=str(target.project_name or ""), execution_mode="api", diagnostics={"issues": []})

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        token = _resolve_token()
        issues = [] if token else ["CLOUDFLARE_API_TOKEN not configured."]
        return ProviderDryRunEvidence(ok=not issues, plan=plan, detail=f"Cloudflare {plan.operation}", issues=issues)

    def execute(self, plan: ProviderExecutionPlan, *, approved: bool, before_snapshot: dict[str, Any] | None = None, approved_at: str | None = None, request_id: str = "cloudflare-skill") -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id, approved, plan
        return ProviderExecutionResult(ok=False, command_submitted=False, provider="cloudflare", operation=plan.operation, target_name=plan.target_name, execution_mode="api", error="Cloudflare skill is readonly.")

    def collect_evidence(self, result: ProviderExecutionResult, *, approved_at: str | None = None) -> ProviderEvidenceBundle:
        return ProviderEvidenceBundle(operation=result.operation, provider=result.provider, target=result.target_name, approved_at=approved_at, command=result.command, command_submitted=result.command_submitted, execution_mode=result.execution_mode, provider_response=result.provider_response, evidence={"readonly": True})

    def verify(self, *, operation: str, before: dict[str, Any], after: dict[str, Any], evidence_bundle: ProviderEvidenceBundle, approved_at: str | None = None, readonly_artifact: dict[str, Any] | None = None) -> ProviderVerificationResult:
        _ = operation, before, after, evidence_bundle, approved_at, readonly_artifact
        return ProviderVerificationResult(status="verified", verified=True, confidence="bounded", reason="Cloudflare readonly.", state="verified", checks=[])

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(ok=False, category="cloudflare", summary="Cloudflare inventory issue.", likely_cause=str((evidence.provider_response or {}).get("error") or "unavailable"), log_signals=[], suggested_operation="discover", requires_approval=False)

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis, target_name
        return ProviderFixPlan(ok=True, summary="Set CLOUDFLARE_API_TOKEN with Zone:Read scope.", proposed_operation="discover", proposed_changes=[], requires_approval=False, preflight_required=False)


def _resolve_token() -> str:
    from aethos_core.config import get_settings

    settings = get_settings()
    return str(getattr(settings, "cloudflare_api_token", "") or os.environ.get("CLOUDFLARE_API_TOKEN") or "").strip()


def _cloudflare_inventory() -> dict[str, Any]:
    token = _resolve_token()
    if not token:
        return {"ok": False, "error": "CLOUDFLARE_API_TOKEN not configured.", "provider": "cloudflare", "zones": []}
    try:
        import httpx

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        with httpx.Client(timeout=20.0) as client:
            response = client.get("https://api.cloudflare.com/client/v4/zones?per_page=20", headers=headers)
        if response.status_code >= 400:
            return {"ok": False, "error": f"Cloudflare API HTTP {response.status_code}", "provider": "cloudflare", "zones": []}
        payload = response.json()
        zones = payload.get("result") if isinstance(payload, dict) else []
        names = [str(row.get("name") or "") for row in zones if isinstance(row, dict) and row.get("name")]
        return {"ok": True, "provider": "cloudflare", "zone_count": len(names), "zones": names[:20]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:240], "provider": "cloudflare", "zones": []}
