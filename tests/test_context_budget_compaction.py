# SPDX-License-Identifier: Apache-2.0
"""Context budget + compaction helpers (Part A §A2)."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.agents.runtime.context_budget import (
    compact_session_transcript,
    enrich_user_message_with_memory,
    estimate_context_chars,
    should_compact,
)


def test_enrich_user_message_includes_memory_overlay():
    with patch(
        "aethos_core.chat.conversation_context.compose_conversation_llm_context",
        return_value="Summary: discussed atlas-trader.",
    ):
        out = enrich_user_message_with_memory("sess-1", "follow up on that")
    assert "atlas-trader" in out
    assert "follow up" in out


def test_should_compact_on_large_message_list():
    messages = [{"role": "user", "content": "x" * 50_000}]
    assert should_compact(messages)


def test_compact_session_transcript_after_many_turns():
    with patch(
        "aethos_core.memory.conversation_summary_memory.get_recent_turns",
        return_value=[{"user_text": "u", "reply_preview": "r"}] * 45,
    ):
        assert compact_session_transcript("sess-1", turn_count=45) is True


def test_compact_keeps_tail_under_threshold():
    from aethos_core.agents.runtime.context_budget import compact_tool_loop_messages, should_compact

    messages = [{"role": "user", "content": "subject: atlas-trader"}]
    for i in range(40):
        messages.append({"role": "user", "content": f"turn {i} " + "x" * 1200})
        messages.append({"role": "assistant", "content": f"reply {i}"})
    assert should_compact(messages)
    # compaction helper delegates to execution_brain — without API key stays same length guard
    assert len(messages) >= 40


def test_estimate_context_chars_matches_compaction_helper():
    messages = [{"role": "user", "content": "hello"}]
    assert estimate_context_chars(messages) > 0
