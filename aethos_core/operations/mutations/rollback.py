# SPDX-License-Identifier: Apache-2.0
"""Rollback contract model — plan-only in Phase 9.6."""

from __future__ import annotations

from typing import Any


def rollback_plan_for_operation(*, provider: str, operation_type: str, **context: Any) -> dict[str, Any]:
    plans: dict[tuple[str, str], dict[str, Any]] = {
        ("railway", "redeploy"): {
            "reversible": True,
            "strategy": "Redeploy prior deployment if provider API supports promotion.",
            "verification": "readonly_execution list_deployments",
        },
        ("railway", "restart"): {
            "reversible": True,
            "strategy": "Redeploy prior deployment or trigger another restart if service remains unhealthy.",
            "verification": "readonly_execution list_deployments",
            "previous_deployment_reference": "latest_deployment_before_restart",
            "recovery_action": "Redeploy last successful deployment or repeat restart after verification.",
        },
        ("railway", "set_env_var"): {
            "reversible": True,
            "strategy": "Restore prior env value if captured in before-state.",
            "verification": "readonly_execution project_details",
        },
        ("vercel", "redeploy"): {
            "reversible": True,
            "strategy": "Promote previous production deployment.",
            "verification": "readonly_execution list_deployments",
        },
        ("github", "workflow_rerun"): {
            "reversible": False,
            "strategy": "New workflow run; prior run history preserved.",
            "verification": "readonly_execution workflow_runs",
        },
    }
    key = (provider, operation_type)
    if key in plans:
        plan = dict(plans[key])
        if provider == "railway" and operation_type == "restart":
            dep_id = context.get("deployment_id")
            dep_state = context.get("deployment_state")
            if dep_id:
                plan["previous_deployment_reference"] = dep_id
            if dep_state:
                plan["previous_deployment_state"] = dep_state
            if context.get("deployment_created_at"):
                plan["previous_deployment_timestamp"] = context.get("deployment_created_at")
        return plan
    return {
        "reversible": False,
        "strategy": "Rollback plan not defined for this operation yet.",
        "verification": "readonly_execution post-check when available",
    }
