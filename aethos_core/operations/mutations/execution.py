# SPDX-License-Identifier: Apache-2.0
"""Mutation execution — governed real execution when approved."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.config import get_settings
from aethos_core.operations.mutations.audit import build_audit_stub, finalize_audit_record
from aethos_core.operations.mutations.lifecycle import (
    EXECUTION_FAILED,
    EXECUTION_MUTATION_REQUESTED,
    EXECUTION_STABILIZING,
    LIFECYCLE_VERIFICATION_RUNNING,
    execution_state_after_provider_response,
    lifecycle_after_provider_response,
    verification_state_after_enqueue,
)
from aethos_core.operations.mutations.lifecycle_authority import sync_mutation_job_lifecycle
from aethos_core.operations.mutations.risk import MutationRiskTier, classify_mutation_risk, execution_allowed_for_tier
from aethos_core.operations.mutations.secrets import redact_secrets_in_text
from aethos_core.operations.mutations.verification import enqueue_mutation_verification
from aethos_core.providers.base.provider_registry import ProviderRegistry


@dataclass
class MutationExecutionOutcome:
    summary: str
    full_result: str
    dry_run: bool
    blocked: bool
    executed: bool
    artifact: dict[str, Any]


def run_mutation_execution_dry_run(*, params: dict[str, Any]) -> MutationExecutionOutcome:
    provider = str(params.get("provider") or "unknown")
    operation_type = str(params.get("operation_type") or "unknown")
    target = str(params.get("target_name") or "(none)")
    tier = classify_mutation_risk(operation_type=operation_type, provider=provider)
    allowed = execution_allowed_for_tier(tier)

    artifact = {
        "provider": provider,
        "operation_type": operation_type,
        "target_name": target,
        "risk_tier": tier.value,
        "dry_run": True,
        "mutating": False,
        "executed": False,
        "reason": "mutation_execution_not_enabled",
    }

    if not allowed:
        full = (
            f"# Mutation execution blocked\n\n"
            f"Tier `{tier.value}` is not enabled for real execution.\n"
            f"No mutation was performed on `{target}`."
        )
        return MutationExecutionOutcome(
            summary="Mutation execution blocked — design-only phase.",
            full_result=full,
            dry_run=True,
            blocked=True,
            executed=False,
            artifact=artifact,
        )

    full = (
        f"# Mutation execution dry-run\n\n"
        f"Would execute `{operation_type}` on `{target}` ({provider}) — **no provider mutation performed**."
    )
    return MutationExecutionOutcome(
        summary="Mutation dry-run complete — no provider mutation performed.",
        full_result=full,
        dry_run=True,
        blocked=False,
        executed=False,
        artifact=artifact,
    )


def run_mutation_execution(*, params: dict[str, Any], job_id: str | None = None) -> MutationExecutionOutcome:
    if not params.get("mutation_execution_approved"):
        return run_mutation_execution_dry_run(params=params)

    settings = get_settings()
    if not settings.mutation_execution_enabled:
        return run_mutation_execution_dry_run(params=params)

    provider = str(params.get("provider") or "unknown")
    operation_type = str(params.get("operation_type") or "unknown")
    target = str(params.get("target_name") or "(none)")

    if operation_type == "set_env_var" and not settings.provider_env_var_mutations_enabled:
        artifact = {"executed": False, "reason": "env_var_writes_not_enabled", "provider": provider}
        return MutationExecutionOutcome(
            summary="Environment variable writes remain blocked.",
            full_result=(
                "# Mutation execution blocked\n\n"
                "Env var writes require `PROVIDER_ENV_VAR_MUTATIONS_ENABLED=true`."
            ),
            dry_run=False,
            blocked=True,
            executed=False,
            artifact=artifact,
        )

    tier_value = str(params.get("risk_tier") or "")
    try:
        tier = MutationRiskTier(tier_value) if tier_value else classify_mutation_risk(
            operation_type=operation_type, provider=provider
        )
    except ValueError:
        tier = classify_mutation_risk(operation_type=operation_type, provider=provider)

    if tier == MutationRiskTier.T3_PRODUCTION and not settings.mutation_t3_production_enabled:
        artifact = {"executed": False, "reason": "t3_production_not_enabled", "provider": provider}
        return MutationExecutionOutcome(
            summary="Production mutation blocked — T3 not enabled.",
            full_result="# Mutation execution blocked\n\nProduction-impacting mutations require explicit T3 enablement.",
            dry_run=False,
            blocked=True,
            executed=False,
            artifact=artifact,
        )

    if not execution_allowed_for_tier(tier):
        return run_mutation_execution_dry_run(params=params)

    spec = ProviderRegistry.get(provider)
    adapter = spec.mutation_adapter if spec else None
    if not adapter or not adapter.enabled:
        artifact = {"executed": False, "reason": "mutation_adapter_disabled", "provider": provider}
        return MutationExecutionOutcome(
            summary=f"Mutation adapter disabled for {provider}.",
            full_result=f"# Mutation execution blocked\n\nProvider `{provider}` mutations are not enabled.",
            dry_run=False,
            blocked=True,
            executed=False,
            artifact=artifact,
        )

    if operation_type not in adapter.supported_mutations():
        artifact = {"executed": False, "reason": "unsupported_mutation", "operation_type": operation_type}
        return MutationExecutionOutcome(
            summary=f"Unsupported mutation `{operation_type}`.",
            full_result=f"# Mutation execution blocked\n\nOperation `{operation_type}` is not supported yet.",
            dry_run=False,
            blocked=True,
            executed=False,
            artifact=artifact,
        )

    try:
        result = adapter.execute(operation=operation_type, params=params)
    except Exception as exc:
        msg = redact_secrets_in_text(str(exc))
        artifact = {
            "provider": provider,
            "operation_type": operation_type,
            "target_name": target,
            "executed": False,
            "mutating": False,
            "error": msg,
        }
        return MutationExecutionOutcome(
            summary=f"Mutation failed: {msg[:120]}",
            full_result=f"# Mutation execution failed\n\n{msg}",
            dry_run=False,
            blocked=False,
            executed=False,
            artifact=artifact,
        )

    executed = bool(result.get("ok"))
    if executed:
        # Provider state changed — drop any cached readonly reads so the next
        # "show projects / health / logs" reflects the mutation immediately (§C4).
        try:
            from aethos_core.execution_brain.provider_connection_cache import cache_invalidate

            cache_invalidate(provider)
        except Exception:
            pass
    exec_state = execution_state_after_provider_response(provider_accepted=executed, result=result)
    lifecycle_state = lifecycle_after_provider_response(provider_accepted=executed)
    ver_state = verification_state_after_enqueue() if executed else None
    artifact = {
        "provider": provider,
        "operation_type": operation_type,
        "target_name": target,
        "risk_tier": tier.value,
        "dry_run": False,
        "mutating": executed,
        "executed": executed,
        "provider_mutation_requested": executed,
        "verified": False,
        "execution_state": exec_state,
        "verification_state": ver_state,
        "lifecycle_state": lifecycle_state,
        "provider_result": result,
        "rollback_plan": params.get("rollback_plan"),
        "blast_radius": params.get("blast_radius"),
    }
    railway_result = result.get("railway_mutation_result")
    if isinstance(railway_result, dict):
        artifact["railway_mutation_result"] = railway_result
    if executed and isinstance(result.get("rollback_metadata"), dict):
        artifact["rollback_metadata"] = result["rollback_metadata"]
    if params.get("railway_before_snapshot"):
        artifact["railway_before_snapshot"] = params["railway_before_snapshot"]
    if params.get("mutation_execution_approved_at_iso"):
        artifact["mutation_execution_approved_at_iso"] = params["mutation_execution_approved_at_iso"]
    if isinstance(result.get("provider_evidence_bundle"), dict):
        artifact["provider_evidence_bundle"] = result["provider_evidence_bundle"]
    if result.get("command"):
        artifact["command"] = result["command"]
    if result.get("execution_mode"):
        artifact["execution_mode"] = result["execution_mode"]
    if not executed:
        fc = result.get("failure_classification") or result.get("failure_type")
        if fc:
            artifact["failure_type"] = fc
            artifact["failure_classification"] = fc
    if isinstance(result.get("evidence"), dict):
        artifact["provider_evidence"] = result["evidence"]
    if provider == "railway" and isinstance(result, dict):
        artifact["railway_execution_proof"] = {
            "provider": provider,
            "operation": operation_type,
            "executed": executed,
            "restart_command_submitted": bool(result.get("restart_command_submitted")),
            "command": result.get("command"),
            "execution_mode": result.get("execution_mode"),
            "graphql_operation": result.get("graphql_operation"),
            "http_status": result.get("http_status"),
            "railway_response": result.get("railway_response"),
            "restart_requested_at": result.get("restart_requested_at"),
            "deployment_or_restart_id": result.get("deployment_or_restart_id"),
            "environment_id": result.get("environment_id"),
            "project_id": result.get("project_id"),
            "mutation_diagnostics": result.get("mutation_diagnostics"),
            "post_mutation_verification_job": artifact.get("verification_job_id"),
        }
    audit = finalize_audit_record(
        build_audit_stub(
            request=str(params.get("user_request") or ""),
            provider=provider,
            operation_type=operation_type,
            target_name=params.get("target_name"),
            risk_tier=tier.value,
            result="provider_mutation_requested" if executed else "failed",
        ),
        execution_artifact=artifact,
        job_id=job_id,
    )
    artifact["audit"] = audit
    try:  # §8 SLO signal — mutation success rate.
        from aethos_core.observability.telemetry import record_mutation_result

        record_mutation_result(executed)
    except Exception:  # noqa: BLE001
        pass
    try:  # §3 unified audit ledger — central mutation-execute record (best-effort).
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(
            action="mutation.execute",
            target=f"{provider}:{operation_type}:{target}",
            outcome="ok" if executed else "failed",
            ref=job_id,
            before={"risk_tier": tier.value, "request": str(params.get("user_request") or "")[:240]},
            after={"executed": executed, "execution_state": exec_state},
        )
    except Exception:  # noqa: BLE001
        pass

    verification_job = None
    if executed and job_id:
        from aethos_core.runtime.jobs import job_store

        mutation_job = job_store.get(job_id)
        if mutation_job:
            verification_job = enqueue_mutation_verification(
                mutation_job=mutation_job,
                execution_artifact=artifact,
            )
            if verification_job:
                artifact["verification_job_id"] = verification_job.id
                artifact["verification_state"] = verification_state_after_enqueue()
                artifact["lifecycle_state"] = LIFECYCLE_VERIFICATION_RUNNING
                artifact["execution_state"] = EXECUTION_STABILIZING if executed else EXECUTION_FAILED

    lines = [
        "# Mutation execution",
        "",
        f"**Provider:** {provider}",
        f"**Operation:** {operation_type.replace('_', ' ')}",
        f"**Target:** {target}",
        f"**Provider mutation requested:** {'yes' if executed else 'no'}",
        f"**Execution state:** {exec_state}",
        "",
    ]
    if executed:
        lines.append("**Status:** provider accepted the mutation request — verification is monitoring recovery.")
    else:
        lines.append("**Status:** provider mutation did not execute.")
    if result.get("detail"):
        lines.append(f"**Detail:** {redact_secrets_in_text(str(result['detail']))}")
    if verification_job:
        lines.extend(["", f"**Verification job:** `{verification_job.id}`"])

    from aethos_core.operations.mutations.lifecycle_authority import canonical_mutation_state, mutation_summary

    canonical_state = canonical_mutation_state(artifact)
    artifact["canonical_lifecycle_state"] = canonical_state
    summary = mutation_summary(
        provider=provider,
        operation_type=operation_type,
        target=target,
        canonical_state=canonical_state,
        failure_classification=str(result.get("failure_classification") or result.get("failure_type") or "") or None,
    )
    artifact["lifecycle_summary"] = summary
    if params.get("rollback_plan"):
        rp = params["rollback_plan"]
        if isinstance(rp, dict):
            lines.extend(
                [
                    "",
                    "**Rollback plan:**",
                    f"- Strategy: {rp.get('strategy')}",
                    f"- Verification: {rp.get('verification')}",
                ]
            )
    lines.extend(["", f"**Lifecycle:** {summary}"])
    return MutationExecutionOutcome(
        summary=summary,
        full_result="\n".join(lines),
        dry_run=False,
        blocked=not executed,
        executed=executed,
        artifact=artifact,
    )
