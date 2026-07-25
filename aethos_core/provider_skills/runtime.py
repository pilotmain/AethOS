# SPDX-License-Identifier: Apache-2.0
"""Provider skill runtime — load skills and run governed operation loops."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_evidence.store import attach_evidence_bundle
from aethos_core.provider_skills.types import ProviderEvidenceBundle, ProviderExecutionPlan


def load_provider_skill(provider: str):
    provider = (provider or "").strip().lower()
    if provider == "railway":
        from aethos_core.provider_skills.railway.skill import RailwayProviderSkill

        return RailwayProviderSkill()
    if provider == "vercel":
        from aethos_core.provider_skills.vercel.skill import VercelProviderSkill

        return VercelProviderSkill()
    if provider == "github":
        from aethos_core.provider_skills.github.skill import GitHubProviderSkill

        return GitHubProviderSkill()
    if provider == "docker":
        from aethos_core.provider_skills.docker.skill import DockerProviderSkill

        return DockerProviderSkill()
    if provider in {"kubernetes", "k8s"}:
        from aethos_core.provider_skills.kubernetes.skill import KubernetesProviderSkill

        return KubernetesProviderSkill()
    if provider == "aws":
        from aethos_core.provider_skills.aws.skill import AwsProviderSkill

        return AwsProviderSkill()
    if provider == "gcp":
        from aethos_core.provider_skills.gcp.skill import GcpProviderSkill

        return GcpProviderSkill()
    if provider == "azure":
        from aethos_core.provider_skills.azure.skill import AzureProviderSkill

        return AzureProviderSkill()
    if provider == "cloudflare":
        from aethos_core.provider_skills.cloudflare.skill import CloudflareProviderSkill

        return CloudflareProviderSkill()
    from aethos_core.execution_brain.cloud_provider_catalog import (
        FIRST_CLASS_AGENT_PROVIDERS,
        SKILL_BACKED_PROVIDERS,
        is_registered_provider,
    )

    key = (provider or "").strip().lower()
    if key in FIRST_CLASS_AGENT_PROVIDERS or key in SKILL_BACKED_PROVIDERS:
        return None
    if is_registered_provider(key):
        from aethos_core.provider_skills.cloud.skill import TokenCloudProviderSkill

        return TokenCloudProviderSkill(key)
    return None


def plan_provider_operation(
    *,
    provider: str,
    operation: str,
    target: Any,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    skill = load_provider_skill(provider)
    if skill is None:
        return {"ok": False, "error": f"No provider skill for `{provider}`."}
    plan = skill.plan(operation=operation, target=target, context=context)
    dry = skill.dry_run(plan)
    return {"ok": dry.ok, "plan": plan.to_dict(), "dry_run": dry.to_dict()}


def execute_provider_operation(
    *,
    provider: str,
    operation: str,
    target: Any,
    approved: bool,
    job_id: str | None = None,
    before_snapshot: dict[str, Any] | None = None,
    approved_at: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    skill = load_provider_skill(provider)
    if skill is None:
        return {"ok": False, "error": f"No provider skill for `{provider}`."}
    plan = skill.plan(operation=operation, target=target)
    dry = skill.dry_run(plan)
    if not dry.ok:
        return {"ok": False, "error": "; ".join(dry.issues) or "Provider dry-run failed.", "dry_run": dry.to_dict()}

    result = skill.execute(
        plan,
        approved=approved,
        before_snapshot=before_snapshot,
        approved_at=approved_at,
        request_id=request_id or job_id or "provider-skill",
    )
    bundle = skill.collect_evidence(result, approved_at=approved_at)
    verification = skill.verify(
        operation=operation,
        before=bundle.before,
        after=bundle.after,
        evidence_bundle=bundle,
        approved_at=approved_at,
    )
    bundle.verification = verification.to_dict()
    bundle_dict = bundle.to_dict()

    if result.command_submitted and not verification.verified and result.logs_after:
        diagnosis = skill.diagnose_failure(bundle)
        bundle_dict["diagnosis"] = diagnosis.to_dict()
        bundle_dict["fix_plan"] = skill.propose_fix(diagnosis, target_name=plan.target_name).to_dict()

    payload = {
        "ok": result.command_submitted,
        "command_submitted": result.command_submitted,
        "execution_mode": plan.execution_mode,
        "command": result.command,
        "execution_result": result.to_dict(),
        "evidence_bundle": bundle_dict,
        "verification": verification.to_dict(),
    }
    if job_id:
        attach_evidence_bundle(job_id=job_id, bundle=bundle_dict)
    return payload


def diagnose_provider_job(*, job_id: str) -> dict[str, Any]:
    from aethos_core.provider_evidence.store import get_evidence_bundle
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return {"ok": False, "error": "job_not_found"}
    provider = str(job.params.get("provider") or "railway")
    skill = load_provider_skill(provider)
    if skill is None:
        return {"ok": False, "error": "provider_skill_not_found"}
    evidence_resp = get_evidence_bundle(job_id=job_id)
    bundle_raw = evidence_resp.get("bundle") if evidence_resp.get("ok") else {}
    if not isinstance(bundle_raw, dict):
        bundle_raw = {}
    bundle = ProviderEvidenceBundle(
        operation=str(bundle_raw.get("operation") or job.params.get("operation_type") or "restart"),
        provider=provider,
        target=str(bundle_raw.get("target") or job.params.get("target_name") or ""),
        approved_at=bundle_raw.get("approved_at"),
        command=bundle_raw.get("command"),
        command_submitted=bool(bundle_raw.get("command_submitted")),
        execution_mode=str(bundle_raw.get("execution_mode") or "api"),
        provider_response=dict(bundle_raw.get("provider_response") or {}),
        before=dict(bundle_raw.get("before") or {}),
        after=dict(bundle_raw.get("after") or {}),
        evidence=dict(bundle_raw.get("evidence") or {}),
        verification=dict(bundle_raw.get("verification") or {}),
        logs_excerpt=list(bundle_raw.get("logs_excerpt") or []),
    )
    logs = bundle.logs_excerpt
    if not logs:
        from aethos_core.providers.railway.cli_executor import railway_logs

        if bundle.target:
            logs = list((railway_logs(service_name=bundle.target).get("logs") or [])[-50:])
            bundle.logs_excerpt = logs
    diagnosis = skill.diagnose_failure(bundle)
    fix_plan = skill.propose_fix(diagnosis, target_name=bundle.target)
    job.params["provider_diagnosis"] = diagnosis.to_dict()
    job.params["provider_fix_plan"] = fix_plan.to_dict()
    return {
        "ok": True,
        "job_id": job_id,
        "diagnosis": diagnosis.to_dict(),
        "fix_plan": fix_plan.to_dict(),
    }


def fix_plan_for_job(*, job_id: str) -> dict[str, Any]:
    diag = diagnose_provider_job(job_id=job_id)
    if not diag.get("ok"):
        return diag
    return {"ok": True, "job_id": job_id, "fix_plan": diag.get("fix_plan"), "diagnosis": diag.get("diagnosis")}
