# SPDX-License-Identifier: Apache-2.0
"""Multi-agent coordination — orchestration authority retained."""

from __future__ import annotations

import time
from typing import Any

from aethos_core.agents.runtime.agent_limits import MAX_BACKGROUND_RUNTIME_SEC, MAX_RECURSION_DEPTH
from aethos_core.agents.runtime.agent_context import AgentContext
from aethos_core.agents.runtime.artifacts import store_agent_artifact
from aethos_core.agents.runtime.comms import finish_coordination_comms as _finish_comms
from aethos_core.agents.runtime.comms import record_agent_message as _msg
from aethos_core.agents.runtime.comms import start_coordination_comms as _start_comms
from aethos_core.agents.runtime.delegation import delegate_agent_step
from aethos_core.agents.runtime.evidence_merge import format_merged_report, merge_agent_evidence
from aethos_core.agents.runtime.planner import TaskPlan, plan_task
from aethos_core.agents.runtime.report_mode import infer_report_mode
from aethos_core.agents.memory.task_memory import record_coordination


def run_agent_coordination(
    *,
    goal: str,
    session_id: str = "default",
    workspace_hint: str | None = None,
    depth: int = 0,
) -> dict[str, Any]:
    """Execute bounded multi-agent task under orchestration — no direct mutations."""
    if depth > MAX_RECURSION_DEPTH:
        return {"ok": False, "error": "recursion_depth_exceeded", "read_only": True}

    started = time.time()
    plan = plan_task(goal, depth=depth)
    results: list[dict[str, Any]] = []
    collected_evidence: list[str] = []

    # Live inter-agent comms (drives the real-time multi-agent visual). Best-effort —
    # never let recording affect the run.
    def _comms(fn):
        try:
            fn()
        except Exception:  # noqa: BLE001
            pass

    assignments = list(plan.assignments)
    # Unique node id per assignment so roles that share a capability (e.g. several
    # 'research' specialists for researcher/copywriter/marketer) still render as
    # distinct agents in the live graph instead of collapsing onto one node.
    node_ids = [f"{a.agent_id}-{i}" for i, a in enumerate(assignments)]
    labels = [a.task.split(":")[0].strip() or a.agent_id for a in assignments]

    _comms(
        lambda: _start_comms(
            session_id,
            [
                {"id": node_ids[i], "label": labels[i], "role": a.agent_id}
                for i, a in enumerate(assignments)
            ],
            goal=goal,
        )
    )
    for idx, assignment in enumerate(assignments):
        if time.time() - started > MAX_BACKGROUND_RUNTIME_SEC:
            results.append(
                {
                    "agent_id": assignment.agent_id,
                    "task": assignment.task,
                    "status": "failed",
                    "error": "runtime_budget_exceeded",
                }
            )
            break
        ctx = AgentContext(
            agent_id=assignment.agent_id,
            task=assignment.task,
            action=assignment.action,
            session_id=session_id,
            workspace_hint=workspace_hint,
            user_request=goal,
            recursion_depth=depth,
            prior_results=list(results),
            evidence_ids=list(collected_evidence),
        )
        _comms(
            lambda a=assignment, nid=node_ids[idx]: _msg(
                session_id, frm="orchestrator", to=nid, mtype="dispatch", summary=a.task
            )
        )
        row = delegate_agent_step(ctx)
        results.append(row)
        if row.get("artifact_id"):
            collected_evidence.append(str(row["artifact_id"]))
        collected_evidence.extend([str(e) for e in row.get("evidence_ids") or []])
        _comms(
            lambda a=assignment, r=row, nid=node_ids[idx]: _msg(
                session_id,
                frm=nid,
                to="orchestrator",
                mtype="report",
                summary=f"{r.get('status', 'done')}: {(r.get('summary') or a.task)}",
            )
        )
        # Hand off to the next teammate so the visual shows work flowing across agents.
        if idx + 1 < len(assignments):
            _comms(
                lambda cur=node_ids[idx], nxt=node_ids[idx + 1]: _msg(
                    session_id, frm=cur, to=nxt, mtype="handoff", summary="handing off context"
                )
            )

    merged = merge_agent_evidence(
        plan_id=plan.plan_id,
        goal=goal,
        agent_results=results,
        report_mode=infer_report_mode(goal),
    )
    from aethos_core.agents.memory.operational_patterns import record_coordination_patterns

    recurring = record_coordination_patterns(merged=merged, plan_id=plan.plan_id)
    merged["recurring_patterns"] = recurring or merged.get("recurring_patterns") or []
    graph = build_coordination_graph(plan, results, merged)
    report = format_merged_report(merged)

    coord_artifact = store_agent_artifact(
        artifact_type="agent_coordination",
        agent_id=None,
        plan_id=plan.plan_id,
        payload={
            "plan": plan.to_dict(),
            "results": results,
            "merged": merged,
            "graph": graph,
            "duration_ms": int((time.time() - started) * 1000),
        },
        summary=f"Coordination — {merged.get('status')}",
    )
    summary_artifact = store_agent_artifact(
        artifact_type="agent_summary",
        agent_id=None,
        plan_id=plan.plan_id,
        payload={"report": report, "merged": merged},
        summary=f"Multi-agent report — {merged.get('status')}",
    )
    store_agent_artifact(
        artifact_type="agent_confidence_summary",
        agent_id=None,
        plan_id=plan.plan_id,
        payload={
            "confidence": merged.get("confidence"),
            "severity": merged.get("severity"),
            "severity_authority": merged.get("severity_authority"),
            "report_mode": merged.get("report_mode"),
            "conclusions": merged.get("conclusions"),
            "evidence_ids": merged.get("evidence_ids"),
        },
        summary=f"Confidence {((merged.get('confidence') or {}).get('level')) or 'low'} · severity {merged.get('severity')}",
    )

    record_coordination(
        plan_id=plan.plan_id,
        goal=goal,
        status=str(merged.get("status")),
        artifact_id=coord_artifact["artifact_id"],
    )

    _comms(lambda: _finish_comms(session_id))

    return {
        "ok": True,
        "plan": plan.to_dict(),
        "graph": graph,
        "results": results,
        "merged": merged,
        "report": report,
        "coordination_artifact_id": coord_artifact["artifact_id"],
        "summary_artifact_id": summary_artifact["artifact_id"],
        "read_only": True,
        "execution_enabled": False,
        "mutation_execution_enabled": False,
        "duration_ms": int((time.time() - started) * 1000),
    }


