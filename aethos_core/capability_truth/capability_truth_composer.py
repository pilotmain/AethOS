# SPDX-License-Identifier: Apache-2.0
"""Capability truth composer — honest chat answers about provider maturity."""

from __future__ import annotations

import re

from aethos_core.capability_truth.adapter_readiness import check_adapter_readiness, get_configured_operational_providers
from aethos_core.capability_truth.provider_capability_matrix import list_provider_summaries, provider_display_label, provider_truth_line, providers_with_e2e_readiness

_E2E_TODAY_RX = re.compile(
    r"\b("
    r"which\s+(?:cloud(?:\s+env|\s+environment)?|provider|providers)"
    r"|work\s+(?:end[\s-]to[\s-]end|e2e)\s+today"
    r"|end[\s-]to[\s-]end\s+today"
    r"|most\s+complete\s+(?:provider|cloud)"
    r")\b",
    re.I,
)


def compose_capability_truth_reply(text: str = "") -> str:
    if _E2E_TODAY_RX.search(text or ""):
        return compose_e2e_provider_answer()
    return compose_general_capabilities_reply()


def compose_e2e_provider_answer() -> str:
    e2e = providers_with_e2e_readiness()
    configured = get_configured_operational_providers()
    lines = [
        "**Railway is the most complete cloud provider I can work end to end today.**",
        "",
        "Honest provider maturity:",
    ]
    for summary in list_provider_summaries():
        lines.append(provider_truth_line(summary))

    if configured:
        names = ", ".join(f"**{provider_display_label(item.provider)}**" for item in configured)
        lines.extend(
            [
                "",
                f"Configured adapters detected: {names}.",
                "I can still plan workflows for other providers, but I should verify adapter + credentials before claiming execution.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "No cloud credentials are configured in this runtime yet — I can plan workflows, "
                "but governed execution requires verified provider credentials.",
            ]
        )

    if not e2e:
        lines.append("")
        lines.append("No provider is fully E2E-ready without configured credentials.")

    lines.extend(
        [
            "",
            "I can plan multi-step DevOps workflows, but mutations still require explicit target clarification and approval.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def compose_general_capabilities_reply() -> str:
    lines = [
        "I can help with governed operational work, but I should stay honest about what is fully wired today:",
        "",
        "Provider maturity:",
    ]
    for summary in list_provider_summaries():
        lines.append(provider_truth_line(summary))

    lines.extend(
        [
            "",
            "Platform strengths:",
            "- Failed-service investigation, evidence correlation, and repair learning",
            "- Governed mutations with preflight + approval for wired provider operations",
            "- Mission Control jobs, verification, and investigation continuity",
            "",
            "For production-impacting actions I create a governed preflight only after target repo/provider/env/action are clear.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def compose_unimplemented_provider_gap(provider: str) -> str:
    status = check_adapter_readiness(provider)
    summary_line = ""
    from aethos_core.capability_truth.provider_capability_matrix import get_provider_summary

    summary = get_provider_summary(provider)
    if summary:
        summary_line = summary.honest_summary
    label = summary.label if summary else provider_display_label(provider)
    lines = [
        f"**{label}** is not a fully wired execution path in AethOS today.",
        "",
        summary_line or "This provider adapter is stubbed or planned only.",
    ]
    if status.notes:
        lines.extend(["", "Current gaps:"])
        for note in status.notes[:4]:
            lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "I can still help plan the workflow and identify what would need to be configured first.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)
