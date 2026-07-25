# SPDX-License-Identifier: Apache-2.0
"""Canonical provider target resolution — shared across readonly and mutation flows."""

from __future__ import annotations

from aethos_core.operations.target_resolution import TargetResolution


def collect_target_hints(*, user_request: str, target_hints: list[str] | None) -> list[str]:
    from aethos_core.operations.intents import extract_target_hints

    hints: list[str] = []
    seen: set[str] = set()
    for h in list(target_hints or []) + extract_target_hints(user_request):
        key = (h or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            hints.append(h.strip())
    return hints


def canonical_resolve_target(
    *,
    provider: str,
    user_request: str,
    target_hints: list[str] | None,
    operation_type: str,
) -> TargetResolution:
    hints = collect_target_hints(user_request=user_request, target_hints=target_hints)
    if provider == "railway":
        from aethos_core.operations.orchestration.target_resolution.railway_resolution import (
            resolve_railway_target,
        )

        return resolve_railway_target(
            user_request=user_request,
            target_hints=hints,
            operation_type=operation_type,
        )
    if provider == "github":
        from aethos_core.operations.orchestration.target_resolution.github_resolution import (
            resolve_github_target,
        )

        return resolve_github_target(
            user_request=user_request,
            target_hints=hints,
            operation_type=operation_type,
        )
    if provider in ("vercel", "unknown"):
        from aethos_core.operations.orchestration.target_resolution.vercel_resolution import (
            resolve_vercel_target,
        )

        return resolve_vercel_target(
            user_request=user_request,
            target_hints=hints,
            operation_type=operation_type,
        )
    return TargetResolution(
        status="missing",
        target_name=hints[0] if hints else None,
        message=f"Target resolution not configured for provider `{provider}`.",
        source="canonical",
    )
