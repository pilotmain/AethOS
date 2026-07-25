# SPDX-License-Identifier: Apache-2.0
"""Provider tool contracts — self-describing tools for the execution brain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ToolType = Literal["readonly", "preflight", "mutation"]


@dataclass(frozen=True)
class ProviderToolContract:
    tool_id: str
    provider: str
    tool_name: str
    tool_type: ToolType
    description: str
    required_inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    recovery_hints: tuple[str, ...] = ()
    requires_approval: bool = False


_CONTRACTS: dict[str, ProviderToolContract] = {}


def _register(contract: ProviderToolContract) -> ProviderToolContract:
    _CONTRACTS[contract.tool_id] = contract
    return contract


# Workspace / git (planning layer — provider-agnostic)
_register(
    ProviderToolContract(
        tool_id="local_workspace.discover",
        provider="workspace",
        tool_name="discover_workspace",
        tool_type="readonly",
        description="Discover local workspace portfolio and active repo roots.",
        required_inputs=("session_id",),
        outputs=("workspace_roots", "active_repo"),
        recovery_hints=("Set AETHOS_PORTFOLIO_ROOT", "Open project in registered workspace"),
    )
)
_register(
    ProviderToolContract(
        tool_id="git.resolve_remote",
        provider="github",
        tool_name="resolve_remote",
        tool_type="readonly",
        description="Resolve git remote slug for the active workspace.",
        required_inputs=("repo_root",),
        outputs=("remote_slug", "default_branch"),
        recovery_hints=("Ensure origin remote exists", "Name repo explicitly as org/repo"),
    )
)

# Railway
for _spec in (
    (
        "railway.validate_token",
        "validate_token",
        "readonly",
        ("credential_id",),
        ("connection_ok",),
        ("RAILWAY_TOKEN_MISSING", "RAILWAY_TOKEN_INVALID", "RAILWAY_RATE_LIMITED", "RAILWAY_API_CONNECTION_FAILED"),
        "Validate Railway API token.",
    ),
    (
        "railway.discover_projects",
        "discover_projects",
        "readonly",
        ("session_id",),
        ("projects", "services"),
        ("RAILWAY_INVENTORY_UNAVAILABLE",),
        "List Railway projects, environments, and services.",
    ),
    (
        "railway.discover_services",
        "discover_services",
        "readonly",
        ("project", "environment"),
        ("service",),
        ("RAILWAY_TARGET_SERVICE_MISSING",),
        "Resolve target Railway service.",
    ),
    (
        "railway.check_env_readiness",
        "check_env_readiness",
        "readonly",
        ("service",),
        ("env_keys", "missing_keys"),
        ("ENV_VAR_REFERENCE_MISSING",),
        "Assess required env var keys without values.",
    ),
    (
        "railway.fetch_logs",
        "fetch_logs",
        "readonly",
        ("service", "limit"),
        ("logs",),
        ("DEPLOYMENT_FAILED",),
        "Fetch deployment logs for diagnosis.",
    ),
    (
        "railway.verify_deployment",
        "verify_deployment",
        "readonly",
        ("service",),
        ("deployment_state", "health"),
        ("HEALTH_CHECK_FAILED",),
        "Poll deployment status and health.",
    ),
    (
        "railway.create_deploy_preflight",
        "create_deploy_preflight",
        "preflight",
        ("target", "env_plan"),
        ("job_id",),
        ("MUTATION_EXECUTION_DISABLED", "E2E_ORCHESTRATION_DISABLED"),
        "Create governed deploy preflight job.",
        True,
    ),
    (
        "railway.redeploy",
        "redeploy",
        "mutation",
        ("service",),
        ("deployment_id",),
        ("DEPLOYMENT_FAILED",),
        "Governed redeploy of existing service.",
        True,
    ),
):
    tool_id, name, tier, inputs, outputs, hints, desc = _spec[:7]
    approval = _spec[7] if len(_spec) > 7 else False
    _register(
        ProviderToolContract(
            tool_id=tool_id,
            provider="railway",
            tool_name=name,
            tool_type=tier,  # type: ignore[arg-type]
            description=desc,
            required_inputs=inputs,
            outputs=outputs,
            recovery_hints=hints,
            requires_approval=approval,
        )
    )

# Vercel
for _spec in (
    (
        "vercel.validate_token",
        "validate_token",
        "readonly",
        ("credential_id",),
        ("connection_ok",),
        ("VERCEL_TOKEN_MISSING", "VERCEL_TOKEN_INVALID"),
        "Validate Vercel API token.",
    ),
    (
        "vercel.discover_projects",
        "discover_projects",
        "readonly",
        ("session_id",),
        ("projects",),
        ("VERCEL_TOKEN_MISSING",),
        "List Vercel projects.",
    ),
    (
        "vercel.fetch_logs",
        "fetch_logs",
        "readonly",
        ("project", "limit"),
        ("logs",),
        ("VERCEL_TOKEN_MISSING",),
        "Fetch deployment log events.",
    ),
    (
        "vercel.verify_deployment",
        "verify_deployment",
        "readonly",
        ("project",),
        ("deployment_state",),
        ("HEALTH_CHECK_FAILED",),
        "Check latest deployment status.",
    ),
    (
        "vercel.create_deploy_preflight",
        "create_deploy_preflight",
        "preflight",
        ("project",),
        ("job_id",),
        ("MUTATION_EXECUTION_DISABLED",),
        "Create governed Vercel deploy preflight.",
        True,
    ),
):
    tool_id, name, tier, inputs, outputs, hints, desc = _spec[:7]
    approval = _spec[7] if len(_spec) > 7 else False
    _register(
        ProviderToolContract(
            tool_id=tool_id,
            provider="vercel",
            tool_name=name,
            tool_type=tier,  # type: ignore[arg-type]
            description=desc,
            required_inputs=inputs,
            outputs=outputs,
            recovery_hints=hints,
            requires_approval=approval,
        )
    )


def get_tool_contract(tool_id: str) -> ProviderToolContract | None:
    return _CONTRACTS.get(tool_id)


def list_tool_contracts(*, provider: str = "") -> list[ProviderToolContract]:
    rows = list(_CONTRACTS.values())
    if provider:
        rows = [row for row in rows if row.provider == provider]
    return rows


def recovery_hints_for_tool(tool_id: str) -> tuple[str, ...]:
    contract = get_tool_contract(tool_id)
    return contract.recovery_hints if contract else ()
