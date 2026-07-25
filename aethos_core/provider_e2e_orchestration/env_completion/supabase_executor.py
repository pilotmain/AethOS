# SPDX-License-Identifier: Apache-2.0
"""Run approved Supabase env completion — browser/vault → Vercel env → redeploy → verify."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.provider_e2e_orchestration.deployment_polling import poll_deployment_status
from aethos_core.provider_e2e_orchestration.env_completion.supabase_approval import (
    validate_supabase_env_completion_gate,
)
from aethos_core.provider_e2e_orchestration.env_completion.supabase_browser_phase import (
    collect_supabase_values_from_sources,
)
from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
    SUPABASE_ENV_VAR_NAMES,
)
from aethos_core.provider_e2e_orchestration.env_var_execution import apply_env_vars
from aethos_core.provider_e2e_orchestration.evidence_bundle import build_provider_e2e_evidence_bundle
from aethos_core.provider_e2e_orchestration.final_report import (
    build_final_report_payload,
    compose_provider_e2e_final_report,
)
from aethos_core.provider_e2e_orchestration.health_verification import verify_health
from aethos_core.provider_e2e_orchestration.job_model import build_provider_e2e_job_model
from aethos_core.provider_e2e_orchestration.redeploy_execution import execute_redeploy
from aethos_core.providers.railway.env_value_readiness.deployment_env_store import register_deployment_env_values
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import build_target_key_for_plan
from aethos_core.security.secret_redaction import redact_text


@dataclass
class SupabaseEnvCompletionOutcome:
    summary: str
    full_result: str
    executed: bool
    blocked: bool
    artifact: dict[str, Any]


def run_supabase_env_completion(*, job_id: str, params: dict[str, Any]) -> SupabaseEnvCompletionOutcome:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    gate = validate_supabase_env_completion_gate(job, for_execution=True)
    if not gate.ok:
        body = _blocked_report(gate.failure_state or "blocked", gate.detail, gate.report or {})
        return SupabaseEnvCompletionOutcome(
            summary=gate.detail or "Supabase env completion blocked.",
            full_result=body,
            executed=False,
            blocked=True,
            artifact={
                "execution_status": "blocked",
                "failure_state": gate.failure_state,
                "approval_gate_report": gate.report or {},
            },
        )

    params = dict(params)
    params["execution_status"] = "running"
    chat_session_id = str(params.get("session_id") or "default")
    plan = _plan_from_params(params)
    target_key = build_target_key_for_plan(plan)
    missing_names = list(params.get("missing_env_names") or SUPABASE_ENV_VAR_NAMES)

    collected, collection_trace = collect_supabase_values_from_sources(
        plan=plan,
        params=params,
        chat_session_id=chat_session_id,
    )
    still_missing = [n for n in missing_names if n not in collected]
    if still_missing:
        return _finish(
            job_id=job_id,
            params=params,
            execution_status="collection_failed",
            store_report={
                "ok": False,
                "registered_names": [],
                "detail": f"Missing Supabase values for: {', '.join(still_missing)}",
                "collection_trace": collection_trace,
            },
            env_report={"ok": False, "skipped": True, "failed_names": still_missing},
            redeploy_report={"ok": False, "skipped": True},
            poll_report={"ok": False, "final_state": "failed", "timeline": []},
            health_report={"ok": False, "detail": "Skipped"},
        )

    registered = register_deployment_env_values(target_key=target_key, values=collected)
    store_report = {
        "ok": True,
        "registered_names": registered,
        "target_key": target_key,
        "detail": f"Registered {len(registered)} Supabase env name(s) in secure deployment store.",
        "collection_trace": collection_trace,
    }

    model = build_provider_e2e_job_model(params)
    model.env_var_names = list(dict.fromkeys([*model.env_var_names, *registered]))
    env_report = apply_env_vars(model, params=params, mutation_execution_approved=True)
    if not env_report.get("ok") and not env_report.get("skipped"):
        return _finish(
            job_id=job_id,
            params=params,
            execution_status="env_failed",
            store_report=store_report,
            env_report=env_report,
            redeploy_report={"ok": False, "skipped": True, "detail": "Skipped — env step failed."},
            poll_report={"ok": False, "final_state": "failed", "timeline": []},
            health_report={"ok": False, "detail": "Skipped"},
        )

    redeploy_report = execute_redeploy(model, params=params)
    if not redeploy_report.get("ok"):
        return _finish(
            job_id=job_id,
            params=params,
            execution_status="redeploy_failed",
            store_report=store_report,
            env_report=env_report,
            redeploy_report=redeploy_report,
            poll_report={"ok": False, "final_state": "failed", "timeline": []},
            health_report={"ok": False, "detail": "Skipped"},
        )

    poll_report = poll_deployment_status(
        model,
        deployment_id=str(redeploy_report.get("deployment_id") or ""),
        params=params,
    )
    if not poll_report.get("ok"):
        return _finish(
            job_id=job_id,
            params=params,
            execution_status="polling_failed" if poll_report.get("final_state") == "timed_out" else "failed",
            store_report=store_report,
            env_report=env_report,
            redeploy_report=redeploy_report,
            poll_report=poll_report,
            health_report={"ok": False, "detail": "Skipped"},
        )

    health_report = verify_health(
        model,
        deployment_url=str(poll_report.get("deployment_url") or ""),
        poll_report=poll_report,
    )
    execution_status = "completed" if health_report.get("ok") else "verification_failed"
    return _finish(
        job_id=job_id,
        params=params,
        execution_status=execution_status,
        store_report=store_report,
        env_report=env_report,
        redeploy_report=redeploy_report,
        poll_report=poll_report,
        health_report=health_report,
    )


def _plan_from_params(params: dict[str, Any]) -> dict[str, Any]:
    target = params.get("target") if isinstance(params.get("target"), dict) else {}
    return {
        "repo": str(params.get("referenced_github_repo") or ""),
        "project": str(params.get("project_name") or target.get("project_name") or ""),
        "environment": str(params.get("environment") or "production"),
        "service_name": str(params.get("service_name") or ""),
        "provider": "vercel",
    }


def _blocked_report(failure_state: str, detail: str, report: dict[str, Any]) -> str:
    lines = [
        "## Supabase env completion blocked",
        "",
        detail or failure_state,
        "",
        f"Failure state: `{failure_state}`",
    ]
    if report:
        lines.extend(["", "### Gate report", f"- Project: `{report.get('project_name') or 'unknown'}`"])
    return "\n".join(lines)


def _finish(
    *,
    job_id: str,
    params: dict[str, Any],
    execution_status: str,
    store_report: dict[str, Any],
    env_report: dict[str, Any],
    redeploy_report: dict[str, Any],
    poll_report: dict[str, Any],
    health_report: dict[str, Any],
) -> SupabaseEnvCompletionOutcome:
    from aethos_core.runtime.jobs import job_store

    params = dict(params)
    params["execution_status"] = execution_status
    model = build_provider_e2e_job_model(params)
    evidence = build_provider_e2e_evidence_bundle(
        preflight_job_id=job_id,
        approval_id=str(params.get("approval_id") or ""),
        provider=model.provider,
        env_report=env_report,
        redeploy_report=redeploy_report,
        poll_report=poll_report,
        health_report=health_report,
        model_snapshot=model.to_dict(),
    )
    evidence["store_report"] = store_report
    evidence["flow"] = "supabase_env_completion"
    full_report = compose_provider_e2e_final_report(
        provider=model.provider,
        evidence=evidence,
        execution_status=execution_status,
    )
    payload = build_final_report_payload(
        full_report=full_report,
        evidence=evidence,
        execution_status=execution_status,
    )
    summary = _summary_for_status(execution_status, store_report, env_report, poll_report)
    artifact = {
        "execution_status": execution_status,
        "store_report": store_report,
        "env_var_execution_report": env_report,
        "redeploy_execution_report": redeploy_report,
        "deployment_polling_report": poll_report,
        "health_verification_report": health_report,
        "provider_e2e_evidence_bundle": evidence,
        "provider_e2e_final_report": payload,
        "flow": "supabase_env_completion",
        "mutating": execution_status == "completed",
        "executed": execution_status == "completed",
    }
    job = job_store.get(job_id)
    if job:
        job.params.update(artifact)
    return SupabaseEnvCompletionOutcome(
        summary=redact_text(summary),
        full_result=redact_text(full_report),
        executed=execution_status == "completed",
        blocked=execution_status == "blocked",
        artifact=artifact,
    )


def _summary_for_status(
    execution_status: str,
    store_report: dict[str, Any],
    env_report: dict[str, Any],
    poll_report: dict[str, Any],
) -> str:
    if execution_status == "completed":
        return (
            f"Supabase env completion succeeded — stored {len(store_report.get('registered_names') or [])} key(s), "
            f"applied {len(env_report.get('applied_names') or [])} to Vercel, deployment ready."
        )
    if execution_status == "collection_failed":
        return str(store_report.get("detail") or "Could not collect Supabase credentials.")
    if execution_status == "env_failed":
        failed = ", ".join(env_report.get("failed_names") or [])
        return f"Supabase values stored but Vercel env apply failed for: {failed or 'unknown keys'}."
    if execution_status == "redeploy_failed":
        return "Env vars applied but Vercel redeploy failed."
    if execution_status in {"failed", "polling_failed"}:
        return str(poll_report.get("detail") or "Vercel deployment did not reach ready state.")
    if execution_status == "verification_failed":
        return "Deploy reached ready state but health verification failed."
    return f"Supabase env completion ended with status `{execution_status}`."
