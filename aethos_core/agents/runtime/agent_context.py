# SPDX-License-Identifier: Apache-2.0
"""Scoped agent context — per-delegation boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    agent_id: str
    task: str
    action: str
    session_id: str = "default"
    workspace_hint: str | None = None
    user_request: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    prior_results: list[dict[str, Any]] = field(default_factory=list)
    read_only: bool = True
    recursion_depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task": self.task,
            "action": self.action,
            "session_id": self.session_id,
            "workspace_hint": self.workspace_hint,
            "read_only": self.read_only,
            "recursion_depth": self.recursion_depth,
            "evidence_ids": list(self.evidence_ids),
            "prior_agent_count": len(self.prior_results),
        }
