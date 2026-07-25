# SPDX-License-Identifier: Apache-2.0
"""Provider tool registry — dynamic capability inventory for the execution brain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProviderName = Literal["railway", "vercel"]
ToolTier = Literal["readonly", "preflight", "mutation"]


@dataclass(frozen=True)
class ProviderTool:
    tool_id: str
    provider: ProviderName
    label: str
    tier: ToolTier
    description: str
    requires_approval: bool = False


_RAILWAY_TOOLS: tuple[ProviderTool, ...] = (
    ProviderTool("railway.validate_token", "railway", "Validate Railway token", "readonly", "Test Railway API connection."),
    ProviderTool("railway.discover_projects", "railway", "Discover projects", "readonly", "List Railway projects and environments."),
    ProviderTool("railway.discover_services", "railway", "Discover services", "readonly", "Resolve target service for deployment."),
    ProviderTool("railway.check_env_readiness", "railway", "Check env readiness", "readonly", "Assess required env vars without showing values."),
    ProviderTool("railway.create_deploy_preflight", "railway", "Create deploy preflight", "preflight", "Create governed E2E orchestration job.", requires_approval=True),
    ProviderTool("railway.redeploy", "railway", "Redeploy service", "mutation", "Governed redeploy of existing service.", requires_approval=True),
    ProviderTool("railway.set_env_var", "railway", "Set env var", "mutation", "Governed env var write.", requires_approval=True),
    ProviderTool("railway.fetch_logs", "railway", "Fetch logs", "readonly", "Read deployment logs for diagnosis."),
    ProviderTool("railway.verify_deployment", "railway", "Verify deployment", "readonly", "Poll deployment status and health URL."),
)

_VERCEL_TOOLS: tuple[ProviderTool, ...] = (
    ProviderTool("vercel.validate_token", "vercel", "Validate Vercel token", "readonly", "Test Vercel API connection."),
    ProviderTool("vercel.discover_projects", "vercel", "Discover projects", "readonly", "List Vercel projects."),
    ProviderTool("vercel.check_env_readiness", "vercel", "Check env readiness", "readonly", "Assess env var keys without values."),
    ProviderTool("vercel.create_deploy_preflight", "vercel", "Create deploy preflight", "preflight", "Create governed E2E orchestration job.", requires_approval=True),
    ProviderTool("vercel.redeploy", "vercel", "Redeploy project", "mutation", "Governed production redeploy.", requires_approval=True),
    ProviderTool("vercel.verify_deployment", "vercel", "Verify deployment", "readonly", "Check deployment URL and status."),
)


def list_provider_tools(provider: ProviderName) -> list[ProviderTool]:
    if provider == "railway":
        return list(_RAILWAY_TOOLS)
    return list(_VERCEL_TOOLS)


def get_tool(tool_id: str) -> ProviderTool | None:
    for tool in (*_RAILWAY_TOOLS, *_VERCEL_TOOLS):
        if tool.tool_id == tool_id:
            return tool
    return None


def tools_for_goal(*, provider: ProviderName, requires_env: bool, requires_verify: bool) -> list[str]:
    """Ordered tool ids for a deploy goal."""
    if provider == "railway":
        steps = [
            "railway.validate_token",
            "railway.discover_projects",
            "railway.discover_services",
        ]
        if requires_env:
            steps.append("railway.check_env_readiness")
        steps.append("railway.create_deploy_preflight")
        if requires_verify:
            steps.append("railway.verify_deployment")
        return steps
    steps = ["vercel.validate_token", "vercel.discover_projects"]
    if requires_env:
        steps.append("vercel.check_env_readiness")
    steps.append("vercel.create_deploy_preflight")
    if requires_verify:
        steps.append("vercel.verify_deployment")
    return steps


def capability_summary(provider: ProviderName) -> str:
    tools = list_provider_tools(provider)
    readonly = [t.label for t in tools if t.tier == "readonly"]
    governed = [t.label for t in tools if t.tier in {"preflight", "mutation"}]
    return (
        f"**{provider.title()} capabilities available to the execution brain:**\n"
        f"- Readonly: {', '.join(readonly)}\n"
        f"- Governed (approval required): {', '.join(governed)}"
    )
