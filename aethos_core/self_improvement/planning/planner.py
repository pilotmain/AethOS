# SPDX-License-Identifier: Apache-2.0
"""Implementation planning for self-improvement workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImplementationPlan:
    goal: str
    steps: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": self.steps,
            "verification": self.verification,
            "blocked_actions": self.blocked_actions,
            "execution_enabled": False,
        }


def plan_for_issue(*, issue_title: str) -> ImplementationPlan:
    return ImplementationPlan(
        goal=issue_title,
        steps=[
            "ResearchAgent analyzes affected modules with provenance",
            "PlannerAgent proposes minimal diff under orchestration policy",
            "ExecutorAgent edits on feature branch only",
            "VerifierAgent runs tests and attaches evidence",
            "PRWriterAgent drafts summary for human review",
        ],
        verification=["tests pass", "diff evidence attached", "no merge without human"],
        blocked_actions=["merge to main", "force push", "self-authorized production deploy"],
    )
