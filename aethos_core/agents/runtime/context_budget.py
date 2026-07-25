# SPDX-License-Identifier: Apache-2.0
"""Context budget for one-loop / agent tool sessions — memory + compaction."""

from __future__ import annotations

from typing import Any

from aethos_core.execution_brain.agent_context_compaction import (
    COMPACT_CHAR_THRESHOLD,
    compact_messages_for_tool_loop,
    estimate_messages_chars,
    should_compact_messages,
)


def conversation_context_block(session_id: str) -> str:
    """Rolling summary + recent turns for injection into the model loop."""
    from aethos_core.chat.conversation_context import compose_conversation_llm_context

    return (compose_conversation_llm_context(session_id) or "").strip()


def enrich_user_message_with_memory(session_id: str, user_message: str) -> str:
    """Prefix the user turn with session memory when available."""
    overlay = conversation_context_block(session_id)
    try:
        from aethos_core.config import get_settings

        if getattr(get_settings(), "vector_memory_enabled", False):
            from aethos_core.memory.long_term_store import recall_facts

            facts = recall_facts(user_message, limit=5)
            if facts.get("ok") and facts.get("memories"):
                overlay = (overlay + "\n\nLong-term memory:\n" if overlay else "Long-term memory:\n")
                for row in facts["memories"][:5]:
                    if isinstance(row, dict):
                        overlay += f"- {str(row.get('text') or row.get('snippet') or '')[:200]}\n"
    except Exception:  # noqa: BLE001
        pass
    raw = (user_message or "").strip()
    if not overlay:
        return raw
    return f"{overlay}\n\n---\n\nCurrent request:\n{raw}"


def estimate_context_chars(messages: list[dict[str, Any]]) -> int:
    return estimate_messages_chars(messages)


def should_compact(messages: list[dict[str, Any]], *, threshold: int = COMPACT_CHAR_THRESHOLD) -> bool:
    return should_compact_messages(messages, threshold=threshold)


def compact_tool_loop_messages(
    messages: list[dict[str, Any]],
    *,
    api_key: str,
    model: str,
) -> list[dict[str, Any]]:
    return compact_messages_for_tool_loop(messages, api_key=api_key, model=model)


def compact_session_transcript(
    session_id: str,
    *,
    turn_count: int,
    compact_after_turns: int = 40,
) -> bool:
    """True when the session should fold older turns into the rolling summary."""
    if turn_count < compact_after_turns:
        return False
    from aethos_core.memory.conversation_summary_memory import get_recent_turns

    turns = get_recent_turns(session_id, limit=compact_after_turns + 5)
    return len(turns) >= compact_after_turns
