# SPDX-License-Identifier: Apache-2.0
"""First-run capability overview for personal introduction onboarding."""

from __future__ import annotations

# Canonical locked beta-smoke stages — README and onboarding bullets stay synced to this tuple.
LOCKED_BETA_SMOKE_STAGE_IDS: tuple[str, ...] = (
    "foundation_single_loop",
    "chat_basic_qa",
    "canvas_structured_render",
    "telegram_real_errors",
    "channel_health_routing",
    "railway_readonly_direct",
    "provider_inventory_health",
    "repo_analysis",
    "arbiter_consensus",
    "deploy_end_to_end",
    "engineering_review",
    "model_selection_and_failover",
    "tenant_owner_can_approve",
    "deploy_routes_to_deploy",
    "cross_provider_failover",
)

_STAGE_BULLETS: dict[str, str] = {
    "foundation_single_loop": (
        "One model-driven chat loop with governed mutation gates — questions never become deploy targets"
    ),
    "chat_basic_qa": (
        "Summarize URLs and follow up from conversation memory without canned help blurbs"
    ),
    "canvas_structured_render": (
        "Render structured operational views to the live Canvas panel"
    ),
    "telegram_real_errors": (
        "Send Telegram messages with real transport errors surfaced (no generic failure literals)"
    ),
    "channel_health_routing": (
        "Diagnose channel health (Telegram webhook, tokens) before workspace or repo commands"
    ),
    "railway_readonly_direct": (
        "Run Railway read-only deployment and inventory checks directly — no preflight job"
    ),
    "provider_inventory_health": (
        "List provider inventory with live health tables across every connected cloud"
    ),
    "repo_analysis": (
        "Analyze connected GitHub repositories via API — no local workspace registration required"
    ),
    "arbiter_consensus": (
        "Run multi-model arbiter consensus when at least two models are configured"
    ),
    "deploy_end_to_end": (
        "Check deploy readiness directly; route deploy mutations through approval with the right provider tool"
    ),
    "engineering_review": (
        "Review connected repo structure, dependencies, and CI workflows via GitHub API"
    ),
    "model_selection_and_failover": (
        "Honor the selected model for agent turns and fail over across providers on hard errors"
    ),
    "tenant_owner_can_approve": (
        "Each tenant owner can approve pairings and run their tenant without platform-owner env"
    ),
    "deploy_routes_to_deploy": (
        "Deploy requests route to governed deploy flow — not the Railway read-only lane"
    ),
    "cross_provider_failover": (
        "LLM failover crosses distinct providers (registry + vault), not just models on one provider"
    ),
}


def locked_beta_smoke_stage_ids() -> tuple[str, ...]:
    return LOCKED_BETA_SMOKE_STAGE_IDS


def onboarding_capability_bullets() -> list[str]:
    return [_STAGE_BULLETS[stage_id] for stage_id in LOCKED_BETA_SMOKE_STAGE_IDS]


def compose_onboarding_welcome_text() -> str:
    from aethos_core.production.deployment_mode import is_hosted_deployment

    lines = [
        "I'm **AethOS** — your operational intelligence partner on the control plane.",
        "",
        "Here's what I can help you with:",
        "",
    ]
    for item in onboarding_capability_bullets():
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Cloud-specific powers unlock once you connect providers in **Connections**.",
        ]
    )
    if is_hosted_deployment():
        lines.extend(
            [
                "",
                "On this hosted deployment I analyze code from **connected GitHub repositories** "
                "(not files on your laptop). Link repos under **Repositories** in Mission Control.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "On your machine I can also read **local workspaces** you register in Mission Control.",
            ]
        )
    return "\n".join(lines)
