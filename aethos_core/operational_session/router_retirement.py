# SPDX-License-Identifier: Apache-2.0
"""KERNEL_003/004 — legacy readonly router retirement registry."""

from __future__ import annotations

from typing import Literal

RouterDisposition = Literal[
    "SAFE_TO_DELETE",
    "SAFE_TO_DELEGATE",
    "DELETED_WAVE_2",
    "REQUIRES_KERNEL_FEATURE",
    "KEEP_TEMPORARILY",
]

WAVE_1_ROUTERS: dict[str, dict[str, str]] = {
    "railway_named_service_logs": {
        "module": "DELETED — was aethos_core.chat.railway_named_service_log_router",
        "capability": "Railway named service logs",
        "replacement": "operational_session.railway_readonly_executor.fetch_logs",
        "disposition": "DELETED_WAVE_2",
    },
    "multi_provider_health": {
        "module": "DELETED — was aethos_core.chat.multi_provider_health_router",
        "capability": "Named Railway/Vercel health inline",
        "replacement": "operational_session.railway_readonly_executor.health_check",
        "disposition": "DELETED_WAVE_2",
    },
    "explicit_provider_readonly_diagnostics": {
        "module": "DELETED — was aethos_core.operational_target_resolution.routing",
        "capability": "Explicit Vercel/Railway readonly diagnostics",
        "replacement": "operational_session.kernel_planner_bridge",
        "disposition": "DELETED_WAVE_2",
    },
    "railway_projects_inventory": {
        "module": "PARTIAL — route removed from railway_projects_chat",
        "capability": "Railway project/service inventory",
        "replacement": "operational_session.railway_readonly_executor.list_inventory",
        "disposition": "DELETED_WAVE_2",
    },
    "vercel_readonly_provider_router": {
        "module": "PARTIAL — Vercel branch removed from readonly_provider_router",
        "capability": "Vercel readonly logs/deployments",
        "replacement": "operational_session.vercel_readonly_executor",
        "disposition": "DELETED_WAVE_2",
    },
    "response_composition_rerender": {
        "module": "aethos_core.response_composition.response_composer",
        "capability": "Cached health rerender",
        "replacement": "operational_session session subject",
        "disposition": "SAFE_TO_DELEGATE",
    },
    "railway_credential_diagnostics": {
        "module": "aethos_core.providers.railway.deployment_readiness.railway_credential_diagnostics",
        "capability": "Railway token validation chat",
        "replacement": "execution_brain.provider_tool_contract railway.validate_token",
        "disposition": "KEEP_TEMPORARILY",
    },
    "railway_deployment_lifecycle_diagnostics": {
        "module": "aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_diagnostics_router",
        "capability": "Deployment lifecycle readonly",
        "replacement": "operational_session.railway_readonly_executor.deployment_status",
        "disposition": "REQUIRES_KERNEL_FEATURE",
    },
    "internal_diagnostics_router": {
        "module": "aethos_core.chat.route_trace",
        "capability": "Route trace / API meta",
        "replacement": "KEEP — not operational readonly",
        "disposition": "KEEP_TEMPORARILY",
    },
    "provider_readiness_routes": {
        "module": "aethos_core.provider_e2e_readiness.readiness_router",
        "capability": "E2E readiness reports",
        "replacement": "execution_brain deploy_planning",
        "disposition": "KEEP_TEMPORARILY",
    },
}


def kernel_router_retirement_enabled() -> bool:
    from aethos_core.config import get_settings

    settings = get_settings()
    return bool(settings.operational_conversation_kernel_enabled and settings.kernel_router_retirement_enabled)


def vercel_reference_lane_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().vercel_reference_lane_enabled)


def legacy_readonly_router_retired(router_id: str) -> bool:
    """Wave 2: deleted routers are permanently retired when kernel retirement flag is on."""
    if not kernel_router_retirement_enabled():
        return False
    row = WAVE_1_ROUTERS.get(router_id)
    if row is None:
        return False
    return row.get("disposition") in {"SAFE_TO_DELEGATE", "DELETED_WAVE_2"}


def wave_1_retirement_stats() -> dict[str, int | float]:
    total = len(WAVE_1_ROUTERS)
    delegated = sum(
        1 for row in WAVE_1_ROUTERS.values() if row.get("disposition") in {"SAFE_TO_DELEGATE", "DELETED_WAVE_2"}
    )
    deleted = sum(1 for row in WAVE_1_ROUTERS.values() if row.get("disposition") == "DELETED_WAVE_2")
    return {
        "total_cataloged": total,
        "wave_1_delegated": delegated,
        "wave_2_deleted": deleted,
        "delegation_percent": round(100.0 * delegated / total, 1) if total else 0.0,
        "deletion_percent": round(100.0 * deleted / total, 1) if total else 0.0,
    }


def delegate_to_kernel_notice(router_id: str) -> str:
    row = WAVE_1_ROUTERS.get(router_id) or {}
    return str(row.get("replacement") or "operational_conversation_kernel")
