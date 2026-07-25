# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements evaluator."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
    ORG_PLAN_TO_COMMERCIAL_PLAN,
    PLAN_CAPABILITIES,
    PLAN_CHANNELS,
    PLAN_LIMITS,
    PLAN_PROVIDERS,
    PLANS,
    UPGRADE_PATHS,
)


def normalize_commercial_plan(org_plan: str | None) -> str:
    lowered = str(org_plan or "free").strip().lower()
    for source, commercial in ORG_PLAN_TO_COMMERCIAL_PLAN:
        if lowered == source:
            return commercial
    return "FREE"


def plan_limits(plan: str) -> dict[str, int | None]:
    for name, limits in PLAN_LIMITS:
        if name == plan:
            return dict(limits)
    return dict(PLAN_LIMITS[0][1])


def plan_capabilities(plan: str) -> tuple[str, ...]:
    for name, capabilities in PLAN_CAPABILITIES:
        if name == plan:
            return capabilities
    return PLAN_CAPABILITIES[0][1]


def plan_channels(plan: str) -> tuple[str, ...]:
    for name, channels in PLAN_CHANNELS:
        if name == plan:
            return channels
    return PLAN_CHANNELS[0][1]


def plan_providers(plan: str) -> tuple[str, ...]:
    for name, providers in PLAN_PROVIDERS:
        if name == plan:
            return providers
    return PLAN_PROVIDERS[0][1]


def is_capability_entitled(*, plan: str, capability: str) -> bool:
    return capability in plan_capabilities(plan)


def is_channel_entitled(*, plan: str, channel: str) -> bool:
    return channel in plan_channels(plan)


def is_provider_entitled(*, plan: str, provider: str) -> bool:
    return provider in plan_providers(plan)


def enterprise_only_capabilities() -> tuple[str, ...]:
    return plan_capabilities("ENTERPRISE")


def free_blocked_from_enterprise_entitlements(*, plan: str) -> list[str]:
    blocked = []
    for capability in enterprise_only_capabilities():
        if not is_capability_entitled(plan=plan, capability=capability):
            blocked.append(capability)
    return blocked


def usage_within_limits(*, plan: str, usage: dict[str, int]) -> dict[str, Any]:
    limits = plan_limits(plan)
    rows = []
    all_within = True
    for key, maximum in limits.items():
        metric = key.replace("max_", "")
        current = int(usage.get(metric, usage.get(key, 0)))
        if maximum is None:
            within = True
            remaining = None
        else:
            within = current <= maximum
            remaining = max(0, maximum - current)
        if not within:
            all_within = False
        rows.append(
            {
                "metric": metric,
                "current": current,
                "maximum": maximum,
                "remaining": remaining,
                "within_limit": within,
                "read_only": True,
            }
        )
    return {"within_all_limits": all_within, "limits": rows, "read_only": True}


def upgrade_opportunities(*, plan: str) -> list[dict[str, Any]]:
    opportunities = []
    for source, target in UPGRADE_PATHS:
        if source == plan:
            opportunities.append(
                {
                    "from_plan": source,
                    "to_plan": target,
                    "advisory_only": True,
                    "automatic_upgrade_enabled": False,
                    "read_only": True,
                }
            )
    return opportunities


def plan_registry_rows() -> list[dict[str, Any]]:
    rows = []
    for plan in PLANS:
        rows.append(
            {
                "plan": plan,
                "capabilities": list(plan_capabilities(plan)),
                "channels": list(plan_channels(plan)),
                "providers": list(plan_providers(plan)),
                "limits": plan_limits(plan),
                "read_only": True,
            }
        )
    return rows
