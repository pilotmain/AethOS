# SPDX-License-Identifier: Apache-2.0
"""Tool planning graph — Goal → Step → Tool → Result (planning structure)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.execution_brain.goal_planner import OperationalGoalPlan, SubGoal
from aethos_core.execution_brain.provider_tool_contract import get_tool_contract


@dataclass
class ToolPlanStep:
    step_id: str
    sub_goal_kind: str
    label: str
    tool_id: str
    tool_type: str
    provider: str
    status: str = "pending"
    readonly: bool = True
    result_summary: str = ""
    error_code: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolPlanningGraph:
    goal_headline: str
    provider: str
    steps: list[ToolPlanStep] = field(default_factory=list)
    planning_only: bool = False

    def next_pending_step(self) -> ToolPlanStep | None:
        for step in self.steps:
            if step.status == "pending":
                return step
        return None

    def next_readonly_step(self) -> ToolPlanStep | None:
        for step in self.steps:
            if step.status == "pending" and step.readonly:
                return step
        return None

    def completed_count(self) -> int:
        return sum(1 for step in self.steps if step.status == "completed")

    def failed_step(self) -> ToolPlanStep | None:
        for step in self.steps:
            if step.status == "failed":
                return step
        return None


def build_tool_planning_graph(plan: OperationalGoalPlan) -> ToolPlanningGraph:
    steps: list[ToolPlanStep] = []
    idx = 0
    for sub in plan.sub_goals:
        for tool_id in sub.tool_ids:
            contract = get_tool_contract(tool_id)
            provider = contract.provider if contract else plan.provider
            tool_type = contract.tool_type if contract else "readonly"
            readonly = tool_type == "readonly"
            steps.append(
                ToolPlanStep(
                    step_id=f"step-{idx}",
                    sub_goal_kind=sub.kind,
                    label=sub.label if len(sub.tool_ids) == 1 else f"{sub.label} ({tool_id})",
                    tool_id=tool_id,
                    tool_type=tool_type,
                    provider=provider,
                    readonly=readonly,
                )
            )
            idx += 1
    return ToolPlanningGraph(
        goal_headline=plan.headline,
        provider=plan.provider,
        steps=steps,
        planning_only=plan.kind == "deploy_planning",
    )


def mark_step_completed(graph: ToolPlanningGraph, step_id: str, *, summary: str = "", evidence: dict | None = None) -> ToolPlanningGraph:
    updated: list[ToolPlanStep] = []
    for step in graph.steps:
        if step.step_id == step_id:
            updated.append(
                ToolPlanStep(
                    **{
                        **step.__dict__,
                        "status": "completed",
                        "result_summary": summary,
                        "evidence": dict(evidence or {}),
                    }
                )
            )
        else:
            updated.append(step)
    return ToolPlanningGraph(
        goal_headline=graph.goal_headline,
        provider=graph.provider,
        steps=updated,
        planning_only=graph.planning_only,
    )


def mark_step_failed(graph: ToolPlanningGraph, step_id: str, *, error_code: str, summary: str = "") -> ToolPlanningGraph:
    updated: list[ToolPlanStep] = []
    for step in graph.steps:
        if step.step_id == step_id:
            updated.append(
                ToolPlanStep(
                    **{
                        **step.__dict__,
                        "status": "failed",
                        "error_code": error_code,
                        "result_summary": summary,
                    }
                )
            )
        else:
            updated.append(step)
    return ToolPlanningGraph(
        goal_headline=graph.goal_headline,
        provider=graph.provider,
        steps=updated,
        planning_only=graph.planning_only,
    )
