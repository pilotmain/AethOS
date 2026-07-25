# SPDX-License-Identifier: Apache-2.0
"""Run operation preflight jobs — read-only planning layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.preflight_summary import chat_summary_for_preflight
from aethos_core.operations.target_resolution import resolve_vercel_target
from aethos_core.operations.orchestration.job_taxonomy import resolve_preflight_provider
from aethos_core.operations.orchestration.preflight_builder import format_api_provider_preflight_report
from aethos_core.operations.vercel_preflight import (
    build_vercel_preflight,
    format_preflight_report,
)


@dataclass
class PreflightOutcome:
    preflight: OperationPreflight
    summary: str
    preview: str
    full_result: str


def refresh_preflight_report(preflight: OperationPreflight, *, user_request: str = "") -> str:
    if preflight.provider == "railway":
        return format_api_provider_preflight_report(
            preflight,
            user_request=user_request,
            provider_title="Railway",
        )
    if preflight.provider == "github":
        return format_api_provider_preflight_report(
            preflight,
            user_request=user_request,
            provider_title="GitHub",
        )
    return format_preflight_report(preflight, user_request=user_request)


def run_operation_preflight(
    *,
    job_type: str,
    params: dict[str, Any],
) -> PreflightOutcome:
    user_request = str(params.get("user_request") or "")
    provider = resolve_preflight_provider(job_type, params)
    operation_type = str(params.get("operation_type") or job_type)
    hints = list(params.get("target_hints") or [])

    if provider == "local":
        from aethos_core.operations.local_preflight import build_local_preflight

        preflight = build_local_preflight(operation_type=operation_type, user_request=user_request)
    elif provider == "railway":
        from aethos_core.operations.railway_preflight import build_railway_preflight
        from aethos_core.operations.railway_preflight import format_preflight_report as format_railway_preflight_report
        from aethos_core.operations.railway_target_resolution import resolve_railway_target

        resolution = resolve_railway_target(
            user_request=user_request,
            target_hints=hints,
            operation_type=operation_type,
        )
        preflight = build_railway_preflight(
            operation_type=operation_type,
            resolution=resolution,
            user_request=user_request,
        )
        from aethos_core.operations.execution_status import enrich_preflight_execution_metadata
        from aethos_core.operations.preflight_status import derive_preflight_status

        preflight.preflight_status = derive_preflight_status(preflight)
        enrich_preflight_execution_metadata(preflight)
        full = format_railway_preflight_report(preflight, user_request=user_request)
        summary = chat_summary_for_preflight(preflight, user_request=user_request)
        preview = summary.split("\n")[0][:240]
        return PreflightOutcome(preflight=preflight, summary=summary, preview=preview, full_result=full)
    elif provider == "github":
        from aethos_core.operations.github_preflight import build_github_preflight
        from aethos_core.operations.github_preflight import format_preflight_report as format_github_preflight_report
        from aethos_core.operations.github_target_resolution import resolve_github_target

        resolution = resolve_github_target(
            user_request=user_request,
            target_hints=hints,
            operation_type=operation_type,
        )
        preflight = build_github_preflight(
            operation_type=operation_type,
            resolution=resolution,
            user_request=user_request,
        )
        from aethos_core.operations.execution_status import enrich_preflight_execution_metadata
        from aethos_core.operations.preflight_status import derive_preflight_status

        preflight.preflight_status = derive_preflight_status(preflight)
        enrich_preflight_execution_metadata(preflight)
        full = format_github_preflight_report(preflight, user_request=user_request)
        summary = chat_summary_for_preflight(preflight, user_request=user_request)
        preview = summary.split("\n")[0][:240]
        return PreflightOutcome(preflight=preflight, summary=summary, preview=preview, full_result=full)
    elif provider in ("vercel", "unknown"):
        resolution = resolve_vercel_target(
            user_request=user_request,
            target_hints=hints,
            operation_type=operation_type,
        )
        preflight = build_vercel_preflight(
            operation_type=operation_type,
            resolution=resolution,
            user_request=user_request,
        )
    else:
        preflight = OperationPreflight(
            provider=provider,
            operation_type=operation_type,
            target_name=None,
            target_status="planned",
            risk_level="low",
            mutation_required=False,
            proposed_steps=[
                f"{provider.title()} support is planned.",
                "This preflight records your request for a future phase.",
            ],
            blockers=["Provider operations not implemented yet."],
            next_action="provider_planned",
        )

    from aethos_core.operations.execution_status import enrich_preflight_execution_metadata
    from aethos_core.operations.preflight_status import derive_preflight_status

    preflight.preflight_status = derive_preflight_status(preflight)
    enrich_preflight_execution_metadata(preflight)

    full = format_preflight_report(preflight, user_request=user_request)
    summary = chat_summary_for_preflight(preflight, user_request=user_request)
    preview = summary.split("\n")[0][:240]
    return PreflightOutcome(preflight=preflight, summary=summary, preview=preview, full_result=full)
