# SPDX-License-Identifier: Apache-2.0
"""GitHub read-only operation preflight builders."""

from __future__ import annotations

from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.orchestration.preflight_builder import (
    GITHUB_PREFLIGHT_PROFILE,
    build_ambiguous_target_preflight,
    build_api_readonly_resolved_preflight,
    build_missing_target_preflight,
    format_api_provider_preflight_report,
    mutation_blockers,
)
from aethos_core.operations.target_resolution import TargetResolution


def _github_proposed_steps(*, target: str, operation_type: str) -> list[str]:
    if operation_type == "workflow_diagnostic":
        return [
            f"Resolve GitHub repository `{target}`.",
            "Find recent failed workflow runs using GitHub Actions API.",
            "Collect readonly workflow run/job evidence.",
            "Produce failure diagnostic artifact in Mission Control.",
        ]
    if operation_type == "workflow_jobs":
        return [
            f"Resolve GitHub repository `{target}`.",
            "Find recent failed workflow runs using GitHub Actions API.",
            "Collect failed job and step metadata.",
            "Produce job-level evidence artifact in Mission Control.",
        ]
    return [
        f"Resolve GitHub repository `{target}`.",
        f"Run read-only {operation_type.replace('_', ' ')} via GitHub Actions API.",
        "Produce evidence artifact in Mission Control.",
    ]


def build_github_preflight(
    *,
    operation_type: str,
    resolution: TargetResolution,
    user_request: str,
) -> OperationPreflight:
    profile = GITHUB_PREFLIGHT_PROFILE
    op = operation_type
    blockers = mutation_blockers(op, message=profile.mutation_blocker_message)

    if resolution.status == "ambiguous":
        return build_ambiguous_target_preflight(profile, operation_type=op, resolution=resolution)

    target = resolution.target_name
    if resolution.status != "resolved" or not target:
        return build_missing_target_preflight(profile, operation_type=op, resolution=resolution)

    return build_api_readonly_resolved_preflight(
        profile,
        operation_type=op,
        target=target,
        user_request=user_request,
        proposed_steps=_github_proposed_steps(target=target, operation_type=op),
        blockers=blockers,
    )


def format_preflight_report(preflight: OperationPreflight, *, user_request: str = "") -> str:
    return format_api_provider_preflight_report(
        preflight,
        user_request=user_request,
        provider_title=GITHUB_PREFLIGHT_PROFILE.provider_title,
    )
