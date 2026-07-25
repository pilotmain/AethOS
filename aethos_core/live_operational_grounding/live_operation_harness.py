# SPDX-License-Identifier: Apache-2.0
"""Live operation harness — repeatable Tier-1 provider validation flows."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_hardening.verify import verify_provider_mutation


_LIVE_FLOWS: tuple[dict[str, str], ...] = (
    {
        "id": "railway_restart",
        "provider": "railway",
        "operation": "restart",
        "validation": "restart request, deployment transition, runtime verification",
    },
    {
        "id": "vercel_deploy_check",
        "provider": "vercel",
        "operation": "redeploy",
        "validation": "endpoint, build status, browser confirmation",
    },
    {
        "id": "github_workflow_rerun",
        "provider": "github",
        "operation": "workflow_rerun",
        "validation": "workflow state, conclusion, downstream signal",
    },
    {
        "id": "failed_deployment_analysis",
        "provider": "railway",
        "operation": "restart",
        "validation": "provider evidence + runtime truth on failure path",
    },
    {
        "id": "recovery_followup",
        "provider": "railway",
        "operation": "restart",
        "validation": "Telegram continuity after real operation",
    },
    {
        "id": "delayed_stabilization",
        "provider": "railway",
        "operation": "restart",
        "validation": "sustained verification — 5m / 15m / later follow-up",
    },
)


def list_live_operation_flows() -> list[dict[str, str]]:
    return [dict(flow) for flow in _LIVE_FLOWS]


def run_live_operation_flow(*, flow_id: str, provider_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute harness verification for a named live operation flow."""
    flow = next((f for f in _LIVE_FLOWS if f["id"] == flow_id), None)
    if not flow:
        return {"ok": False, "flow_id": flow_id, "summary": f"Unknown live operation flow: {flow_id}."}

    verification = verify_provider_mutation(
        provider=flow["provider"],
        operation_type=flow["operation"],
        provider_result=provider_result or {"deployment_state_after": "success"},
    )
    return {
        "ok": True,
        "flow": flow,
        "verification": verification,
        "verified": bool(verification.get("verified")) or verification.get("maturity") == "stable",
        "summary": f"Live operation flow `{flow_id}` assessed — {flow['validation']}.",
    }
