# SPDX-License-Identifier: Apache-2.0
"""Provider readonly intent router — GitHub inspection (Vercel owned by operational kernel)."""

from __future__ import annotations

from aethos_core.chat.service import ChatTurnResult
from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
    classify_readonly_provider_intent,
    is_explicit_provider_readonly_request,
    should_yield_active_thread_for_readonly,
)


def provider_readonly_preemption_blocks_route(text: str, *, session_id: str = "default") -> bool:
    return is_explicit_provider_readonly_request(text)


def compose_readonly_provider_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = classify_readonly_provider_intent(text)
    if intent is None:
        return None

    if intent.provider == "vercel":
        return None

    if intent.provider == "github":
        from aethos_core.provider_readonly_intent.github_readonly_router import compose_github_readonly_route_reply

        return compose_github_readonly_route_reply(text, session_id=session_id)

    return None


def route_readonly_provider_question(
    text: str,
    *,
    session_id: str = "default",
) -> ChatTurnResult | None:
    routed = compose_readonly_provider_route_reply(text, session_id=session_id)
    if routed is None:
        return None
    reply, intent, meta = routed
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )
