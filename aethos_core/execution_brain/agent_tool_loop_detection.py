# SPDX-License-Identifier: Apache-2.0
"""Tool loop stuck detection — break repeated identical calls."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from typing import Any


class ToolLoopDetector:
    """Detect ping-pong / identical tool repetition within one agent run."""

    def __init__(self, *, window: int = 12, repeat_threshold: int = 3) -> None:
        self._window = max(4, window)
        self._repeat_threshold = max(2, repeat_threshold)
        self._recent: deque[str] = deque(maxlen=self._window)
        self._counts: dict[str, int] = {}

    def _fingerprint(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        payload = json.dumps({"name": tool_name, "input": tool_input}, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def check_before(self, tool_name: str, tool_input: dict[str, Any]) -> tuple[bool, str]:
        fp = self._fingerprint(tool_name, tool_input)
        next_count = self._counts.get(fp, 0) + 1
        if next_count >= self._repeat_threshold:
            return True, f"identical_tool_repeat:{tool_name}:{next_count}"
        if len(self._recent) >= self._window:
            trial = list(self._recent) + [fp]
            if len(set(trial[-self._window :])) <= 2:
                return True, f"tool_ping_pong:{tool_name}"
        return False, ""

    def record(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        fp = self._fingerprint(tool_name, tool_input)
        self._recent.append(fp)
        self._counts[fp] = self._counts.get(fp, 0) + 1

    def is_stuck(self, tool_name: str, tool_input: dict[str, Any]) -> tuple[bool, str]:
        fp = self._fingerprint(tool_name, tool_input)
        count = self._counts.get(fp, 0)
        if count >= self._repeat_threshold:
            return True, f"identical_tool_repeat:{tool_name}:{count}"
        if len(self._recent) >= self._window:
            unique = len(set(self._recent))
            if unique <= 2:
                return True, f"tool_ping_pong:{tool_name}"
        return False, ""


def stuck_tool_result(tool_name: str, reason: str) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": "tool_loop_detected",
            "tool": tool_name,
            "reason": reason,
            "hint": "Change strategy — narrow the query, use a different tool, or answer from prior results.",
        }
    )
