# SPDX-License-Identifier: Apache-2.0
"""Route provider E2E readiness prompts — inspect and report only."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.provider_e2e_readiness.blocker_mapping import (
    map_railway_blockers,
    map_vercel_blockers,
)
from aethos_core.provider_e2e_readiness.readiness_intent import (
    detect_provider_e2e_readiness_kind,
    is_provider_e2e_readiness_intent,
)
from aethos_core.provider_e2e_readiness.readiness_report import compose_structured_readiness_report


def route_provider_e2e_readiness(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_provider_e2e_readiness_intent(text):
        return None

    kind = detect_provider_e2e_readiness_kind(text)
    if kind == "railway":
        return _route_railway(text, session_id=session_id)
    if kind == "vercel":
        return _route_vercel(text, session_id=session_id)
    return None


def _route_railway(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )

    checks = safe_run_deployment_readiness_checks(user_text=text, session_id=session_id)
    settings = get_settings()
    checks["mutation_execution_enabled"] = settings.mutation_execution_enabled
    checks["provider_env_var_mutations_enabled"] = settings.provider_env_var_mutations_enabled

    target = _resolve_railway_target(checks, user_text=text)
    target_label = " / ".join(target) if target else ""
    inv = checks.get("inventory") or {}
    target_resolved: bool | None = None
    if checks.get("railway_api_connection_ok") and inv.get("ok"):
        if target is not None:
            target_resolved = True
        elif int(inv.get("service_count") or 0) == 0:
            target_resolved = False
        elif int(inv.get("service_count") or 0) > 1:
            target_resolved = False
    blockers = map_railway_blockers(
        checks,
        settings=settings,
        target_resolved=target_resolved,
        include_mutation_gates=True,
    )
    overall_ready = not blockers and bool(checks.get("railway_api_connection_ok"))
    body = compose_structured_readiness_report(
        provider="railway",
        checks=checks,
        blockers=blockers,
        target_label=target_label,
        overall_ready=overall_ready,
    )
    return body, "provider_e2e_readiness_report", _meta(
        provider="railway",
        stage="readiness_report",
        checks=checks,
        blocker_count=len(blockers),
    )


def _route_vercel(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.provider_e2e_readiness.vercel_readiness_checks import run_vercel_readiness_checks

    checks = run_vercel_readiness_checks(session_id=session_id)
    settings = get_settings()
    project_count = int(checks.get("vercel_project_count") or 0)
    projects = list(checks.get("vercel_projects") or [])
    target_label = ""
    project_resolved: bool | None = None
    if project_count == 1 and projects:
        target_label = str(projects[0].get("name") or "")
        project_resolved = True
    elif project_count > 1:
        project_resolved = False

    blockers = map_vercel_blockers(
        credential_ok=bool(checks.get("vercel_credential_ok")),
        credential_detail=str(checks.get("vercel_credential_detail") or ""),
        connection_ok=bool(checks.get("vercel_api_connection_ok")),
        connection_detail=str(checks.get("vercel_api_connection_detail") or ""),
        project_resolved=project_resolved,
        project_count=project_count,
        settings=settings,
        include_mutation_gates=True,
    )
    overall_ready = not blockers and bool(checks.get("vercel_api_connection_ok"))
    body = compose_structured_readiness_report(
        provider="vercel",
        checks=checks,
        blockers=blockers,
        target_label=target_label,
        overall_ready=overall_ready,
    )
    return body, "provider_e2e_readiness_report", _meta(
        provider="vercel",
        stage="readiness_report",
        checks=checks,
        blocker_count=len(blockers),
    )


def _resolve_railway_target(checks: dict[str, Any], *, user_text: str = "") -> tuple[str, str, str] | None:
    from aethos_core.providers.railway.railway_inventory_target_picker import pick_single_railway_target

    return pick_single_railway_target(checks, user_text, default_hint="aethos")


def _meta(
    *,
    provider: str,
    stage: str,
    checks: dict[str, Any],
    blocker_count: int,
) -> dict[str, str]:
    meta = {
        "route_id": "provider_e2e_readiness_report",
        "matched_module": "provider_e2e_readiness.readiness_router",
        "provider": provider,
        "provider_e2e_readiness_stage": stage,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_started": "false",
        "preflight_created": "false",
        "suppress_governance_footer": "true",
        "presentation_bypass": "true",
        "blocker_count": str(blocker_count),
    }
    if provider == "railway":
        inv = checks.get("inventory") or {}
        if inv.get("project_count") is not None:
            meta["railway_project_count"] = str(inv.get("project_count"))
    else:
        meta["vercel_project_count"] = str(checks.get("vercel_project_count") or 0)
    return meta
