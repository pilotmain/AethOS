# SPDX-License-Identifier: Apache-2.0
"""Railway deploy + env + verify E2E orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.provider_e2e_execution.composer import (
    compose_e2e_orchestration_preflight_reply,
    redact_checks_snapshot,
)
from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_readiness.blocker_mapping import map_railway_blockers
from aethos_core.provider_e2e_readiness.readiness_report import compose_structured_missing_config_report
from aethos_core.runtime.authority import authority

_RAILWAY_E2E_ACTION = "env configuration + redeploy + verify"


def _pick_target_service(
    checks: dict[str, Any],
    *,
    user_text: str = "",
    hint: str = "aethos",
) -> tuple[str, str, str] | None:
    from aethos_core.providers.railway.railway_inventory_target_picker import pick_single_railway_target

    picked = pick_single_railway_target(checks, user_text or hint, default_hint=hint)
    return picked


def _pick_target_services(
    checks: dict[str, Any],
    *,
    user_text: str,
    hint: str = "aethos",
) -> list[tuple[str, str, str]]:
    from aethos_core.providers.railway.railway_inventory_target_picker import pick_railway_targets

    result = pick_railway_targets(checks, user_text, default_hint=hint)
    return [(row.project, row.environment, row.service) for row in result.targets]


def route_railway_e2e_execution(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_greenfield_deployment_intent(text):
        return None

    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        compose_readiness_blocker,
        readonly_checks_passed,
    )

    checks = safe_run_deployment_readiness_checks(user_text=text, session_id=session_id)
    settings = get_settings()

    if not checks.get("railway_credential_ok"):
        blockers = map_railway_blockers(checks, settings=settings, include_mutation_gates=False)
        body = compose_structured_missing_config_report(
            provider="railway",
            requested_action=_RAILWAY_E2E_ACTION,
            blockers=blockers,
            required_configuration=list(
                checks.get("required_env_vars") or ["RAILWAY_API_TOKEN in Mission Control → Advanced settings → Credentials"]
            ),
        )
        return body, "railway_e2e_missing_config", _meta(stage="missing_credential", checks=checks, suppress_footer=True)

    if not checks.get("railway_api_connection_ok"):
        blockers = map_railway_blockers(checks, settings=settings, include_mutation_gates=False)
        body = compose_structured_missing_config_report(
            provider="railway",
            requested_action=_RAILWAY_E2E_ACTION,
            blockers=blockers,
            required_configuration=["Valid Railway API token with project read access"],
        )
        return body, "railway_e2e_missing_config", _meta(stage="api_connection_failed", checks=checks, suppress_footer=True)

    if not readonly_checks_passed(checks):
        body = compose_readiness_blocker(checks, diagnostic=str(checks.get("check_error") or ""))
        return body, "railway_e2e_readiness_blocked", _meta(stage="readiness_blocked", checks=checks, suppress_footer=True)

    targets = _pick_target_services(checks, user_text=text)
    if len(targets) > 1:
        return _route_multi_target_railway_e2e(
            text,
            checks=checks,
            settings=settings,
            targets=targets,
            session_id=session_id,
        )

    target = _pick_target_service(checks, user_text=text)
    if target is None:
        from aethos_core.providers.railway.railway_inventory_target_picker import pick_railway_targets
        from aethos_core.task_frame.railway_deploy_selection import (
            compose_ambiguous_railway_target_reply,
            detect_railway_deploy_operation,
            store_railway_deploy_selection_task,
        )

        picked = pick_railway_targets(checks, text)
        operation = detect_railway_deploy_operation(text)
        candidates = list(picked.candidates or [])
        if candidates:
            store_railway_deploy_selection_task(
                session_id=session_id,
                user_text=text,
                checks=checks,
                candidates=candidates,
                operation=operation,
            )
        blockers = map_railway_blockers(
            checks,
            settings=settings,
            target_resolved=False,
            include_mutation_gates=False,
        )
        body = compose_ambiguous_railway_target_reply(operation=operation, candidates=candidates)
        if not candidates:
            body = compose_structured_missing_config_report(
                provider="railway",
                requested_action=_RAILWAY_E2E_ACTION,
                blockers=blockers,
                required_configuration=["Target Railway service name (existing service required for redeploy path)"],
            )
        return body, "railway_e2e_missing_config", _meta(
            stage="ambiguous_target",
            checks=checks,
            suppress_footer=True,
            task_frame="stored" if candidates else "none",
        )

    project_name, environment_name, service_name = target
    target_label = f"{project_name} / {environment_name} / {service_name}"

    env_writes = settings.provider_env_var_mutations_enabled
    steps = [
        "Validate Railway credential and inventory (complete)",
        "Assess required env vars against secure store / env value readiness",
    ]
    if env_writes:
        steps.append("Governed `set_env_var` preflight for missing variables (approval required)")
    else:
        steps.append("Report env vars that must be configured manually (generic writes disabled)")
    steps.extend(
        [
            f"Governed redeploy of `{service_name}` (approval required)",
            "Poll deployment status and collect log evidence",
            "Verify health URL / deployment status and produce final report",
        ]
    )

    from aethos_core.provider_e2e_orchestration.job_model import enrich_job_params_for_orchestration

    job_params = enrich_job_params_for_orchestration(
        {
            "provider": "railway",
            "session_id": session_id,
            "user_request": text,
            "target": {
                "project_name": project_name,
                "environment_name": environment_name,
                "service_name": service_name,
            },
            "orchestration_steps": steps,
            "checks_snapshot": redact_checks_snapshot(checks),
            "env_var_mutations_enabled": env_writes,
            "mutation_execution_enabled": settings.mutation_execution_enabled,
        }
    )

    job = authority.create_job(
        title=f"Railway E2E: {service_name} deploy + env + verify",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params=job_params,
        source="chat",
        session_id=session_id,
        auto_run=False,
    )

    from aethos_core.jobs.session_approval_target import record_session_approval_target

    record_session_approval_target(
        session_id=session_id,
        job_id=job.id,
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        provider="railway",
        action_type="provider_e2e_orchestration",
    )

    inv = checks.get("inventory") or {}
    readiness_summary = (
        f"Railway token validated. Inventory: **{inv.get('project_count', 0)}** project(s), "
        f"**{inv.get('service_count', 0)}** service(s)."
    )
    body = compose_e2e_orchestration_preflight_reply(
        provider="railway",
        job_id=job.id,
        target_label=target_label,
        steps=steps,
        readiness_summary=readiness_summary,
        approval_path=mutation_approval_surface(),
    )
    return body, "railway_e2e_orchestration_preflight", _meta(
        stage="preflight_created",
        checks=checks,
        job_id=job.id,
        service=service_name,
    )


def _route_multi_target_railway_e2e(
    text: str,
    *,
    checks: dict[str, Any],
    settings: Any,
    targets: list[tuple[str, str, str]],
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight
    from aethos_core.task_frame.railway_deploy_selection import detect_railway_deploy_operation

    operation = detect_railway_deploy_operation(text)
    op_label = operation.replace("_", " ")
    job_ids: list[str] = []
    paths: list[str] = []
    for project_name, environment_name, service_name in targets:
        path = f"{project_name} / {environment_name} / {service_name}"
        params = {
            "user_request": text,
            "provider": "railway",
            "operation_type": operation,
            "target_name": service_name,
            "target": {
                "provider": "railway",
                "project_name": project_name,
                "environment": environment_name,
                "service_name": service_name,
                "resolved": True,
                "source": "railway_inventory_target_picker",
            },
            "target_resolved": True,
            "target_status": "resolved",
            "selected_target_path": path,
        }
        job = authority.create_job(
            title=f"Railway {op_label} mutation preflight — {service_name}",
            job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
            params=params,
            source="chat",
            session_id=session_id,
            auto_run=True,
        )
        sync_thread_from_preflight(job=job, user_request=text)
        job_ids.append(job.id)
        paths.append(path)

    approval_path = mutation_approval_surface()
    listed = "\n".join(f"- `{job_id}` → **{path}**" for job_id, path in zip(job_ids, paths))
    body = (
        f"Resolved **{len(paths)}** Railway staging target(s) for **{op_label}**:\n"
        f"{listed}\n\n"
        f"I created governed {op_label} prefights for each service. **No {op_label} has been performed yet.**\n\n"
        f"Review them in **{approval_path}** before approving execution."
    )
    return body, "railway_multi_target_preflight_created", _meta(
        stage="multi_preflight_created",
        checks=checks,
        job_id=job_ids[0] if job_ids else "",
        proposed_job_ids=",".join(job_ids),
        service=",".join(p.split(" / ")[-1] for p in paths),
        target_count=str(len(paths)),
    )


def _meta(*, stage: str, checks: dict[str, Any], suppress_footer: bool = False, **extra: str) -> dict[str, str]:
    meta = {
        "route_id": "railway_e2e_execution",
        "matched_module": "provider_e2e_execution.railway_e2e_execution",
        "provider": "railway",
        "e2e_stage": stage,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "capability_truth_only": "false",
    }
    if suppress_footer:
        meta["suppress_governance_footer"] = "true"
    meta["presentation_bypass"] = "true"
    if checks.get("railway_credential_ok"):
        meta["railway_credential_ok"] = "true"
    for key, value in extra.items():
        meta[key] = str(value)
    return meta
