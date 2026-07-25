# SPDX-License-Identifier: Apache-2.0
"""Provider selection for operational queries."""

from __future__ import annotations

from aethos_core.operational_planner.scope_classifier import explicit_provider_in_prompt


def select_provider(text: str, *, session_id: str = "default", scope: str = "unknown") -> str | None:
    explicit = explicit_provider_in_prompt(text)
    if explicit:
        return explicit

    if scope == "active_target":
        from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

        thread = get_active_operational_thread(session_id)
        if thread is not None:
            return str(getattr(thread, "provider", "") or "railway")

    from aethos_core.continuity_intelligence.operational_focus_model import get_operational_focus

    focus = get_operational_focus(session_id=session_id)
    if focus.get("provider"):
        return str(focus.get("provider"))

    lower = (text or "").lower()
    if "railway" in lower:
        return "railway"
    if "vercel" in lower:
        return "vercel"
    if "github" in lower:
        return "github"
    if "docker" in lower:
        return "docker"
    if "kubernetes" in lower or "k8s" in lower:
        return "kubernetes"
    if "aws" in lower:
        return "aws"

    if scope in {"provider_wide", "provider_service"}:
        return "railway"
    return None
