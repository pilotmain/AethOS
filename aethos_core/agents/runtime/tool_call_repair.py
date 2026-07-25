# SPDX-License-Identifier: Apache-2.0
"""Tool-call validation and repair hints for agent tool loops."""

from __future__ import annotations

import json
from typing import Any

MAX_REPAIR_ATTEMPTS = 2

_LOOP_OUTCOMES = frozenset({"answered", "tool_executed", "awaiting_approval", "error_degraded"})


class ToolCallRepairBudget:
    """Per-turn cap so malformed tool calls cannot spin forever."""

    def __init__(self, *, max_attempts: int = MAX_REPAIR_ATTEMPTS) -> None:
        self._max = max(1, int(max_attempts))
        self._attempts = 0

    def allow_repair(self) -> bool:
        return self._attempts < self._max

    def record_repair(self) -> None:
        self._attempts += 1

    @property
    def exhausted(self) -> bool:
        return self._attempts >= self._max


def allowed_names_from_tools(tools: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name") or "").strip()
        if name:
            names.add(name)
    return names


def parse_tool_arguments(raw: str | dict | None) -> tuple[dict[str, Any], str | None]:
    """Parse model tool arguments; return repair hint when JSON is invalid."""
    if isinstance(raw, dict):
        return dict(raw), None
    if raw is None:
        return {}, None
    text = str(raw).strip()
    if not text:
        return {}, None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, f"Tool arguments were invalid JSON ({exc}). Retry with a valid JSON object."
    if not isinstance(parsed, dict):
        return {}, "Tool arguments must be a JSON object (dict), not a list or scalar."
    return parsed, None


def validate_tool_call(
    name: str,
    tool_input: dict[str, Any],
    *,
    allowed_names: set[str],
) -> str | None:
    """Return a repair hint when the call cannot run; None when OK to execute."""
    tool_name = (name or "").strip()
    if not tool_name:
        return "Tool name is missing. Pick a tool from the schema and call it with required fields."
    if allowed_names and tool_name not in allowed_names:
        sample = ", ".join(sorted(allowed_names)[:8])
        return (
            f"Unknown tool `{tool_name}`. Use one of: {sample}"
            + ("…" if len(allowed_names) > 8 else "")
        )
    return None


def repair_result_text(hint: str, *, exhausted: bool = False) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": "tool_call_repair",
            "repair_hint": hint,
            "retry": not exhausted,
            "repair_exhausted": exhausted,
        }
    )


def classify_loop_outcome(
    text: str,
    *,
    tool_calls: int,
    degraded: bool = False,
) -> str:
    """Deterministic terminal outcome for one loop turn."""
    if degraded:
        return "error_degraded"
    body = (text or "").strip().lower()
    if any(
        phrase in body
        for phrase in (
            "approve in mission control",
            "approval required",
            "preflight created",
            "awaiting approval",
            "pending approval",
        )
    ):
        return "awaiting_approval"
    if tool_calls > 0:
        return "tool_executed"
    return "answered"


def normalize_loop_outcome(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in _LOOP_OUTCOMES:
        return raw
    return "answered"
