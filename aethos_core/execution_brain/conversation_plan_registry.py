# SPDX-License-Identifier: Apache-2.0
"""Conversation plan registry — active goals, steps, and resume state."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.execution_brain.goal_planner import OperationalGoalPlan
from aethos_core.execution_brain.tool_planning_graph import ToolPlanningGraph

_lock = threading.Lock()
_memory: dict[str, dict] = {}


@dataclass
class ConversationPlan:
    session_id: str
    active_goal: str = ""
    goal_kind: str = ""
    provider: str = ""
    completed_steps: list[str] = field(default_factory=list)
    pending_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    suggested_next_action: str = ""
    graph: ToolPlanningGraph | None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_goal": self.active_goal,
            "goal_kind": self.goal_kind,
            "provider": self.provider,
            "completed_steps": list(self.completed_steps),
            "pending_steps": list(self.pending_steps),
            "failed_steps": list(self.failed_steps),
            "suggested_next_action": self.suggested_next_action,
            "graph": _graph_to_dict(self.graph),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ConversationPlan:
        return cls(
            session_id=str(payload.get("session_id") or "default"),
            active_goal=str(payload.get("active_goal") or ""),
            goal_kind=str(payload.get("goal_kind") or ""),
            provider=str(payload.get("provider") or ""),
            completed_steps=[str(item) for item in payload.get("completed_steps") or []],
            pending_steps=[str(item) for item in payload.get("pending_steps") or []],
            failed_steps=[str(item) for item in payload.get("failed_steps") or []],
            suggested_next_action=str(payload.get("suggested_next_action") or ""),
            graph=_graph_from_dict(payload.get("graph")),
            updated_at=str(payload.get("updated_at") or ""),
        )


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation_plans"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def load_conversation_plan(*, session_id: str = "default") -> ConversationPlan | None:
    sid = (session_id or "default").strip() or "default"
    with _lock:
        cached = _memory.get(sid)
    if cached is None:
        path = _session_path(sid)
        if path.is_file():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
        else:
            return None
    if not isinstance(cached, dict):
        return None
    return ConversationPlan.from_dict(cached)


def save_conversation_plan(plan: ConversationPlan) -> None:
    plan.updated_at = datetime.now(UTC).isoformat()
    payload = plan.to_dict()
    sid = plan.session_id
    with _lock:
        _memory[sid] = payload
    try:
        _session_path(sid).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def upsert_plan_from_graph(
    *,
    session_id: str,
    goal: OperationalGoalPlan,
    graph: ToolPlanningGraph,
    suggested_next_action: str = "",
) -> ConversationPlan:
    pending = [step.step_id for step in graph.steps if step.status == "pending"]
    completed = [step.step_id for step in graph.steps if step.status == "completed"]
    failed = [step.step_id for step in graph.steps if step.status == "failed"]
    plan = ConversationPlan(
        session_id=session_id,
        active_goal=goal.headline,
        goal_kind=goal.kind,
        provider=goal.provider,
        completed_steps=completed,
        pending_steps=pending,
        failed_steps=failed,
        suggested_next_action=suggested_next_action,
        graph=graph,
    )
    save_conversation_plan(plan)
    return plan


def clear_conversation_plans_for_tests() -> None:
    with _lock:
        _memory.clear()


def _graph_to_dict(graph: ToolPlanningGraph | None) -> dict[str, Any]:
    if graph is None:
        return {}
    return {
        "goal_headline": graph.goal_headline,
        "provider": graph.provider,
        "planning_only": graph.planning_only,
        "steps": [
            {
                "step_id": step.step_id,
                "sub_goal_kind": step.sub_goal_kind,
                "label": step.label,
                "tool_id": step.tool_id,
                "tool_type": step.tool_type,
                "provider": step.provider,
                "status": step.status,
                "readonly": step.readonly,
                "result_summary": step.result_summary,
                "error_code": step.error_code,
            }
            for step in graph.steps
        ],
    }


def _graph_from_dict(payload: Any) -> ToolPlanningGraph | None:
    if not isinstance(payload, dict):
        return None
    from aethos_core.execution_brain.tool_planning_graph import ToolPlanStep, ToolPlanningGraph

    steps = []
    for row in payload.get("steps") or []:
        if not isinstance(row, dict):
            continue
        steps.append(
            ToolPlanStep(
                step_id=str(row.get("step_id") or ""),
                sub_goal_kind=str(row.get("sub_goal_kind") or ""),
                label=str(row.get("label") or ""),
                tool_id=str(row.get("tool_id") or ""),
                tool_type=str(row.get("tool_type") or "readonly"),
                provider=str(row.get("provider") or ""),
                status=str(row.get("status") or "pending"),
                readonly=bool(row.get("readonly", True)),
                result_summary=str(row.get("result_summary") or ""),
                error_code=str(row.get("error_code") or ""),
            )
        )
    return ToolPlanningGraph(
        goal_headline=str(payload.get("goal_headline") or ""),
        provider=str(payload.get("provider") or ""),
        steps=steps,
        planning_only=bool(payload.get("planning_only")),
    )
