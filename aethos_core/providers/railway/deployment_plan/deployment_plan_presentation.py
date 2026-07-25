# SPDX-License-Identifier: Apache-2.0
"""Presentation bypass for Railway deployment plan artifacts — no cleanroom truncation."""

from __future__ import annotations

from typing import Any

RAILWAY_DEPLOYMENT_PLAN_ROUTE_ID = "railway_deployment_plan"
RAILWAY_CREATION_PREFLIGHT_ROUTE_ID = "railway_deployment_creation_preflight"
RAILWAY_SERVICE_CREATION_SIMULATOR_ROUTE_ID = "railway_service_creation_simulator"
PROVIDER_E2E_READINESS_ROUTE_ID = "provider_e2e_readiness_report"
RAILWAY_E2E_EXECUTION_ROUTE_ID = "railway_e2e_execution"
VERCEL_E2E_EXECUTION_ROUTE_ID = "vercel_e2e_execution"

PROVIDER_E2E_PRESENTATION_INTENTS = frozenset(
    {
        "provider_e2e_readiness_report",
        "railway_e2e_missing_config",
        "vercel_e2e_missing_config",
        "railway_e2e_orchestration_preflight",
        "vercel_e2e_orchestration_preflight",
        "railway_e2e_readiness_blocked",
        "execution_brain_railway_pilot",
        "execution_brain_preflight_created",
        "execution_brain_recovery",
        "execution_brain_turn",
    }
)

RAILWAY_DEPLOYMENT_PLAN_INTENTS = frozenset(
    {
        "railway_deployment_plan",
        "railway_deployment_plan_show",
        "railway_deployment_plan_draft",
        "railway_deployment_plan_clarification",
        "railway_deployment_plan_needs_readiness",
        "railway_deployment_plan_needs_repo",
        "railway_deployment_plan_show_missing",
        "railway_deployment_plan_complete",
        "railway_deployment_plan_completion",
        "railway_deployment_plan_complete_needs_plan",
        "railway_deployment_plan_review",
        "railway_deployment_plan_review_not_ready",
        "railway_deployment_plan_confirm",
        "railway_deployment_plan_confirm_already",
        "railway_deployment_plan_confirm_not_ready",
        "railway_creation_preflight_draft",
        "railway_creation_preflight_show",
        "railway_creation_preflight_show_missing",
        "railway_creation_preflight_not_ready",
        "railway_creation_preflight_approved",
        "railway_creation_preflight_approve_already",
        "railway_creation_preflight_approve_missing",
        "railway_service_creation_simulation",
        "railway_service_creation_simulation_show",
        "railway_service_creation_simulation_show_missing",
        "railway_service_creation_simulation_not_ready",
        "railway_service_creation_simulation_blocking",
        "railway_service_creation_simulation_blocking_missing",
        "railway_service_creation_simulation_passed",
        "railway_service_creation_simulation_passed_missing",
        "railway_service_creation_simulation_failed",
        "railway_service_creation_simulation_failed_missing",
    }
)


def is_railway_deployment_plan_presentation_bypass(
    *,
    intent: str = "",
    route_id: str = "",
    meta: dict[str, Any] | None = None,
    channel: str = "chat",
) -> bool:
    """True when outbound shaping must not truncate the governed plan artifact."""
    from aethos_core.governance.approval_privacy_governance import chat_presentation_bypass_allowed

    if not chat_presentation_bypass_allowed(channel=channel):
        return False
    rid = route_id or str((meta or {}).get("route_id") or "")
    if rid in {
        RAILWAY_DEPLOYMENT_PLAN_ROUTE_ID,
        RAILWAY_CREATION_PREFLIGHT_ROUTE_ID,
        RAILWAY_SERVICE_CREATION_SIMULATOR_ROUTE_ID,
        PROVIDER_E2E_READINESS_ROUTE_ID,
        "execution_brain",
        RAILWAY_E2E_EXECUTION_ROUTE_ID,
        VERCEL_E2E_EXECUTION_ROUTE_ID,
    }:
        return True
    if str((meta or {}).get("presentation_bypass") or "").lower() == "true":
        return True
    intent_name = intent or ""
    if intent_name in PROVIDER_E2E_PRESENTATION_INTENTS:
        return True
    return intent_name in RAILWAY_DEPLOYMENT_PLAN_INTENTS
