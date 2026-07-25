# SPDX-License-Identifier: Apache-2.0
"""On-demand agent capabilities — bounded, policy-governed under orchestration authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.agents.runtime.planner import plan_task
from aethos_core.agents.runtime.registry import available_capabilities

# Capabilities the orchestrator can compose into on-demand task agents (plus the
# standing orchestration planner). This is a capability set, not a static roster.
AGENT_ROLES = frozenset({*available_capabilities(), "planner"})


@dataclass
class AgentTaskGraph:
    goal: str
    roles: list[str] = field(default_factory=list)
    proposed_steps: list[str] = field(default_factory=list)
    verification_criteria: list[str] = field(default_factory=list)
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "roles": self.roles,
            "proposed_steps": self.proposed_steps,
            "verification_criteria": self.verification_criteria,
            "execution_enabled": self.execution_enabled,
            "dry_run": True,
        }


def simulate_task_graph(goal: str) -> AgentTaskGraph:
    plan = plan_task(goal)
    return AgentTaskGraph(
        goal=goal,
        roles=[a.agent_id for a in plan.assignments],
        proposed_steps=[f"{a.agent_id}: {a.task} — orchestration-governed" for a in plan.assignments],
        verification_criteria=[
            "Evidence attached",
            "Approval gates respected",
            "No mutation execution",
            "Orchestration retains authority",
        ],
        execution_enabled=False,
    )
