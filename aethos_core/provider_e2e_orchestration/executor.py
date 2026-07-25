# SPDX-License-Identifier: Apache-2.0
"""Run approved provider E2E orchestration — env → redeploy → poll → verify → report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.provider_e2e_orchestration.approval_gate import (
    build_approval_gate_validation_report,
    validate_approval_gate,
)
from aethos_core.provider_e2e_orchestration.deployment_polling import poll_deployment_status
from aethos_core.provider_e2e_orchestration.env_var_execution import apply_env_vars
from aethos_core.provider_e2e_orchestration.evidence_bundle import build_provider_e2e_evidence_bundle
from aethos_core.provider_e2e_orchestration.final_report import (
    build_final_report_payload,
    compose_provider_e2e_final_report,
)
from aethos_core.provider_e2e_orchestration.health_verification import verify_health
from aethos_core.provider_e2e_orchestration.job_model import build_provider_e2e_job_model
from aethos_core.provider_e2e_orchestration.redeploy_execution import execute_redeploy
from aethos_core.security.secret_redaction import redact_text


@dataclass
class ProviderE2EExecutionOutcome:
    summary: str
    full_result: str
    executed: bool
    blocked: bool
    artifact: dict[str, Any]


def run_provider_e2e_orchestration(*, job_id: str, params: dict[str, Any]) -> ProviderE2EExecutionOutcome:
    from aethos_core.runtime.jobs import job_store

    params = dict(params)
    if _is_governed_railway_greenfield(params):
        return _run_governed_railway_greenfield_orchestration(job_id=job_id, params=params)

    job = job_store.get(job_id)
    gate = validate_approval_gate(job, for_execution=True)
    if not gate.ok:
        report = build_approval_gate_validation_report(gate)
        body = _blocked_report(gate.failure_state or "blocked", gate.detail, report)
        return ProviderE2EExecutionOutcome(
            summary=gate.detail or "E2E orchestration blocked.",
            full_result=body,
            executed=False,
            blocked=True,
            artifact={
                "execution_status": "blocked",
                "failure_state": gate.failure_state,
                "approval_gate_validation_report": report,
            },
        )

    model = build_provider_e2e_job_model(params)
    params = dict(params)
    params["execution_status"] = "running"
    approved = bool(params.get("provider_e2e_approved"))

    env_report = apply_env_vars(model, params=params, mutation_execution_approved=approved)
    env_report = _annotate_build_critical_env(model, params, env_report)

    if model.env_var_names and not env_report.get("ok") and not env_report.get("skipped"):
        return _finish(
            job_id=job_id,
            params=params,
            model=model,
            execution_status="env_failed",
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
            model=model,
            execution_status="redeploy_failed",
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
            model=model,
            execution_status="polling_failed" if poll_report.get("final_state") == "timed_out" else "failed",
            env_report=env_report,
            redeploy_report=redeploy_report,
            poll_report=poll_report,
            health_report={"ok": False, "detail": "Skipped — deploy not ready."},
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
        model=model,
        execution_status=execution_status,
        env_report=env_report,
        redeploy_report=redeploy_report,
        poll_report=poll_report,
        health_report=health_report,
    )


def _is_governed_railway_greenfield(params: dict[str, Any]) -> bool:
    from aethos_core.providers.railway.greenfield_deployment.governed_greenfield_executor import (
        is_governed_railway_greenfield_orchestration,
    )

    return is_governed_railway_greenfield_orchestration(params)


def _run_governed_railway_greenfield_orchestration(
    *,
    job_id: str,
    params: dict[str, Any],
) -> ProviderE2EExecutionOutcome:
    from aethos_core.providers.railway.greenfield_deployment.governed_greenfield_executor import (
        run_governed_railway_greenfield_orchestration,
    )
    from aethos_core.provider_e2e_orchestration.job_model import build_provider_e2e_job_model

    model = build_provider_e2e_job_model(params)
    summary, full_result, executed, artifact = run_governed_railway_greenfield_orchestration(
        job_id=job_id,
        params=params,
    )
    execution_status = str(artifact.get("execution_status") or ("completed" if executed else "failed"))
    blocked = execution_status == "blocked"
    return ProviderE2EExecutionOutcome(
        summary=summary,
        full_result=full_result,
        executed=executed,
        blocked=blocked,
        artifact={
            **artifact,
            "provider_e2e_evidence_bundle": {
                "provider": model.provider,
                "greenfield": True,
                "journal": artifact.get("journal"),
            },
        },
    )


def _finish(
    *,
    job_id: str,
    params: dict[str, Any],
    model,
    execution_status: str,
    env_report: dict[str, Any],
    redeploy_report: dict[str, Any],
    poll_report: dict[str, Any],
    health_report: dict[str, Any],
) -> ProviderE2EExecutionOutcome:
    advisory: dict[str, Any] = {}
    advisory_text = ""
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
    if execution_status != "completed":
        from aethos_core.provider_e2e_orchestration.e2e_completion_advisor import (
            build_e2e_completion_advisory,
            compose_completion_advisory_report,
        )

        advisory = build_e2e_completion_advisory(
            model=model,
            params=params,
            env_report=env_report,
            poll_report=poll_report,
            redeploy_report=redeploy_report,
            execution_status=execution_status,
        )
        advisory_text = compose_completion_advisory_report(advisory)
        evidence["completion_advisory"] = advisory
    full_report = compose_provider_e2e_final_report(
        provider=model.provider,
        evidence=evidence,
        execution_status=execution_status,
        completion_advisory_text=advisory_text,
    )
    payload = build_final_report_payload(
        full_report=full_report,
        evidence=evidence,
        execution_status=execution_status,
    )
    summary_override = ""
    if execution_status == "env_failed" and model.provider == "railway":
        from aethos_core.providers.railway.env_value_readiness.deployment_env_guidance import (
            assess_deployment_env_for_plan,
            compose_deployment_env_block_report,
        )

        plan = dict(params.get("target_plan") or {})
        if params.get("referenced_github_repo"):
            plan.setdefault("repo", str(params.get("referenced_github_repo") or ""))
        plan.setdefault("project", model.project_name)
        plan.setdefault("environment", model.environment)
        plan.setdefault("service_name", model.service_name)
        env_report_dict = dict(params.get("required_env_var_report") or {})
        env_report_dict.setdefault("required_env_var_names", list(model.env_var_names or []))
        assessment = assess_deployment_env_for_plan(plan=plan, env_report=env_report_dict)
        summary_override, block_report = compose_deployment_env_block_report(assessment)
        advisory_text = block_report
        evidence["deployment_env_assessment"] = assessment.to_dict()
        artifact_assessment = assessment.to_dict()
    else:
        artifact_assessment = None

    artifact = {
        "execution_status": execution_status,
        "env_var_execution_report": _redact_report(env_report),
        "redeploy_execution_report": redeploy_report,
        "deployment_polling_report": poll_report,
        "health_verification_report": health_report,
        "provider_e2e_evidence_bundle": evidence,
        "provider_e2e_final_report": payload,
        "completion_advisory": advisory,
        "mutating": execution_status == "completed",
        "executed": execution_status == "completed",
    }
    if artifact_assessment is not None:
        artifact["deployment_env_assessment"] = artifact_assessment
    return ProviderE2EExecutionOutcome(
        summary=summary_override or str(payload.get("summary") or "E2E orchestration finished."),
        full_result=redact_text(full_report),
        executed=execution_status == "completed",
        blocked=execution_status == "blocked",
        artifact=artifact,
    )


def _redact_report(report: dict[str, Any]) -> dict[str, Any]:
    safe = dict(report)
    safe.pop("env_var_value", None)
    return safe


def _blocked_report(failure: str, detail: str, report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Provider E2E orchestration blocked",
            "",
            f"**Reason:** `{failure}`",
            "",
            detail,
            "",
            f"Gate report: `{report}`",
        ]
    )


def _annotate_build_critical_env(model, params: dict[str, Any], env_report: dict[str, Any]) -> dict[str, Any]:
    if model.provider != "vercel":
        return env_report
    from aethos_core.provider_e2e_orchestration.e2e_completion_advisor import _required_env_names
    from aethos_core.providers.vercel.greenfield_deployment.build_env_criticality import list_build_critical_env_names

    names = _required_env_names(params, env_report)
    framework = str((params.get("target_plan") or {}).get("framework") or "nextjs")
    build_critical = list_build_critical_env_names(names, framework=framework)
    applied = {str(n).upper() for n in (env_report.get("applied_names") or [])}
    missing_build = [n for n in build_critical if n.upper() not in applied]
    annotated = dict(env_report)
    annotated["build_critical_env_names"] = build_critical
    annotated["missing_build_critical_env_names"] = missing_build
    annotated["all_required_names"] = names
    if missing_build and not env_report.get("skipped"):
        annotated["ok"] = False
        annotated["detail"] = (
            f"Cannot deploy safely — {len(missing_build)} build-critical env var(s) missing "
            f"({', '.join(missing_build[:6])}{'…' if len(missing_build) > 6 else ''})."
        )
    return annotated