def build_coordination_graph(
    plan: TaskPlan,
    results: list[dict[str, Any]] | None = None,
    merged: dict[str, Any] | None = None,
) -> dict[str, Any]:
    results = results or []
    merged = merged or {}
    by_agent = {str(r.get("agent_id")): r for r in results}
    nodes = [{"id": "planner", "label": "Orchestration Planner", "type": "planner", "severity": "neutral"}]
    edges: list[dict[str, Any]] = []
    prev = "planner"
    for a in plan.assignments:
        row = by_agent.get(a.agent_id) or {}
        sev = str((row.get("analysis") or {}).get("severity") or "LOW").lower()
        nodes.append(
            {
                "id": a.agent_id,
                "label": a.agent_id.replace("_", " ").title(),
                "type": "agent",
                "task": a.task,
                "status": row.get("status"),
                "duration_ms": row.get("duration_ms"),
                "evidence_count": len(row.get("evidence_ids") or []),
                "substrate_invoked": row.get("substrate_invoked") or [],
                "severity": sev,
            }
        )
        edges.append({"from": prev, "to": a.agent_id, "task": a.task, "dependency": True, "kind": "orchestration"})
        prev = a.agent_id

    correlation = merged.get("correlation") or {}
    for edge in correlation.get("graph_edges") or []:
        edges.append(
            {
                "from": edge.get("from"),
                "to": edge.get("to"),
                "label": edge.get("label"),
                "kind": "evidence",
                "dependency": False,
            }
        )

    replay = [
        {"step": "intent", "label": plan.goal[:120]},
        {"step": "agents", "label": f"{len(plan.assignments)} agent(s)"},
        {"step": "evidence", "label": f"{merged.get('evidence_bundle_count', 0)} artifact(s)"},
        {"step": "correlation", "label": f"{correlation.get('correlation_count', 0)} correlation(s)"},
        {"step": "report", "label": str(merged.get("report_mode") or "generic")},
        {"step": "verification", "label": "read-only · no mutation execution"},
    ]
    return {"nodes": nodes, "edges": edges, "replay": replay, "confidence": merged.get("confidence")}
