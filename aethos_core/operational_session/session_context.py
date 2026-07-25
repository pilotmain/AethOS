# SPDX-License-Identifier: Apache-2.0
"""Operational session turn context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionTurn:
    user_text: str = ""
    operation: str = ""
    reply_intent: str = ""
    recorded_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_text": self.user_text,
            "operation": self.operation,
            "reply_intent": self.reply_intent,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> SessionTurn:
        if not payload:
            return cls()
        return cls(
            user_text=str(payload.get("user_text") or ""),
            operation=str(payload.get("operation") or ""),
            reply_intent=str(payload.get("reply_intent") or ""),
            recorded_at=str(payload.get("recorded_at") or ""),
        )


@dataclass
class SessionContext:
    last_operation: str = ""
    last_result_summary: str = ""
    last_deployment_id: str = ""
    last_log_limit: int = 5
    last_tool_id: str = ""
    last_provider: str = ""
    last_subject_label: str = ""
    turns: list[SessionTurn] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_operation": self.last_operation,
            "last_result_summary": self.last_result_summary,
            "last_deployment_id": self.last_deployment_id,
            "last_log_limit": self.last_log_limit,
            "last_tool_id": self.last_tool_id,
            "last_provider": self.last_provider,
            "last_subject_label": self.last_subject_label,
            "turns": [turn.to_dict() for turn in self.turns[-20:]],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> SessionContext:
        if not payload:
            return cls()
        turns = [SessionTurn.from_dict(row) for row in payload.get("turns") or [] if isinstance(row, dict)]
        return cls(
            last_operation=str(payload.get("last_operation") or ""),
            last_result_summary=str(payload.get("last_result_summary") or ""),
            last_deployment_id=str(payload.get("last_deployment_id") or ""),
            last_log_limit=int(payload.get("last_log_limit") or 5),
            last_tool_id=str(payload.get("last_tool_id") or ""),
            last_provider=str(payload.get("last_provider") or ""),
            last_subject_label=str(payload.get("last_subject_label") or ""),
            turns=turns,
        )
