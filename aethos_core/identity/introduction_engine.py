# SPDX-License-Identifier: Apache-2.0
"""Introduction engine — greeting and first impression system."""

from __future__ import annotations

import random

from aethos_core.identity.operational_voice import IDENTITY_INTRO, PARTNERSHIP_CLOSING


def is_returning_session(recent_turns: list[dict] | None) -> bool:
    if not recent_turns:
        return False
    assistant_turns = [t for t in recent_turns if t.get("role") == "assistant"]
    return len(assistant_turns) >= 1


def _greeting_name() -> str:
    try:
        from aethos_core.onboarding.operator_persona import persona_greeting_name

        return persona_greeting_name()
    except Exception:
        return ""


def greeting_reply(*, text: str = "", returning: bool = False) -> str:
    """Warm, calm, grounded greeting — never theatrical."""
    name = _greeting_name()
    who = f" {name}" if name else ""
    t = (text or "").strip().lower()
    if returning:
        options = (
            f"Good to see you again{who}.\n\nWhat's the most important thing on your mind right now?",
            f"Welcome back{who}.\n\nWhat would you like to work through?",
            f"Hi{who} — I'm here.\n\nWhat are we focusing on today?",
        )
        return random.choice(options)

    if t in {"hi", "hey", "yo", "sup"}:
        options = (
            f"Hi{who} — I'm **AethOS**.\n\nWhat are we focusing on today?",
            f"Hi{who}. I'm here.\n\nWhat would you like to work through?",
        )
        return random.choice(options)

    return f"Hello{who} — I'm **AethOS**.\n\nWhat would you like to work through?"


def identity_intro_reply() -> str:
    """Trustworthy operational intelligence introduction — not a tooling manifest."""
    name = _greeting_name()
    prefix = f"Hi {name} — " if name else ""
    body = f"{IDENTITY_INTRO}\n\n{PARTNERSHIP_CLOSING}"
    if prefix:
        return prefix + body
    return body


def who_are_you_reply() -> str:
    return identity_intro_reply()
