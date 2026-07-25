# SPDX-License-Identifier: Apache-2.0
"""Vercel deploy + env + verify E2E orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.provider_e2e_execution.composer import compose_e2e_orchestration_preflight_reply
from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_readiness.blocker_mapping import map_vercel_blockers
from aethos_core.provider_e2e_readiness.readiness_report import compose_structured_missing_config_report
from aethos_core.runtime.authority import authority

_VERCEL_E2E_ACTION = "env configuration + redeploy + verify"


def _pick_vercel_project(projects: list[dict[str, Any]], *, hint: str = "aethos") -> dict[str, Any] | None:
    hint_lower = hint.lower()
    matches = [p for p in projects if hint_lower in str(p.get("name") or "").lower()]
    if len(matches) == 1:
        return matches[0]
    if len(projects) == 1:
        return projects[0]
    return None


def route_vercel_e2e_execution(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter
    from aethos_core.providers.vercel.api_client import list_projects

    settings = get_settings()
    auth = VercelAuthAdapter()
    resolved = auth.resolve_best_auth_method(operation="read_projects")
    if resolved.get("method") != "api_token":
        blockers = map_vercel_blockers(
            credential_ok=False,
            credential_detail=str(resolved.get("detail") or "Vercel API token not configured or validated."),
            settings=settings,
            include_mutation_gates=False,
        )
        body = compose_structured_missing_config_report(
            provider="vercel",
            requested_action=_VERCEL_E2E_ACTION,
            blockers=blockers,
            required_configuration=["Vercel API token in Mission Control → Advanced settings → Credentials"],
        )
        return body, "vercel_e2e_missing_config", _meta(stage="missing_credential", suppress_footer=True)

    credential_id = str(resolved.get("credential_id") or "")
    token = auth.get_api_token(credential_id)
    if not token:
        blockers = map_vercel_blockers(
            credential_ok=False,
            credential_detail="Vercel token could not be loaded from the credential vault.",
            settings=settings,
            include_mutation_gates=False,
        )
        body = compose_structured_missing_config_report(
            provider="vercel",
            requested_action=_VERCEL_E2E_ACTION,
            blockers=blockers,
            required_configuration=["Validated Vercel API token"],
        )
        return body, "vercel_e2e_missing_config", _meta(stage="token_load_failed", suppress_footer=True)

    try:
        projects = list_projects(token)
    except Exception as exc:
        blockers = map_vercel_blockers(
            credential_ok=True,
            connection_ok=False,
            connection_detail=str(exc),
            settings=settings,
            include_mutation_gates=False,
        )
        body = compose_structured_missing_config_report(
            provider="vercel",
            requested_action=_VERCEL_E2E_ACTION,
            blockers=blockers,
            required_configuration=["Vercel token with project read scope"],
        )
        return body, "vercel_e2e_missing_config", _meta(stage="project_list_failed", suppress_footer=True)

    if not projects:
        blockers = map_vercel_blockers(
            credential_ok=True,
            connection_ok=True,
            project_count=0,
            settings=settings,
            include_mutation_gates=False,
        )
        body = compose_structured_missing_config_report(
            provider="vercel",
            requested_action=_VERCEL_E2E_ACTION,
            blockers=blockers,
            required_configuration=["Existing Vercel project linked to your repository"],
        )
        return body, "vercel_e2e_missing_config", _meta(stage="no_projects", suppress_footer=True)

    project = _pick_vercel_project(projects)
    if project is None:
        blockers = map_vercel_blockers(
            credential_ok=True,
            connection_ok=True,
            project_resolved=False,
            project_count=len(projects),
            settings=settings,
            include_mutation_gates=False,
        )
        body = compose_structured_missing_config_report(
            provider="vercel",
            requested_action=_VERCEL_E2E_ACTION,
            blockers=blockers,
            required_configuration=["Explicit Vercel project name"],
        )
        return body, "vercel_e2e_missing_config", _meta(stage="ambiguous_project", suppress_footer=True)

    project_name = str(project.get("name") or "")
    env_writes = settings.provider_env_var_mutations_enabled
    steps = [
        "Validate Vercel credential and list projects (complete)",
        f"Inspect env var keys/targets for `{project_name}` (values never shown)",
    ]
    if env_writes:
        steps.append("Governed env var add/update preflight for missing keys (approval required)")
    else:
        steps.append("Report env keys that must be configured manually")
    steps.extend(
        [
            f"Governed production redeploy of `{project_name}` (approval required)",
            "Poll deployment status and verify deployment URL",
            "Produce final verification report in Mission Control → Jobs",
        ]
    )

    from aethos_core.provider_e2e_orchestration.job_model import enrich_job_params_for_orchestration

    job_params = enrich_job_params_for_orchestration(
        {
            "provider": "vercel",
            "session_id": session_id,
            "user_request": text,
            "target": {"project_name": project_name, "project_id": str(project.get("id") or "")},
            "project_name": project_name,
            "project_id": str(project.get("id") or ""),
            "credential_id": credential_id,
            "orchestration_steps": steps,
            "env_var_mutations_enabled": env_writes,
            "mutation_execution_enabled": settings.mutation_execution_enabled,
            "t3_production_enabled": settings.mutation_t3_production_enabled,
        }
    )

    job = authority.create_job(
        title=f"Vercel E2E: {project_name} deploy + env + verify",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params=job_params,
        source="chat",
        session_id=session_id,
        auto_run=False,
    )

    body = compose_e2e_orchestration_preflight_reply(
        provider="vercel",
        job_id=job.id,
        target_label=f"Vercel project `{project_name}`",
        steps=steps,
        readiness_summary=f"Vercel token validated. **{len(projects)}** project(s) visible.",
        approval_path=mutation_approval_surface(),
    )
    return body, "vercel_e2e_orchestration_preflight", _meta(
        stage="preflight_created",
        job_id=job.id,
        project=project_name,
    )


def _meta(*, stage: str, suppress_footer: bool = False, **extra: str) -> dict[str, str]:
    meta = {
        "route_id": "vercel_e2e_execution",
        "matched_module": "provider_e2e_execution.vercel_e2e_execution",
        "provider": "vercel",
        "e2e_stage": stage,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "capability_truth_only": "false",
    }
    if suppress_footer:
        meta["suppress_governance_footer"] = "true"
    meta["presentation_bypass"] = "true"
    for key, value in extra.items():
        meta[key] = str(value)
    return meta
