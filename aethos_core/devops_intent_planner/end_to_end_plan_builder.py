# SPDX-License-Identifier: Apache-2.0
"""End-to-end DevOps plan builder — plan-first before mutation preflight."""

from __future__ import annotations

from typing import Any

from aethos_core.capability_truth.adapter_readiness import check_adapter_readiness
from aethos_core.capability_truth.provider_capability_matrix import provider_display_label
from aethos_core.devops_intent_planner.devops_request_classifier import count_devops_actions, detect_requested_providers
from aethos_core.devops_intent_planner.provider_specific_plan_builder import (
    compose_provider_specific_e2e_plan_reply,
    should_use_provider_specific_plan,
)

_PLAN_STEPS: tuple[str, ...] = (
    "Inspect the local repo/workspace context",
    "Check git status, branch, and remotes",
    "Verify the target cloud/provider and environment",
    "Identify required env vars and secrets",
    "Prepare a governed push/deploy/env mutation plan",
    "Ask for approval before any mutation",
    "Verify deployment, logs, and health after execution",
)


def build_end_to_end_plan(text: str, *, session_id: str = "default") -> dict[str, Any]:
    if should_use_provider_specific_plan(text):
        from aethos_core.devops_intent_planner.provider_specific_plan_builder import build_provider_specific_e2e_plan

        return build_provider_specific_e2e_plan(text, session_id=session_id)

    providers = detect_requested_providers(text)
    actions = count_devops_actions(text)
    readiness = {provider: check_adapter_readiness(provider) for provider in providers}
    return {
        "session_id": session_id,
        "requested_actions": actions,
        "providers": providers,
        "steps": list(_PLAN_STEPS),
        "readiness": {
            provider: {
                "registered": status.registered,
                "credentials_configured": status.credentials_configured,
                "e2e_ready": status.e2e_ready,
                "tier": status.tier,
            }
            for provider, status in readiness.items()
        },
        "needs_clarification": [
            "local repo path or workspace root",
            "target provider (Railway is deepest today; GitHub/Vercel expanding)",
            "environment/project/service names",
            "approval scope for push/deploy/env mutations",
        ],
    }


def compose_end_to_end_plan_reply(text: str, *, session_id: str = "default") -> str:
    if should_use_provider_specific_plan(text):
        return compose_provider_specific_e2e_plan_reply(text, session_id=session_id)

    plan = build_end_to_end_plan(text, session_id=session_id)
    providers = plan["providers"]
    lines = [
        "I can help plan and, where configured, execute this through governed steps.",
        "",
        "Proposed end-to-end workflow:",
    ]
    for idx, step in enumerate(_PLAN_STEPS, start=1):
        lines.append(f"{idx}. {step}")

    if providers:
        lines.extend(["", "Requested providers — honest readiness:"])
        for provider in providers:
            status = check_adapter_readiness(provider)
            label = provider_display_label(provider)
            if status.e2e_ready:
                detail = "configured and E2E-capable for wired operations"
            elif status.registered:
                detail = f"{status.tier} adapter; not full push/deploy/env E2E"
            else:
                detail = f"{status.tier} only — not fully implemented"
            lines.append(f"- **{label}**: {detail}")
    else:
        lines.extend(
            [
                "",
                "Provider note: **Railway** is the deepest working cloud path today. "
                "**GitHub** and **Vercel** are expanding; AWS/GCP/Azure/K8s are stub or planned unless configured otherwise.",
            ]
        )

    lines.extend(
        [
            "",
            "Before I create any mutation preflight, I need:",
        ]
    )
    for item in plan["needs_clarification"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "Once those are clear, I can prepare governed preflights for the specific mutation steps you approve.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)
