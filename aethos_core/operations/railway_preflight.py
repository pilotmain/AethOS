# SPDX-License-Identifier: Apache-2.0
"""Railway read-only operation preflight builders."""

from __future__ import annotations

from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.orchestration.preflight_builder import (
    RAILWAY_PREFLIGHT_PROFILE,
    build_ambiguous_target_preflight,
    build_api_readonly_resolved_preflight,
    build_missing_target_preflight,
    format_api_provider_preflight_report,
    mutation_blockers,
)
from aethos_core.operations.target_resolution import TargetResolution


def build_railway_preflight(
    *,
    operation_type: str,
    resolution: TargetResolution,
    user_request: str,
) -> OperationPreflight:
    profile = RAILWAY_PREFLIGHT_PROFILE
    op = operation_type
    blockers = mutation_blockers(op, message=profile.mutation_blocker_message)

    if resolution.status == "ambiguous":
        return build_ambiguous_target_preflight(profile, operation_type=op, resolution=resolution)

    target = resolution.target_name
    if resolution.status != "resolved" or not target:
        return build_missing_target_preflight(profile, operation_type=op, resolution=resolution)

    steps = [
        f"Resolve Railway service `{target}`.",
        f"Run read-only {op.replace('_', ' ')} via Railway API.",
        "Produce evidence artifact in Mission Control.",
    ]
    return build_api_readonly_resolved_preflight(
        profile,
        operation_type=op,
        target=target,
        user_request=user_request,
        proposed_steps=steps,
        blockers=blockers,
    )


def format_preflight_report(preflight: OperationPreflight, *, user_request: str = "") -> str:
    return format_api_provider_preflight_report(
        preflight,
        user_request=user_request,
        provider_title=RAILWAY_PREFLIGHT_PROFILE.provider_title,
    )
