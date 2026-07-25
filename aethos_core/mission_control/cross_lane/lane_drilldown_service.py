# SPDX-License-Identifier: Apache-2.0
"""FIX 131 — read-only lane drilldown for Mission Control."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.mission_control.cross_lane.cross_lane_contract import OBSERVED_LANES
from aethos_core.mission_control.cross_lane.lane_collectors import (
    _read_json_dir,
    collect_durable_jobs,
    collect_incident_command,
    collect_multi_agent,
    collect_production_governance,
    collect_railway_orchestration,
    collect_route_diagnostics,
    collect_software_delivery,
)
from aethos_core.mission_control.cross_lane.lane_drilldown_contract import (
    LANE_DRILLDOWN_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_131,
)

_DATA_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class LaneDrilldownResult:
    ok: bool
    lane: str
    session_id: str
    sections: list[dict[str, Any]] = field(default_factory=list)
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def _section(
    *,
    section_id: str,
    title: str,
    kind: str,
    items: list[Any] | None = None,
    rows: list[dict[str, str]] | None = None,
    empty_message: str = "No records for this section.",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "section_id": section_id,
        "title": title,
        "kind": kind,
        "empty_message": empty_message,
    }
    if rows is not None:
        payload["rows"] = rows
    if items is not None:
        payload["items"] = items
    return payload


def _audit_events_from_record(record: dict[str, Any] | None, *, prefix: str) -> list[dict[str, Any]]:
    if not record:
        return []
    events = list(record.get("events") or record.get("audit_events") or [])
    out: list[dict[str, Any]] = []
    for ev in events:
        if isinstance(ev, dict):
            out.append(
                {
                    "source": prefix,
                    "timestamp": ev.get("recorded_at") or ev.get("timestamp") or "",
                    "action": ev.get("action") or ev.get("event_type") or "",
                    "detail": ev.get("detail") or ev.get("message") or "",
                }
            )
    return out


def _receipt_files(relative_dir: str, *, limit: int = 6) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for row in _read_json_dir(_DATA_ROOT / relative_dir, limit=limit):
        receipts.append(
            {
                "source_file": row.get("_source_file"),
                "recorded_at": row.get("recorded_at"),
                "phase": row.get("phase") or row.get("status"),
                "detail": row.get("detail") or row.get("summary"),
                "plan_id": row.get("plan_id"),
                "mutation_performed": row.get("mutation_performed", False),
            }
        )
    return receipts


def build_lane_drilldown(*, session_id: str, lane: str) -> LaneDrilldownResult:
    lane_key = (lane or "").strip()
    if lane_key not in OBSERVED_LANES:
        return LaneDrilldownResult(
            ok=False,
            lane=lane_key,
            session_id=session_id,
            blockers=[f"unknown_lane:{lane_key}"],
        )

    builders = {
        "software_delivery": _drilldown_software_delivery,
        "multi_agent_collaboration": _drilldown_multi_agent,
        "railway_orchestration": _drilldown_railway,
        "production_governance": _drilldown_production_governance,
        "incident_command": _drilldown_incident_command,
        "route_diagnostics": _drilldown_route_diagnostics,
        "durable_jobs": _drilldown_durable_jobs,
    }
    sections = builders[lane_key](session_id=session_id)
    return LaneDrilldownResult(
        ok=True,
        lane=lane_key,
        session_id=session_id,
        sections=sections,
        detail=f"Read-only drilldown for {lane_key}.",
    )


def _drilldown_software_delivery(*, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.software_delivery.branch_push_store import load_branch_push_for_plan
    from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan
    from aethos_core.software_delivery.github_pr_preflight_store import load_github_pr_preflight_for_plan
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
    from aethos_core.software_delivery.multi_agent.multi_agent_store import load_collaboration_for_plan
    from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
    from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
    from aethos_core.software_delivery.software_delivery_phase_2_contract import (
        SOFTWARE_DELIVERY_APPROVAL_PHRASES,
        SOFTWARE_DELIVERY_FROZEN_INVARIANTS,
        SOFTWARE_DELIVERY_LOOP_ORDER,
        SOFTWARE_DELIVERY_ROUTE_ID,
    )
    from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan
    from aethos_core.software_delivery.workspace_verification_store import load_workspace_verification_for_plan

    sd = collect_software_delivery(session_id=session_id)
    plan_id = str(sd.get("plan_id") or "")
    plan = load_issue_plan_for_session(session_id=session_id)
    preflight = load_github_pr_preflight_for_plan(plan_id=plan_id) if plan_id else None
    verification = load_workspace_verification_for_plan(plan_id=plan_id) if plan_id else None
    workspace_apply = load_workspace_application_for_plan(plan_id=plan_id) if plan_id else None
    patch = load_patch_proposal_for_plan(plan_id=plan_id) if plan_id else None
    pr_draft = load_pr_draft_for_plan(plan_id=plan_id) if plan_id else None
    branch_push = load_branch_push_for_plan(plan_id=plan_id) if plan_id else None
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    collab = load_collaboration_for_plan(plan_id=plan_id) if plan_id else None

    gates = list(sd.get("governance_gates") or [])
    pending = list(sd.get("pending_gates") or [])
    timeline = sd.get("timeline") if isinstance(sd.get("timeline"), dict) else {}
    plan_events = list(timeline.get("plan_events") or [])

    approvals: list[dict[str, Any]] = []
    if plan:
        approvals.append(
            {
                "gate": "planning_approved",
                "approved": str(plan.get("status") or "") == "planning_approved",
                "status": plan.get("status"),
                "phrase_required": True,
            }
        )
    if preflight:
        approvals.append(
            {
                "gate": "github_pr_preflight",
                "approved": bool(preflight.get("preflight_approved")),
                "status": preflight.get("status"),
                "phrase_required": True,
            }
        )
    if workspace_apply:
        approvals.append(
            {
                "gate": "workspace_apply",
                "approved": str(workspace_apply.get("status") or "") == "applied",
                "status": workspace_apply.get("status"),
                "phrase_required": True,
            }
        )

    blockers = [{"gate": g, "reason": f"gate_not_passed:{g}"} for g in pending]
    if verification and not verification.get("verification_passed"):
        blockers.append({"gate": "workspace_verification", "reason": "verification_not_passed"})

    verification_rows: list[dict[str, str]] = []
    if verification:
        verification_rows = [
            {"label": "Verification id", "value": str(verification.get("verification_id") or "—")},
            {"label": "Passed", "value": str(bool(verification.get("verification_passed")))},
            {"label": "Status", "value": str(verification.get("status") or "—")},
            {"label": "Failure class", "value": str(verification.get("failure_class") or "—")},
        ]

    receipts = (
        _receipt_files("software_delivery_github_pr_open_receipts")
        + _receipt_files("software_delivery_branch_push_receipts", limit=4)
    )
    if branch_push:
        receipts.insert(
            0,
            {
                "source_file": "branch_push_store",
                "recorded_at": branch_push.get("updated_at"),
                "phase": branch_push.get("status"),
                "detail": branch_push.get("push_summary") or "branch push record",
                "plan_id": plan_id,
                "mutation_performed": True,
            },
        )

    audit: list[dict[str, Any]] = []
    for rec, prefix in (
        (plan, "issue_plan"),
        (preflight, "github_preflight"),
        (verification, "workspace_verification"),
        (workspace_apply, "workspace_apply"),
        (patch, "patch_proposal"),
        (pr_draft, "pr_draft"),
        (branch_push, "branch_push"),
        (pr_open, "pr_open"),
    ):
        audit.extend(_audit_events_from_record(rec, prefix=prefix))

    agent_findings: list[dict[str, Any]] = []
    for output in list((collab or {}).get("agent_outputs") or []):
        if isinstance(output, dict):
            agent_findings.append(
                {
                    "agent_role_id": output.get("agent_role_id"),
                    "status": output.get("status"),
                    "summary": output.get("summary") or output.get("finding"),
                    "mutation_performed": output.get("mutation_performed", False),
                }
            )

    rollback_rows = [
        {"label": "Workspace rollback phrase governed", "value": "yes (FIX 125D contract)"},
        {"label": "Autonomous rollback", "value": "forbidden (phase 2 freeze)"},
        {"label": "Rollback snapshots", "value": "mandatory per freeze invariants"},
    ]
    if workspace_apply:
        rollback_rows.append(
            {"label": "Workspace apply status", "value": str(workspace_apply.get("status") or "—")},
        )

    contract_items = [
        {"label": "Route id", "value": SOFTWARE_DELIVERY_ROUTE_ID},
        {"label": "Loop order", "value": " → ".join(SOFTWARE_DELIVERY_LOOP_ORDER)},
        *[{"label": "Invariant", "value": inv} for inv in SOFTWARE_DELIVERY_FROZEN_INVARIANTS],
        *[{"label": "Approval phrase", "value": p[:80] + ("…" if len(p) > 80 else "")} for p in SOFTWARE_DELIVERY_APPROVAL_PHRASES[:6]],
    ]

    sections: list[dict[str, Any]] = [
        _section(
            section_id="lane_state",
            title="Lane state",
            kind="key_value",
            rows=[
                {"label": "Plan id", "value": plan_id or "—"},
                {"label": "Status", "value": str(sd.get("plan_status") or "—")},
                {"label": "Repository", "value": str(sd.get("repository") or "—")},
                {"label": "Session", "value": session_id},
            ],
        ),
        _section(
            section_id="governance_gates",
            title="Governance gates",
            kind="gate_list",
            items=gates,
            empty_message="No governance gates — start an issue plan in this session.",
        ),
        _section(
            section_id="approvals",
            title="Approvals (read-only status)",
            kind="approval_list",
            items=approvals,
            empty_message="No approval records materialized for this session plan.",
        ),
        _section(
            section_id="timeline",
            title="Software delivery timeline",
            kind="timeline",
            items=plan_events,
            empty_message="No plan timeline events yet.",
        ),
        _section(
            section_id="receipts",
            title="Durable receipts",
            kind="receipt_list",
            items=receipts,
            empty_message="No durable receipts on disk for software delivery.",
        ),
        _section(
            section_id="verification_evidence",
            title="Verification evidence",
            kind="verification_evidence",
            rows=verification_rows,
            items=[verification] if verification else [],
            empty_message="Workspace verification has not run for this plan.",
        ),
        _section(
            section_id="rollback_posture",
            title="Rollback posture",
            kind="rollback_posture",
            rows=rollback_rows,
        ),
        _section(
            section_id="blockers",
            title="Blockers",
            kind="blocker_list",
            items=blockers,
            empty_message="No active blockers — all governed gates passed or N/A.",
        ),
        _section(
            section_id="execution_contract",
            title="Execution contract (phase 2 freeze)",
            kind="execution_contract",
            items=contract_items,
        ),
        _section(
            section_id="agent_findings",
            title="Agent collaboration findings",
            kind="agent_findings",
            items=agent_findings,
            empty_message="No multi-agent collaboration outputs for this plan.",
        ),
        _section(
            section_id="audit_trail",
            title="Audit trail",
            kind="audit_trail",
            items=sorted(audit, key=lambda e: str(e.get("timestamp") or ""), reverse=True)[:40],
            empty_message="No audit events recorded in durable stores.",
        ),
    ]
    return sections


def _drilldown_multi_agent(*, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.software_delivery.multi_agent.multi_agent_contract import (
        BOUNDED_AGENT_ROLE_IDS,
        EXECUTOR_AGENT_ENABLED_FIX_127,
    )
    from aethos_core.software_delivery.multi_agent.multi_agent_store import load_collaboration_for_plan
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")
    collab = load_collaboration_for_plan(plan_id=plan_id) if plan_id else None
    lane = collect_multi_agent(session_id=session_id)
    outputs = list((collab or {}).get("agent_outputs") or [])

    return [
        _section(
            section_id="lane_state",
            title="Lane state",
            kind="key_value",
            rows=[
                {"label": "Collaboration id", "value": str(lane.get("collaboration_id") or "—")},
                {"label": "Status", "value": str(lane.get("status") or "—")},
                {"label": "Executor agent", "value": "disabled" if not EXECUTOR_AGENT_ENABLED_FIX_127 else "enabled"},
            ],
        ),
        _section(
            section_id="agent_findings",
            title="Advisory agent outputs",
            kind="agent_findings",
            items=outputs,
            empty_message="Run software delivery agent collaboration in chat to populate findings.",
        ),
        _section(
            section_id="execution_contract",
            title="Collaboration contract",
            kind="execution_contract",
            items=[
                {"label": "Advisory roles", "value": ", ".join(BOUNDED_AGENT_ROLE_IDS)},
                {"label": "Mutation performed", "value": "false"},
                {"label": "Self-authorizing", "value": "false"},
            ],
        ),
        _section(
            section_id="audit_trail",
            title="Audit trail",
            kind="audit_trail",
            items=_audit_events_from_record(collab, prefix="multi_agent"),
            empty_message="No collaboration audit events.",
        ),
    ]


def _drilldown_railway(*, session_id: str) -> list[dict[str, Any]]:
    lane = collect_railway_orchestration(session_id=session_id)
    journals = _read_json_dir(_DATA_ROOT / "railway_execution_journal", limit=5)
    receipts = _read_json_dir(_DATA_ROOT / "railway_execution_receipts", limit=8)
    receipt_items = _receipt_files("railway_execution_receipts", limit=8)

    blockers: list[dict[str, Any]] = []
    if not journals:
        blockers.append({"reason": "no_execution_journal", "detail": "No Railway execution journal on disk."})

    return [
        _section(
            section_id="lane_state",
            title="Lane state",
            kind="key_value",
            rows=[
                {"label": "Latest execution", "value": str(lane.get("latest_execution_id") or "—")},
                {"label": "Latest status", "value": str(lane.get("latest_journal_status") or "—")},
                {"label": "Session linked", "value": str(lane.get("session_linked"))},
                {"label": "Note", "value": str(lane.get("note") or "—")},
            ],
        ),
        _section(
            section_id="receipts",
            title="Execution receipts",
            kind="receipt_list",
            items=receipt_items,
            empty_message="No Railway execution receipts recorded.",
        ),
        _section(
            section_id="execution_contract",
            title="Execution contract boundary",
            kind="execution_contract",
            items=[
                {"label": "Lane", "value": "railway_orchestration"},
                {"label": "Software delivery coupling", "value": "forbidden"},
                {"label": "Mission Control mutations", "value": "disabled"},
            ],
        ),
        _section(
            section_id="audit_trail",
            title="Journal audit trail",
            kind="audit_trail",
            items=[
                {
                    "source": "railway_execution_journal",
                    "timestamp": j.get("recorded_at") or j.get("updated_at"),
                    "action": j.get("status") or j.get("phase"),
                    "detail": j.get("execution_id") or j.get("_source_file"),
                }
                for j in journals
            ],
            empty_message="No journal entries.",
        ),
        _section(
            section_id="blockers",
            title="Blockers",
            kind="blocker_list",
            items=blockers,
            empty_message="No Railway orchestration blockers detected.",
        ),
        _section(
            section_id="rollback_posture",
            title="Rollback posture",
            kind="rollback_posture",
            rows=[
                {"label": "Rollback receipts dir", "value": "data/railway_production_rollback_escalations"},
                {"label": "Live rollback from MC", "value": "not available (read-only)"},
            ],
        ),
    ]


def _drilldown_production_governance(*, session_id: str) -> list[dict[str, Any]]:
    lane = collect_production_governance(session_id=session_id)
    rollouts = _read_json_dir(_DATA_ROOT / "railway_production_rollout_journal", limit=5)
    shadows = _read_json_dir(_DATA_ROOT / "railway_production_shadow_journal", limit=5)

    return [
        _section(
            section_id="lane_state",
            title="Lane state",
            kind="key_value",
            rows=[
                {"label": "Latest rollout stage", "value": str(lane.get("latest_rollout_stage") or "—")},
                {"label": "Rollout records", "value": str(lane.get("rollout_records") or 0)},
                {"label": "Shadow records", "value": str(lane.get("shadow_records") or 0)},
                {"label": "Mutation policy", "value": str(lane.get("mutation_policy") or "—")},
            ],
        ),
        _section(
            section_id="receipts",
            title="Rollout & shadow journals",
            kind="receipt_list",
            items=[
                *[{"source_file": r.get("_source_file"), "phase": "rollout", "detail": r.get("current_stage"), "recorded_at": r.get("recorded_at")} for r in rollouts],
                *[{"source_file": s.get("_source_file"), "phase": "shadow", "detail": s.get("status"), "recorded_at": s.get("recorded_at")} for s in shadows],
            ],
            empty_message="No production governance journals.",
        ),
        _section(
            section_id="execution_contract",
            title="Governance contract",
            kind="execution_contract",
            items=[
                {"label": "Production forward", "value": "governance_only_no_live_prod_forward"},
                {"label": "Lane boundary", "value": "production_governance != software_delivery"},
            ],
        ),
        _section(
            section_id="rollback_posture",
            title="Rollback posture",
            kind="rollback_posture",
            rows=_receipt_files("railway_production_rollback_escalations", limit=3)
            and [{"label": "Escalation records", "value": str(len(_read_json_dir(_DATA_ROOT / "railway_production_rollback_escalations", limit=5)))}]
            or [{"label": "Escalation records", "value": "0"}],
        ),
    ]


def _drilldown_incident_command(*, session_id: str) -> list[dict[str, Any]]:
    lane = collect_incident_command(session_id=session_id)
    incidents = _read_json_dir(_DATA_ROOT / "railway_production_incidents", limit=8)

    return [
        _section(
            section_id="lane_state",
            title="Lane state",
            kind="key_value",
            rows=[
                {"label": "Open incidents", "value": str(lane.get("open_incidents") or 0)},
                {"label": "Total", "value": str(lane.get("incident_count") or 0)},
                {"label": "Latest id", "value": str(lane.get("latest_incident_id") or "—")},
            ],
        ),
        _section(
            section_id="timeline",
            title="Incident timeline",
            kind="timeline",
            items=[
                {
                    "timestamp": i.get("recorded_at") or i.get("opened_at"),
                    "action": i.get("status"),
                    "detail": i.get("incident_id") or i.get("title"),
                }
                for i in incidents
            ],
            empty_message="No production incidents recorded.",
        ),
        _section(
            section_id="blockers",
            title="Active incident blockers",
            kind="blocker_list",
            items=[
                {"reason": "open_incident", "incident_id": i.get("incident_id"), "status": i.get("status")}
                for i in incidents
                if str(i.get("status") or "").lower() not in {"closed", "resolved"}
            ],
            empty_message="No open production incidents.",
        ),
        _section(
            section_id="audit_trail",
            title="Incident audit trail",
            kind="audit_trail",
            items=incidents,
            empty_message="No incident records.",
        ),
    ]


def _drilldown_route_diagnostics(*, session_id: str) -> list[dict[str, Any]]:
    lane = collect_route_diagnostics(session_id=session_id)
    from aethos_core.chat.route_trace import get_last_route_trace

    trace = get_last_route_trace(session_id=session_id) or {}
    return [
        _section(
            section_id="lane_state",
            title="Route diagnostics",
            kind="key_value",
            rows=[
                {"label": "Route id", "value": str(lane.get("route_id") or "—")},
                {"label": "Module", "value": str(lane.get("matched_module") or "—")},
                {"label": "Intent", "value": str(lane.get("intent") or "—")},
                {"label": "Recorded", "value": str(lane.get("recorded_at") or "—")},
            ],
        ),
        _section(
            section_id="audit_trail",
            title="Last route trace",
            kind="record_list",
            items=[trace] if trace else [],
            empty_message="No route trace for this session yet.",
        ),
    ]


def _drilldown_durable_jobs(*, session_id: str) -> list[dict[str, Any]]:
    lane = collect_durable_jobs(session_id=session_id)
    from aethos_core.jobs.job_registry import list_durable_job_types

    job_types = list_durable_job_types()
    return [
        _section(
            section_id="lane_state",
            title="Durable job graph",
            kind="key_value",
            rows=[
                {"label": "Node count", "value": str(lane.get("node_count") or 0)},
                {"label": "Mutation jobs from MC", "value": "blocked"},
            ],
        ),
        _section(
            section_id="execution_contract",
            title="Job execution contract",
            kind="execution_contract",
            items=[{"label": j.get("id", ""), "value": j.get("description", "") or "durable job type"} for j in job_types[:20]],
            empty_message="No durable job types registered.",
        ),
    ]
