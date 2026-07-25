# SPDX-License-Identifier: Apache-2.0
"""Resolve provider context for provider-neutral operational follow-ups."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_EXPLICIT_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws)\b", re.I)
_PROVIDER_NEUTRAL_HEALTH_RX = re.compile(
    r"\b("
    r"check\s+(?:the\s+)?service\s+health"
    r"|service\s+health"
    r"|check\s+status"
    r"|check\s+(?:the\s+)?status"
    r"|what(?:'s| is)\s+the\s+status"
    r"|is\s+it\s+(?:healthy|running|up|online)"
    r"|health\s+check"
    r"|check\s+health"
    r"|verify\s+health"
    r")\b",
    re.I,
)
_PLATFORM_SYSTEM_HEALTH_RX = re.compile(
    r"\b("
    r"aethos\s+system\s+health"
    r"|platform\s+health"
    r"|your\s+health"
    r"|system\s+health\s+(?:of\s+)?aethos"
    r")\b",
    re.I,
)
_PROVIDER_NEUTRAL_LOGS_RX = re.compile(
    r"\b("
    r"check\s+(?:the\s+)?(?:top|latest|recent)?\s*\d*\s*logs?"
    r"|latest\s+logs?"
    r"|top\s+\d+\s+logs?"
    r")\b",
    re.I,
)


@dataclass
class ActiveProviderContext:
    provider: str
    service: str = ""
    project: str = ""
    environment: str = "production"
    operation: str = ""
    source: str = ""
    thread_path: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "service": self.service,
            "project": self.project,
            "environment": self.environment,
            "operation": self.operation,
            "source": self.source,
            "thread_path": self.thread_path,
        }


def explicit_provider_in_prompt(text: str) -> str | None:
    match = _EXPLICIT_PROVIDER_RX.search(text or "")
    return match.group(1).lower() if match else None


def is_platform_system_health_phrase(text: str) -> bool:
    return bool(_PLATFORM_SYSTEM_HEALTH_RX.search(text or ""))


def is_provider_neutral_health_phrase(text: str, *, session_id: str = "default") -> bool:
    raw = text or ""
    if is_platform_system_health_phrase(raw):
        return True
    if not _PROVIDER_NEUTRAL_HEALTH_RX.search(raw):
        return False
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        should_preempt_to_post_mutation_verification,
    )
    from aethos_core.post_mutation_verification.verification_context_discovery import (
        global_mutation_lifecycle_exists,
    )

    if global_mutation_lifecycle_exists() and should_preempt_to_post_mutation_verification(
        raw, session_id=session_id
    ):
        return False
    return True


def is_provider_neutral_operational_phrase(text: str, *, session_id: str = "default") -> bool:
    raw = text or ""
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        verification_preemption_blocks_route,
    )

    if verification_preemption_blocks_route(raw, session_id=session_id):
        return False
    return is_provider_neutral_health_phrase(raw, session_id=session_id) or bool(
        _PROVIDER_NEUTRAL_LOGS_RX.search(raw)
    )


def should_inherit_active_provider_context(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        explicit_target_overrides_session_context,
    )
    from aethos_core.operational_planner.planner_router import should_override_active_thread

    if explicit_target_overrides_session_context(text, session_id=session_id):
        return False
    if should_override_active_thread(text, session_id=session_id):
        return False
    explicit = explicit_provider_in_prompt(text)
    if explicit == "vercel":
        return False
    if explicit and explicit != "vercel":
        return False
    if not is_provider_neutral_operational_phrase(text, session_id=session_id):
        return False
    return resolve_active_provider_context(session_id=session_id, user_text=text) is not None


def resolve_active_provider_context(*, session_id: str, user_text: str = "") -> ActiveProviderContext | None:
    explicit = explicit_provider_in_prompt(user_text)
    if explicit == "vercel":
        return None

    from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

    thread = get_active_operational_thread(session_id)
    if thread is not None:
        return ActiveProviderContext(
            provider=str(getattr(thread, "provider", "") or "railway"),
            service=str(getattr(thread, "service", "") or ""),
            project=str(getattr(thread, "project", "") or ""),
            environment=str(getattr(thread, "environment", "") or "production"),
            operation=str(getattr(thread, "operation", "") or ""),
            source="active_operational_thread",
            thread_path=thread.service_path(),
        )

    from aethos_core.continuity_intelligence.operational_focus_model import get_operational_focus

    focus = get_operational_focus(session_id=session_id)
    if focus.get("provider") and focus.get("service"):
        project = str(focus.get("project") or "")
        environment = str(focus.get("environment") or "production")
        service = str(focus.get("service") or "")
        path = f"{project} / {environment} / {service}".strip(" /") if project else service
        return ActiveProviderContext(
            provider=str(focus.get("provider") or "railway"),
            service=service,
            project=project,
            environment=environment,
            operation=str(focus.get("operation") or ""),
            source="operational_focus",
            thread_path=path,
        )

    if explicit and explicit != "vercel":
        from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase, search_provider_targets

        phrase = extract_operational_resource_phrase(user_text) or ""
        if phrase:
            topology = search_provider_targets(phrase)
            if topology.resolved and topology.resolved.provider == explicit:
                target = topology.resolved
                return ActiveProviderContext(
                    provider=target.provider,
                    service=target.service_name,
                    project=str(target.project_name or ""),
                    environment=str(target.environment or "production"),
                    source="topology_search",
                    thread_path=target.path or target.service_name,
                )
    return None


def compose_ambiguous_health_clarification_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if explicit_provider_in_prompt(text):
        return None
    if not is_provider_neutral_health_phrase(text, session_id=session_id):
        return None
    if resolve_active_provider_context(session_id=session_id, user_text=text):
        return None
    body = (
        "I can check service health, but I need to know which provider and target you mean.\n\n"
        "Examples:\n"
        "- Railway: `check service health for pilotos-api`\n"
        "- Vercel: `check Vercel service health`\n\n"
        "If you were following up on an active operational thread, that context may have expired — "
        "tell me the service and environment again."
    )
    return body, "health_check_clarification", {}


def block_vercel_inspection_for_active_context(text: str, *, session_id: str = "default") -> bool:
    """Return True when a generic health/status prompt should not route to Vercel."""
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        explicit_target_overrides_session_context,
        should_route_explicit_provider_diagnostics,
    )

    if should_route_explicit_provider_diagnostics(text, session_id=session_id):
        return False
    if explicit_target_overrides_session_context(text, session_id=session_id):
        return False
    if explicit_provider_in_prompt(text) == "vercel":
        return False
    if not is_provider_neutral_health_phrase(text, session_id=session_id):
        return False
    ctx = resolve_active_provider_context(session_id=session_id, user_text=text)
    return ctx is not None and ctx.provider != "vercel"
