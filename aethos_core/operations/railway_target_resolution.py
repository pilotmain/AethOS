# SPDX-License-Identifier: Apache-2.0
"""Resolve Railway service targets via aliases, inventory, and provider API."""

from __future__ import annotations

from aethos_core.operations.target_resolution import TargetResolution
from aethos_core.providers.railway.target_resolver import (
    TARGET_APPROVAL_THRESHOLD,
    resolve_railway_provider_target,
)


def resolve_railway_target(
    *,
    user_request: str,
    target_hints: list[str] | None,
    operation_type: str,
) -> TargetResolution:
    target = resolve_railway_provider_target(
        user_request=user_request,
        target_hints=target_hints,
        operation_type=operation_type,
    )
    matches = [str(row.get("service_name") or "") for row in target.candidates if row.get("service_name")]
    memory = target.to_dict()

    if target.resolved and target.confidence >= TARGET_APPROVAL_THRESHOLD:
        return TargetResolution(
            status="resolved",
            target_name=target.service_name,
            matches=matches,
            memory=memory,
            message=f"Resolved Railway service `{target.service_name}`.",
            source=target.source,
        )
    if target.reason in {"ambiguous_api_match", "ambiguous_inventory_match"}:
        return TargetResolution(
            status="ambiguous",
            matches=matches,
            memory=memory,
            message="Multiple Railway services matched.",
            source=target.source,
        )
    if target.reason == "provider_inventory_unavailable":
        return TargetResolution(
            status="missing",
            target_name=target.service_name,
            matches=matches,
            memory=memory,
            message="Railway provider inventory is unavailable.",
            source=target.source,
        )
    if target.reason == "missing_target_phrase":
        return TargetResolution(
            status="missing",
            matches=matches,
            memory=memory,
            message="Specify a Railway service name.",
            source=target.source,
        )
    return TargetResolution(
        status="missing",
        target_name=target.service_name,
        matches=matches,
        memory=memory,
        message=f"Service `{target.service_name or 'unknown'}` was not found in Railway inventory.",
        source=target.source,
    )
