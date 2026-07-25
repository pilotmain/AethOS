# SPDX-License-Identifier: Apache-2.0
"""Shared readonly preflight builder — Phase 9.3M Slice D."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.connections.auth_labels import auth_method_label_for_provider
from aethos_core.operations.execution.execution_permissions import is_mutating_operation
from aethos_core.operations.execution_status import execution_status_lines, safety_footer
from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.orchestration.registry_runtime import preflight_capability_metadata
from aethos_core.operations.target_resolution import TargetResolution


@dataclass(frozen=True)
class ApiProviderPreflightProfile:
    """Provider-specific preflight copy — semantics stay at the adapter edge."""

    provider: str
    provider_title: str
    missing_information_ambiguous: str
    missing_information_unresolved: str
    ambiguous_step: str
    missing_configure_steps: tuple[str, ...]
    missing_blocker_default: str
    mutation_blocker_message: str = "Mutating operations remain disabled."


def mutation_blockers(operation_type: str, *, message: str) -> list[str]:
    if is_mutating_operation(operation_type):
        return [message]
    return []


def build_ambiguous_target_preflight(
    profile: ApiProviderPreflightProfile,
    *,
    operation_type: str,
    resolution: TargetResolution,
) -> OperationPreflight:
    return OperationPreflight(
        provider=profile.provider,
        operation_type=operation_type,
        target_name=None,
        target_status="ambiguous",
        risk_level="low",
        mutation_required=False,
        required_approval=False,
        current_state={"matches": resolution.matches},
        proposed_steps=[profile.ambiguous_step],
        blockers=[],
        missing_information=[profile.missing_information_ambiguous],
        next_action="clarify_target",
    )


def build_missing_target_preflight(
    profile: ApiProviderPreflightProfile,
    *,
    operation_type: str,
    resolution: TargetResolution,
) -> OperationPreflight:
    target = resolution.target_name
    return OperationPreflight(
        provider=profile.provider,
        operation_type=operation_type,
        target_name=target,
        target_status="missing",
        risk_level="low",
        mutation_required=False,
        required_approval=True,
        current_state={"resolution_message": resolution.message, "matches": resolution.matches},
        proposed_steps=list(profile.missing_configure_steps),
        blockers=[resolution.message or profile.missing_blocker_default],
        missing_information=[profile.missing_information_unresolved],
        next_action="configure_provider",
    )


def build_api_readonly_resolved_preflight(
    profile: ApiProviderPreflightProfile,
    *,
    operation_type: str,
    target: str,
    user_request: str,
    proposed_steps: list[str],
    blockers: list[str] | None = None,
) -> OperationPreflight:
    cap = preflight_capability_metadata(profile.provider, operation_type)
    return OperationPreflight(
        provider=profile.provider,
        operation_type=operation_type,
        target_name=target,
        target_status="resolved",
        risk_level="low",
        mutation_required=False,
        required_approval=True,
        current_state={**cap, "user_request": user_request},
        proposed_steps=proposed_steps,
        blockers=list(blockers or []),
        missing_information=[],
        next_action="approve_readonly_execution",
    )


def format_api_provider_preflight_report(
    preflight: OperationPreflight,
    *,
    user_request: str = "",
    provider_title: str,
) -> str:
    lines = [
        f"# {provider_title} preflight — {preflight.operation_type.replace('_', ' ')}",
        "",
        f"**Target:** `{preflight.target_name or '—'}` · **Status:** {preflight.target_status}",
        "",
    ]
    cap = preflight.current_state or {}
    if cap.get("api_capable"):
        method = str(cap.get("auth_method") or "api_token")
        label = str(cap.get("auth_method_label") or "") or auth_method_label_for_provider(
            preflight.provider, method
        )
        lines.extend([f"**Auth path:** {label} · **Browser required:** no", ""])
    lines.extend(["## Proposed steps"])
    for step in preflight.proposed_steps:
        lines.append(f"- {step}")
    if preflight.blockers:
        lines.extend(["", "## Blockers"])
        for blocker in preflight.blockers:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Execution status", *execution_status_lines(preflight), "", safety_footer(preflight)])
    if user_request:
        lines.extend(["", f"_Request:_ {user_request[:500]}"])
    return "\n".join(lines)


RAILWAY_PREFLIGHT_PROFILE = ApiProviderPreflightProfile(
    provider="railway",
    provider_title="Railway",
    missing_information_ambiguous="target_service",
    missing_information_unresolved="target_service",
    ambiguous_step="Clarify which Railway service you mean.",
    missing_configure_steps=(
        "Configure Railway API token in Mission Control.",
        "Retry with an explicit service name.",
    ),
    missing_blocker_default="Target service could not be resolved.",
)

GITHUB_PREFLIGHT_PROFILE = ApiProviderPreflightProfile(
    provider="github",
    provider_title="GitHub",
    missing_information_ambiguous="target_repository",
    missing_information_unresolved="target_repository",
    ambiguous_step="Clarify which GitHub repository you mean.",
    missing_configure_steps=(
        "Configure GitHub API token in Mission Control.",
        "Retry with an explicit repository name or owner/repo.",
    ),
    missing_blocker_default="Target repository could not be resolved.",
)
