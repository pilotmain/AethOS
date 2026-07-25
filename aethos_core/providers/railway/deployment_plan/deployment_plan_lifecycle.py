# SPDX-License-Identifier: Apache-2.0
"""Deployment plan lifecycle resolution and blocker replies for preflight/simulator lanes."""

from __future__ import annotations

from typing import Any, Literal

from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
from aethos_core.providers.railway.deployment_plan.plan_review import is_plan_review_confirmed

PlanLifecycleState = Literal["no_plan", "unconfirmed", "confirmed_ready"]


def classify_deployment_plan_lifecycle_state(plan: dict[str, Any] | None) -> PlanLifecycleState:
    if not plan or not plan.get("repo"):
        return "no_plan"
    if not is_plan_review_confirmed(plan):
        return "unconfirmed"
    gate = assess_mutation_readiness_gate(plan)
    if not gate.get("mutation_ready"):
        return "unconfirmed"
    return "confirmed_ready"


def resolve_and_materialize_deployment_plan(
    *,
    session_id: str,
    user_text: str = "",
) -> dict[str, Any] | None:
    """Resolve plan via canonical deployment lifecycle store (auto-hydrates from global index)."""
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=user_text,
        require_plan=True,
    )
    plan = lane.plan
    return dict(plan) if plan and plan.get("repo") else None


def compose_no_plan_reply() -> str:
    return "\n".join(
        [
            "I don't have a saved Railway deployment plan in this session.",
            "",
            "Create one first:",
            "`create railway deployment plan for pilotmain/aethos in pilotos / production`",
            "`complete the railway deployment plan`",
            "`review railway deployment plan`",
            "`confirm railway deployment plan`",
            "",
            "Or diagnose session lifecycle state:",
            "`show railway deployment lifecycle`",
            "`repair railway deployment lifecycle`",
            "",
            "No mutation has been performed.",
        ]
    )


def compose_unconfirmed_plan_reply(*, plan: dict[str, Any]) -> str:
    repo = str(plan.get("repo") or "—")
    return "\n".join(
        [
            "I found a Railway deployment plan, but it is not confirmed yet.",
            "",
            f"Plan repo: `{repo}`",
            "",
            "Next step:",
            "`review railway deployment plan`",
            "`confirm railway deployment plan`",
            "",
            "No mutation has been performed.",
        ]
    )


def compose_missing_preflight_reply(*, plan: dict[str, Any]) -> str:
    repo = str(plan.get("repo") or "—")
    return "\n".join(
        [
            "I found the confirmed Railway deployment plan.",
            "",
            f"Plan repo: `{repo}`",
            "",
            "Next step:",
            "`create railway service creation preflight`",
            "",
            "No mutation has been performed.",
        ]
    )


def compose_preflight_not_ready_reply(*, blockers: list[str]) -> str:
    missing = ", ".join(blockers) if blockers else "plan prerequisites"
    return "\n".join(
        [
            "Cannot create a Railway service creation preflight yet.",
            "",
            f"Blocked until: {missing}",
            "",
            "Complete the deployment plan lifecycle first:",
            "`confirm railway deployment plan`",
            "",
            "No mutation has been performed.",
        ]
    )
