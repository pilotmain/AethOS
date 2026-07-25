# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — read-only lane snapshot collectors."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def _read_json_dir(root: Path, *, limit: int = 8) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    paths = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payload["_source_file"] = path.name
            rows.append(payload)
    return rows


def collect_route_diagnostics(*, session_id: str) -> dict[str, Any]:
    from aethos_core.chat.route_trace import get_last_route_trace

    trace = get_last_route_trace(session_id=session_id) or {}
    return {
        "lane": "route_diagnostics",
        "ok": bool(trace),
        "route_id": trace.get("route_id"),
        "matched_module": trace.get("matched_module"),
        "intent": trace.get("intent"),
        "recorded_at": trace.get("recorded_at"),
    }


def collect_software_delivery(*, session_id: str) -> dict[str, Any]:
    from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
    from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
    from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan
    from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
    from aethos_core.software_delivery.multi_agent.multi_agent_store import load_collaboration_for_plan
    from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")
    timeline = build_software_delivery_timeline(session_id=session_id) if plan else {}
    gates = [
        {"gate": "issue_plan", "passed": bool(plan)},
        {"gate": "planning_approved", "passed": str((plan or {}).get("status") or "") == "planning_approved"},
        {"gate": "workspace_verification", "passed": workspace_verification_passed(plan_id=plan_id) if plan_id else False},
        {"gate": "github_preflight_approved", "passed": github_pr_creation_approved_for_plan(plan_id=plan_id) if plan_id else False},
        {"gate": "branch_push_completed", "passed": branch_push_completed_for_plan(plan_id=plan_id) if plan_id else False},
        {"gate": "github_pr_opened", "passed": github_pr_open_completed_for_plan(plan_id=plan_id) if plan_id else False},
    ]
    pending = [g["gate"] for g in gates if not g["passed"]]
    return {
        "lane": "software_delivery",
        "ok": bool(plan),
        "plan_id": plan_id,
        "plan_status": (plan or {}).get("status"),
        "repository": (plan or {}).get("repository"),
        "governance_gates": gates,
        "pending_gates": pending,
        "timeline_event_count": len(timeline.get("plan_events") or []),
        "agent_collaboration": bool(load_collaboration_for_plan(plan_id=plan_id)) if plan_id else False,
        "timeline": timeline,
    }


def collect_multi_agent(*, session_id: str) -> dict[str, Any]:
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
    from aethos_core.software_delivery.multi_agent.multi_agent_store import load_collaboration_for_plan

    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")
    collab = load_collaboration_for_plan(plan_id=plan_id) if plan_id else None
    outputs = list((collab or {}).get("agent_outputs") or [])
    return {
        "lane": "multi_agent_collaboration",
        "ok": bool(collab),
        "collaboration_id": (collab or {}).get("collaboration_id"),
        "status": (collab or {}).get("status"),
        "agents_run": [o.get("agent_role_id") for o in outputs],
        "mutation_performed": False,
    }


def collect_railway_orchestration(*, session_id: str) -> dict[str, Any]:
    journals = _read_json_dir(_DATA_ROOT / "railway_execution_journal", limit=3)
    receipts = _read_json_dir(_DATA_ROOT / "railway_execution_receipts", limit=5)
    return {
        "lane": "railway_orchestration",
        "ok": True,
        "recent_journals": len(journals),
        "recent_receipts": len(receipts),
        "latest_journal_status": journals[0].get("status") if journals else None,
        "latest_execution_id": journals[0].get("execution_id") if journals else None,
        "session_linked": False,
        "note": "Railway journals are execution-scoped; correlate via deployment plan context.",
    }


def collect_production_governance(*, session_id: str) -> dict[str, Any]:
    rollouts = _read_json_dir(_DATA_ROOT / "railway_production_rollout_journal", limit=3)
    shadows = _read_json_dir(_DATA_ROOT / "railway_production_shadow_journal", limit=3)
    return {
        "lane": "production_governance",
        "ok": True,
        "rollout_records": len(rollouts),
        "shadow_records": len(shadows),
        "latest_rollout_stage": (rollouts[0].get("current_stage") if rollouts else None),
        "mutation_policy": "governance_only_no_live_prod_forward",
    }


def collect_incident_command(*, session_id: str) -> dict[str, Any]:
    incidents = _read_json_dir(_DATA_ROOT / "railway_production_incidents", limit=5)
    open_incidents = [
        i for i in incidents if str(i.get("status") or "").lower() not in {"closed", "resolved"}
    ]
    return {
        "lane": "incident_command",
        "ok": True,
        "incident_count": len(incidents),
        "open_incidents": len(open_incidents),
        "latest_incident_id": incidents[0].get("incident_id") if incidents else None,
        "latest_status": incidents[0].get("status") if incidents else None,
    }


def collect_durable_jobs(*, session_id: str) -> dict[str, Any]:
    from aethos_core.jobs.job_registry import list_durable_job_types

    job_types = list_durable_job_types()
    return {
        "lane": "durable_jobs",
        "ok": True,
        "job_graph_nodes": [j.get("id") for j in job_types],
        "mutation_job_types_blocked": True,
        "node_count": len(job_types),
    }


def collect_unified_timeline(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    lanes = snapshot.get("lanes") if isinstance(snapshot.get("lanes"), dict) else {}
    sd = lanes.get("software_delivery") or snapshot.get("software_delivery") or {}
    timeline = sd.get("timeline") if isinstance(sd.get("timeline"), dict) else {}
    for ev in timeline.get("plan_events") or []:
        if isinstance(ev, dict):
            entries.append(
                {
                    "lane": "software_delivery",
                    "timestamp": ev.get("recorded_at") or "",
                    "action": ev.get("action") or "",
                    "detail": ev.get("detail") or "",
                }
            )
    for receipt_dir, lane in (
        ("railway_execution_receipts", "railway_orchestration"),
        ("software_delivery_github_pr_open_receipts", "software_delivery"),
    ):
        for path in sorted((_DATA_ROOT / receipt_dir).glob("*.json"))[:3]:
            try:
                rows = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(rows, list):
                continue
            for row in rows[-5:]:
                if isinstance(row, dict):
                    entries.append(
                        {
                            "lane": lane,
                            "timestamp": row.get("recorded_at") or "",
                            "action": row.get("phase") or "",
                            "detail": row.get("detail") or "",
                        }
                    )
    entries.sort(key=lambda e: str(e.get("timestamp") or ""), reverse=True)
    return entries[:40]
