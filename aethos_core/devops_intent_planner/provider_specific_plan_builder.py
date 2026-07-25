# SPDX-License-Identifier: Apache-2.0
"""Provider-specific end-to-end DevOps plan builder."""

from __future__ import annotations

from typing import Any

from aethos_core.capability_truth.adapter_readiness import check_adapter_readiness
from aethos_core.capability_truth.provider_capability_matrix import get_provider_summary, provider_display_label
from aethos_core.devops_intent_planner.devops_request_classifier import count_devops_actions, detect_requested_providers
from aethos_core.providers.github.expansion.capability_registry import github_expansion_summary
from aethos_core.providers.vercel.expansion.capability_registry import vercel_expansion_summary

_PROVIDER_SPECIFIC_STEPS: tuple[str, ...] = (
    "Identify the local repo path / workspace root",
    "Inspect git status, branch, and remotes",
    "Choose branch strategy (feature branch vs direct deploy branch)",
    "Identify the target GitHub repository",
    "Identify the deploy provider (Vercel, Railway, or other)",
    "Validate the env var list (names/targets only — no secret values in chat)",
    "Prepare a governed mutation plan (push, deploy, env changes) with approval gates",
    "Execute only after explicit approval in Mission Control",
    "Verify GitHub checks / workflow status",
    "Verify deployment health, logs, and domain availability",
)


def should_use_provider_specific_plan(text: str) -> bool:
    providers = detect_requested_providers(text)
    if "github" in providers or "vercel" in providers:
        return True
    return count_devops_actions(text) >= 2


def build_provider_specific_e2e_plan(text: str, *, session_id: str = "default") -> dict[str, Any]:
    providers = detect_requested_providers(text) or ["github", "vercel"]
    readiness = {provider: check_adapter_readiness(provider) for provider in providers}
    return {
        "session_id": session_id,
        "providers": providers,
        "steps": list(_PROVIDER_SPECIFIC_STEPS),
        "readiness": readiness,
        "github_expansion": github_expansion_summary(),
        "vercel_expansion": vercel_expansion_summary(),
        "needs_clarification": [
            "local repo path",
            "GitHub owner/repo (or confirm from git remote)",
            "deploy target provider and project/service name",
            "environment names (production/preview/etc.)",
            "env var keys to create or update",
            "approval scope for each mutation step",
        ],
    }


def _expansion_detail(provider: str) -> str:
    summary = get_provider_summary(provider)
    status = check_adapter_readiness(provider)
    if summary is None:
        return f"{provider_display_label(provider)} adapter status unknown"
    tier = summary.tier.upper()
    if status.e2e_ready:
        return f"{summary.label} ({tier}) — configured and E2E-capable for wired operations"
    if summary.tier == "expanding":
        return f"{summary.label} ({tier}) — readonly + governed ops expanding; mutations require approval and explicit targets"
    return f"{summary.label} ({tier}) — not full push/deploy/env E2E yet"


def compose_provider_specific_e2e_plan_reply(text: str, *, session_id: str = "default") -> str:
    plan = build_provider_specific_e2e_plan(text, session_id=session_id)
    providers = plan["providers"]
    lines = [
        "I can help plan and, where configured, execute this through governed GitHub + deploy-provider steps.",
        "",
        "Provider-specific end-to-end workflow:",
    ]
    for idx, step in enumerate(_PROVIDER_SPECIFIC_STEPS, start=1):
        lines.append(f"{idx}. {step}")

    lines.extend(["", "Provider readiness (honest):"])
    for provider in providers:
        lines.append(f"- **{provider_display_label(provider)}**: {_expansion_detail(provider)}")

    github = plan["github_expansion"]
    vercel = plan["vercel_expansion"]
    if "github" in providers:
        lines.extend(
            [
                "",
                "GitHub wired now:",
                f"- readonly: {', '.join(github['readonly_wired'][:6])}",
                f"- mutations wired: {', '.join(github['mutations_wired']) or 'none yet'}",
                f"- expanding next: {', '.join(github['expanding'][:5])}",
            ]
        )
    if "vercel" in providers:
        lines.extend(
            [
                "",
                "Vercel wired now:",
                f"- readonly: {', '.join(vercel['readonly_wired'][:6])}",
                f"- mutations wired: {', '.join(vercel['mutations_wired']) or 'none yet'}",
                f"- expanding next: {', '.join(vercel['expanding'][:5])}",
            ]
        )

    lines.extend(["", "Before any mutation preflight, I need:"])
    for item in plan["needs_clarification"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "Priority order: deepen **GitHub** first, then **Vercel**, before AWS/GCP/Azure expansion.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)
