# SPDX-License-Identifier: Apache-2.0
"""Capability intro response content tests."""

from __future__ import annotations

from aethos_core.chat.front_door_intent import compose_capability_intro_reply
from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn

_CAPABILITY_PROMPT = "what can you do?"


def test_capability_response_includes_governed_operations() -> None:
    reply = compose_capability_intro_reply(text=_CAPABILITY_PROMPT)
    assert "governed" in reply.lower() or "approval" in reply.lower()


def test_capability_response_is_plain_language_not_provider_dump() -> None:
    reply = compose_capability_intro_reply(text=_CAPABILITY_PROMPT)
    low = reply.lower()
    assert "not_configured" not in low
    assert "chat" in low or "research" in low
    assert "investigation" in low or "explain" in low


def test_capability_response_includes_platform_strengths() -> None:
    reply = compose_capability_intro_reply(text=_CAPABILITY_PROMPT)
    assert "workspace" in reply.lower() or "memory" in reply.lower() or "automate" in reply.lower()


def test_capability_response_excludes_provider_diagnostics_unless_asked() -> None:
    result = safe_resolve_operational_turn("what are you capable of?", session_id="cap-intro-live")
    assert result is not None
    low = result.reply.lower()
    assert "mongodb" not in low
    assert "pilotcore" not in low
    assert "diagnostic id" not in low
    assert "not_configured" not in low
