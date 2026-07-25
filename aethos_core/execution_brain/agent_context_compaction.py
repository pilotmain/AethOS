# SPDX-License-Identifier: Apache-2.0
"""Context compaction for agent tool loops."""

from __future__ import annotations

import json
from typing import Any


COMPACT_CHAR_THRESHOLD = 48_000
SUMMARY_MAX_CHARS = 3_500

SUMMARY_PROMPT = """Summarize this agent tool-loop transcript for continuation. Use:

## Conversation Summary
### User Goal
### Tools Used & Key Results (bullets, include provider/project names)
### Current State
### Open Items

Be dense and factual. Preserve error messages and counts."""


def estimate_messages_chars(messages: list[dict[str, Any]]) -> int:
    total = 0
    for row in messages:
        try:
            total += len(json.dumps(row, default=str))
        except TypeError:
            total += len(str(row))
    return total


def should_compact_messages(messages: list[dict[str, Any]], *, threshold: int = COMPACT_CHAR_THRESHOLD) -> bool:
    return estimate_messages_chars(messages) >= threshold


def compact_messages_for_tool_loop(
    messages: list[dict[str, Any]],
    *,
    api_key: str,
    model: str,
) -> list[dict[str, Any]]:
    """Replace middle history with a structured summary; keep first user turn + tail."""
    if len(messages) < 4:
        return messages

    transcript = _format_transcript(messages[1:-2])
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1200,
        "system": SUMMARY_PROMPT,
        "messages": [{"role": "user", "content": transcript[:60_000]}],
    }
    try:
        # Shared resilient client (transient retry on blips); degrades to the original
        # messages if compaction can't complete so a blip never drops the turn.
        from aethos_core.provider.completion import _http_request_with_transient_retry

        response = _http_request_with_transient_retry(
            "POST",
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
        )
        data = response.json()
    except Exception:
        return messages
    parts = [
        str(block.get("text") or "")
        for block in data.get("content") or []
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    summary = "".join(parts).strip()[:SUMMARY_MAX_CHARS]
    if not summary:
        return messages
    head = messages[:1]
    tail = messages[-2:]
    compact_block = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"[Context compacted for agent loop]\n\n{summary}\n\nContinue from current state.",
            }
        ],
    }
    return head + [compact_block] + tail


def _format_transcript(messages: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for row in messages:
        role = str(row.get("role") or "unknown")
        content = row.get("content")
        if isinstance(content, str):
            lines.append(f"{role}: {content[:2000]}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    lines.append(f"tool_result: {str(block.get('content') or '')[:1500]}")
                elif isinstance(block, dict) and block.get("type") == "text":
                    lines.append(f"{role}: {str(block.get('text') or '')[:1500]}")
                elif isinstance(block, dict) and block.get("type") == "tool_use":
                    lines.append(f"tool_use: {block.get('name')} {json.dumps(block.get('input') or {}, default=str)[:400]}")
    return "\n\n".join(lines)
