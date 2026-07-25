# SPDX-License-Identifier: Apache-2.0
"""Docker provider skill — local CLI inventory when available."""

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


class DockerProviderSkill(ProviderSkillBase):
    provider = "docker"
    supported_operations = ["list_containers", "list_images", "inspect_container"]
    readonly_tools = ["discover", "ps", "images"]
    mutation_tools = ["restart_container"]
    required_credentials = []
    common_failure_patterns = ["docker_not_installed", "daemon_unavailable"]
    repair_recipes = []
    verification_rules = ["readonly_only"]

    def discover(self, *, force: bool = False) -> dict[str, Any]:
        _ = force
        inventory = _docker_inventory()
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
            provider="docker",
            operation=operation,
            target_name=str(target.service_name or ""),
            execution_mode="cli",
            diagnostics={"issues": []},
        )

    def dry_run(self, plan: ProviderExecutionPlan) -> ProviderDryRunEvidence:
        issues: list[str] = []
        if not shutil.which("docker"):
            issues.append("Docker CLI not found on PATH.")
        if plan.operation in self.mutation_tools:
            issues.append("Docker mutations require governed preflight.")
        return ProviderDryRunEvidence(ok=not issues, plan=plan, detail=f"Docker {plan.operation}", issues=issues)

    def execute(
        self,
        plan: ProviderExecutionPlan,
        *,
        approved: bool,
        before_snapshot: dict[str, Any] | None = None,
        approved_at: str | None = None,
        request_id: str = "docker-skill",
    ) -> ProviderExecutionResult:
        _ = before_snapshot, approved_at, request_id, approved, plan
        return ProviderExecutionResult(
            ok=False,
            command_submitted=False,
            provider="docker",
            operation=plan.operation,
            target_name=plan.target_name,
            execution_mode="cli",
            error="Docker skill is readonly.",
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
            reason="Docker readonly.",
            state="verified",
            checks=[],
        )

    def diagnose_failure(self, evidence: ProviderEvidenceBundle) -> ProviderDiagnosis:
        return ProviderDiagnosis(
            ok=False,
            category="docker",
            summary="Docker inventory issue.",
            likely_cause=str((evidence.provider_response or {}).get("error") or "unavailable"),
            log_signals=[],
            suggested_operation="discover",
            requires_approval=False,
        )

    def propose_fix(self, diagnosis: ProviderDiagnosis, *, target_name: str) -> ProviderFixPlan:
        _ = diagnosis, target_name
        return ProviderFixPlan(
            ok=True,
            summary="Install Docker and ensure the daemon is running.",
            proposed_operation="discover",
            proposed_changes=[],
            requires_approval=False,
            preflight_required=False,
        )


def _docker_inventory() -> dict[str, Any]:
    if not shutil.which("docker"):
        return {"ok": False, "error": "Docker CLI not found.", "provider": "docker"}
    try:
        ps = subprocess.run(["docker", "ps", "--format", "{{json .}}"], capture_output=True, text=True, timeout=20, check=False)
        images = subprocess.run(["docker", "images", "--format", "{{json .}}"], capture_output=True, text=True, timeout=20, check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"ok": False, "error": str(exc), "provider": "docker"}
    containers = [_parse_json_line(line) for line in (ps.stdout or "").splitlines() if line.strip()]
    image_rows = [_parse_json_line(line) for line in (images.stdout or "").splitlines() if line.strip()]
    return {
        "ok": ps.returncode == 0 or images.returncode == 0,
        "provider": "docker",
        "container_count": len(containers),
        "containers": containers[:20],
        "image_count": len(image_rows),
        "images": image_rows[:20],
        "error": (ps.stderr or images.stderr or "").strip()[:200] or None,
    }


def _parse_json_line(line: str) -> dict[str, Any]:
    try:
        row = json.loads(line)
        return row if isinstance(row, dict) else {"raw": line}
    except json.JSONDecodeError:
        return {"raw": line}
