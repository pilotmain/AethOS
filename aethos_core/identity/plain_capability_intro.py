# SPDX-License-Identifier: Apache-2.0
"""Plain-language capability intros for non-technical users."""

from __future__ import annotations

import re

from aethos_core.capability_truth.adapter_readiness import get_configured_operational_providers
from aethos_core.capability_truth.provider_capability_matrix import provider_display_label

_PROVIDER_CONNECTION_RX = re.compile(
    r"\b("
    r"what\s+providers?\s+(?:are\s+)?connected"
    r"|which\s+providers?\s+(?:are\s+)?connected"
    r"|show\s+provider\s+connections?"
    r"|provider\s+connection\s+status"
    r"|what(?:'s| is)\s+connected"
    r"|connected\s+providers?"
    r")\b",
    re.I,
)


def is_provider_connection_question(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_PROVIDER_CONNECTION_RX.search(raw))


def compose_plain_capability_overview_reply(*, session_id: str = "default") -> str:
    """Human-friendly overview — what AethOS does for the user, not internal config status."""
    from aethos_core.onboarding.operator_persona import persona_greeting_name

    name = persona_greeting_name()
    opener = f"Hi {name} — " if name else ""

    lines = [
        f"{opener}I'm **AethOS**, your operational intelligence partner. "
        "Here's what I can help you with:",
        "",
        "- **Chat and research** — discuss topics and look things up with sources "
        "(add your own search key in **Connections** if you want live web search)",
        "- **Investigate and explain** — what's happening in your systems, logs, deployments, and failures",
        "- **Deploy and manage apps** — prepare governed actions; anything consequential needs your approval",
        "- **Compare AI models** — run answers through multiple models and see where they agree",
        "- **Workspace, canvas, and memory** — organize notes, docs, and context across your work",
        "- **Automate routine checks** — scheduled, governed automations that keep you informed",
        "",
        "You're always in control of anything that changes production.",
    ]

    configured = get_configured_operational_providers()
    if configured:
        labels = ", ".join(f"**{provider_display_label(item.provider)}**" for item in configured)
        lines.extend(
            [
                "",
                f"You already have {labels} connected — I can inspect and operate there too, still with your approval.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "If you connect cloud providers in **Connections** (Railway, Vercel, GitHub, and others), "
                "I can also inspect and help manage apps there — still with your approval.",
            ]
        )

    lines.append("")
    lines.append("Ask me anything you're working on — I'm here to help.")
    return "\n".join(lines)


def compose_provider_connection_status_reply(*, session_id: str = "default") -> str:
    """Explicit provider-connection question — honest readiness, not a general capability dump."""
    from aethos_core.capability_truth.capability_truth_composer import compose_e2e_provider_answer
    from aethos_core.onboarding.operator_persona import persona_greeting_name

    name = persona_greeting_name()
    prefix = f"Hi {name} — " if name else ""
    body = compose_e2e_provider_answer()
    if prefix:
        return prefix + "\n\n" + body
    return body
