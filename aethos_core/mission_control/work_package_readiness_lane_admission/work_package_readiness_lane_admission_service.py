# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — work package readiness + lane admission service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_169,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_169,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169,
    CODE_WRITE_ENABLED_FIX_169,
    FORBIDDEN_ADMISSION_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_169,
    LANE_ADMISSION_PRINCIPLES,
    LANE_ADMISSION_RECOMMENDATION_EXECUTABLE,
    MERGE_DEPLOY_ENABLED_FIX_169,
    MUTATION_PERFORMED_FIX_169,
    PACKAGE_LANE_MAP,
    PACKAGE_PREREQUISITES,
    PR_ACTION_ENABLED_FIX_169,
    RAILWAY_MUTATION_ENABLED_FIX_169,
    WORK_PACKAGE_READINESS_LANE_ADMISSION_FIX,
    WORK_PACKAGE_READINESS_LANE_ADMISSION_INVARIANT,
    WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
    list_work_package_readiness_lane_admission_records,
)


@dataclass(frozen=True)
class WorkPackageReadinessLaneAdmissionResult:
    ok: bool
    session_id: str
    work_package_readiness_lane_admission: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _packages(work_packages: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _sections(work_packages).get("role_scoped_work_packages") or []
    return [r for r in rows if r.get("agent_role_id") and r.get("package_id")]


def _eligible_lanes(handoff_sections: dict[str, Any]) -> list[str]:
    for row in handoff_sections.get("eligible_lane_mapping") or []:
        lanes = row.get("eligible_lanes") or []
        if lanes:
            return list(lanes)
    return []


def _lanes_for_role(role_id: str, eligible: list[str]) -> list[str]:
    mapped: list[str] = []
    for rid, lanes in PACKAGE_LANE_MAP:
        if rid == role_id:
            mapped = [lane for lane in lanes if not eligible or lane in eligible]
            break
    return mapped or list(eligible)


def _has_work_package_artifact(work_packages: dict[str, Any]) -> bool:
    if int(work_packages.get("work_package_record_count") or 0) > 0:
        return True
    handoff_reads = _sections(work_packages).get("handoff_artifact_read") or []
    return any(r.get("packages_ready") or r.get("content") for r in handoff_reads)


def _pending_approvals(inbox: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in inbox.get("items") or [] if item.get("status") == "pending"]


def _package_readiness_checks(
    *,
    packages: list[dict[str, Any]],
    work_packages: dict[str, Any],
    handoff: dict[str, Any],
    inbox: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "readiness_check_note")]
    handoff_sections = _sections(handoff)
    pending_approvals = _pending_approvals(inbox)
    has_artifact = _has_work_package_artifact(work_packages)
    pending_gates = handoff_sections.get("required_lane_gates") or []

    checks: list[dict[str, Any]] = list(stored)
    checks.append(
        {
            "check_id": "inputs-complete",
            "status": "pass" if packages else "fail",
            "detail": f"Role-scoped packages defined: **{len(packages)}**",
            "read_only": True,
        }
    )
    checks.append(
        {
            "check_id": "evidence-present",
            "status": "pass" if has_artifact else "fail",
            "detail": "Work package or handoff artifact recorded for readiness context.",
            "read_only": True,
        }
    )
    checks.append(
        {
            "check_id": "approvals-satisfied",
            "status": "fail" if pending_approvals else "pass",
            "pending_count": len(pending_approvals),
            "detail": "Pending approvals block lane admission until human review.",
            "autonomous_approval": False,
            "read_only": True,
        }
    )
    checks.append(
        {
            "check_id": "gates-satisfied",
            "status": "fail" if pending_gates else "pass",
            "pending_gate_count": len(pending_gates),
            "detail": "Required lane gates must pass before admission — readiness checks only.",
            "autonomous_pass": False,
            "read_only": True,
        }
    )
    return checks


def _package_readiness_by_role(
    *,
    packages: list[dict[str, Any]],
    ready_roles: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pkg in packages:
        role_id = str(pkg.get("agent_role_id") or "")
        inputs = pkg.get("inputs") or []
        outputs = pkg.get("outputs") or []
        gates = pkg.get("required_gates") or []
        prereqs_met = role_id in ready_roles or role_id == "planner_agent"
        inputs_ok = len(inputs) >= 2
        outputs_ok = len(outputs) >= 2
        ready = inputs_ok and outputs_ok and prereqs_met
        rows.append(
            {
                "readiness_id": f"readiness-{role_id}",
                "agent_role_id": role_id,
                "package_id": pkg.get("package_id"),
                "inputs_complete": inputs_ok,
                "outputs_defined": outputs_ok,
                "prerequisites_met": prereqs_met,
                "gate_count": len(gates),
                "lane_admission_ready": ready,
                "autonomous_lane_entry": False,
                "read_only": True,
            }
        )
    return rows


def _resolve_ready_roles(packages: list[dict[str, Any]]) -> set[str]:
    package_ids = {str(p.get("agent_role_id") or "") for p in packages}
    ready: set[str] = set()
    if "planner_agent" in package_ids:
        ready.add("planner_agent")
    changed = True
    while changed:
        changed = False
        for role_id, prereqs in PACKAGE_PREREQUISITES:
            if role_id in ready:
                continue
            if role_id not in package_ids:
                continue
            if all(p in ready for p in prereqs):
                ready.add(role_id)
                changed = True
    return ready


def _lane_admission_analysis(
    *,
    packages: list[dict[str, Any]],
    eligible_lanes: list[str],
    ready_roles: set[str],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "lane_mapping_note")]
    rows: list[dict[str, Any]] = list(stored)
    for pkg in packages:
        role_id = str(pkg.get("agent_role_id") or "")
        lanes = _lanes_for_role(role_id, eligible_lanes)
        admission_ready = role_id in ready_roles and bool(lanes)
        rows.append(
            {
                "analysis_id": f"admission-{role_id}",
                "agent_role_id": role_id,
                "package_id": pkg.get("package_id"),
                "eligible_lanes": lanes,
                "admission_eligible": admission_ready,
                "lane_entry": False,
                "autonomous_lane_entry": False,
                "read_only": True,
            }
        )
    if not rows:
        rows.append(
            {
                "analysis_id": "no-packages-for-admission",
                "detail": "Complete FIX 168 work packages before lane admission analysis.",
                "read_only": True,
            }
        )
    return rows


def _admission_blockers(
    *,
    packages: list[dict[str, Any]],
    work_packages: dict[str, Any],
    handoff: dict[str, Any],
    inbox: dict[str, Any],
    ready_roles: set[str],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "admission_blocker_note")]
    blockers: list[dict[str, Any]] = list(stored)

    if not _has_work_package_artifact(work_packages):
        blockers.append(
            {
                "blocker_id": "missing-evidence",
                "detail": "Work package or handoff artifact required before lane admission.",
                "read_only": True,
            }
        )

    for item in _pending_approvals(inbox)[:4]:
        blockers.append(
            {
                "blocker_id": f"missing-approval-{item.get('inbox_id')}",
                "gate_id": item.get("gate_id"),
                "detail": "Pending approval blocks lane admission.",
                "read_only": True,
            }
        )

    for pkg in packages:
        role_id = str(pkg.get("agent_role_id") or "")
        if role_id == "verification_agent" and role_id in ready_roles:
            gates = pkg.get("required_gates") or []
            if "workspace_verification" in gates:
                blockers.append(
                    {
                        "blocker_id": "missing-verification",
                        "agent_role_id": role_id,
                        "detail": "Workspace verification gate must pass before software delivery admission.",
                        "read_only": True,
                    }
                )

    for role_id, prereqs in PACKAGE_PREREQUISITES:
        if role_id not in {str(p.get("agent_role_id") or "") for p in packages}:
            continue
        if role_id not in ready_roles:
            missing = [p for p in prereqs if p not in ready_roles]
            blockers.append(
                {
                    "blocker_id": f"missing-prerequisite-{role_id}",
                    "agent_role_id": role_id,
                    "missing_prerequisites": missing,
                    "detail": f"Prerequisite packages must be ready before `{role_id}` lane admission.",
                    "read_only": True,
                }
            )

    for row in (_sections(handoff).get("remaining_blockers") or [])[:3]:
        blockers.append(
            {
                "blocker_id": "handoff-blocker",
                "blocked_entity": row.get("blocked_entity"),
                "blocked_by": row.get("blocked_by"),
                "detail": row.get("detail"),
                "read_only": True,
            }
        )

    if not blockers:
        blockers.append(
            {
                "blocker_id": "admission-review-required",
                "detail": "Human review required before authorizing lane entry.",
                "read_only": True,
            }
        )
    return blockers


def _lane_admission_package(
    *,
    packages: list[dict[str, Any]],
    eligible_lanes: list[str],
    ready_roles: set[str],
    blockers: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "lane_admission_artifact")]
    critical_blockers = [b for b in blockers if b.get("blocker_id") != "admission-review-required"]
    admission_ready = bool(packages) and bool(ready_roles) and len(critical_blockers) <= 2
    package = {
        "package_id": "lane-admission-package",
        "eligible_lane_count": len(eligible_lanes),
        "ready_agent_count": len(ready_roles),
        "admission_ready": admission_ready,
        "lane_entry": False,
        "execution_authority": False,
        "detail": "Lane admission package — eligibility for governed lanes without executing.",
        "recommendation_only": True,
        "read_only": True,
    }
    return stored + [package]


def _admission_forbidden_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "admission_forbidden_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_ADMISSION_ACTIONS
    ]
    return stored + catalog


def _admission_artifact_registry(
    *,
    records: list[dict[str, Any]],
    packages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in records]
    generated = [
        {
            "registry_id": f"admission-{pkg.get('agent_role_id')}",
            "agent_role_id": pkg.get("agent_role_id"),
            "package_id": pkg.get("package_id"),
            "persisted": False,
            "generated": True,
            "executable": False,
            "read_only": True,
        }
        for pkg in packages
    ]
    return stored + generated


def _next_step_admission_sequence(*, admission_ready: bool, eligible_lanes: list[str]) -> list[dict[str, Any]]:
    if not admission_ready:
        return [
            {
                "step": 1,
                "command_hint": "delivery work packages — confirm role-scoped packages before readiness check",
                "autonomous_execution": False,
                "read_only": True,
            },
            {
                "step": 2,
                "command_hint": "admission artifact: <lane admission summary> — persist eligibility review",
                "autonomous_execution": False,
                "read_only": True,
            },
        ]
    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "command_hint": "review lane admission package and admission blockers with human approver",
            "autonomous_execution": False,
            "read_only": True,
        }
    ]
    for idx, lane in enumerate(eligible_lanes[:3], start=2):
        steps.append(
            {
                "step": idx,
                "command_hint": f"human authorizes entry to `{lane}` — readiness does not enter autonomously",
                "lane": lane,
                "autonomous_lane_entry": False,
                "read_only": True,
            }
        )
    return steps


def _admission_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    packages: list[dict[str, Any]],
    ready_roles: set[str],
    admission_ready: bool,
) -> list[dict[str, Any]]:
    score = 25 + min(len(packages) * 10, 40) + min(len(ready_roles) * 5, 25)
    if admission_ready:
        score += 15
    if _by_kind(records, "lane_admission_artifact"):
        score += 10
    score = min(100, score)
    label = "admission_ready" if score >= 80 else "admission_partial" if score >= 50 else "admission_blocked"
    return [
        {
            "score_id": "lane-admission-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "ready_agent_count": len(ready_roles),
            "human_authorization_required": True,
            "execution_authority": False,
            "detail": "Admission integrity — evaluates lane eligibility without execution authority.",
            "read_only": True,
        }
    ]


def build_work_package_readiness_lane_admission(*, session_id: str) -> WorkPackageReadinessLaneAdmissionResult:
    sid = (session_id or "default").strip()[:64] or "default"

    wp_result = build_bounded_delivery_work_packages(session_id=sid)
    work_packages = wp_result.bounded_delivery_work_packages if wp_result.ok else {}

    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
        build_execution_handoff_coordination,
    )

    handoff_result = build_execution_handoff_coordination(session_id=sid)
    handoff_data = handoff_result.execution_handoff_coordination if handoff_result.ok else {}

    plan_id = str(work_packages.get("plan_id") or handoff_data.get("plan_id") or "") or None
    correlation_id = str(work_packages.get("correlation_id") or handoff_data.get("correlation_id") or "") or None

    records = list_work_package_readiness_lane_admission_records(session_id=sid, plan_id=plan_id)
    inbox = approval_inbox_payload(session_id=sid)

    packages = _packages(work_packages)
    ready_roles = _resolve_ready_roles(packages)
    eligible_lanes = _eligible_lanes(_sections(handoff_data))

    readiness_checks = _package_readiness_checks(
        packages=packages,
        work_packages=work_packages,
        handoff=handoff_data,
        inbox=inbox,
        records=records,
    )
    readiness_by_role = _package_readiness_by_role(packages=packages, ready_roles=ready_roles)
    admission_blockers = _admission_blockers(
        packages=packages,
        work_packages=work_packages,
        handoff=handoff_data,
        inbox=inbox,
        ready_roles=ready_roles,
        records=records,
    )
    lane_admission_pkg = _lane_admission_package(
        packages=packages,
        eligible_lanes=eligible_lanes,
        ready_roles=ready_roles,
        blockers=admission_blockers,
        records=records,
    )
    admission_ready = bool(lane_admission_pkg and lane_admission_pkg[-1].get("admission_ready"))

    sections = {
        "package_readiness_checks": readiness_checks,
        "package_readiness_by_role": readiness_by_role,
        "lane_admission_analysis": _lane_admission_analysis(
            packages=packages,
            eligible_lanes=eligible_lanes,
            ready_roles=ready_roles,
            records=records,
        ),
        "admission_blockers": admission_blockers,
        "lane_admission_package": lane_admission_pkg,
        "admission_forbidden_actions": _admission_forbidden_actions(records=records),
        "admission_artifact_registry": _admission_artifact_registry(records=records, packages=packages),
        "next_step_admission_sequence": _next_step_admission_sequence(
            admission_ready=admission_ready,
            eligible_lanes=eligible_lanes,
        ),
        "admission_integrity_scoring": _admission_integrity_scoring(
            records=records,
            packages=packages,
            ready_roles=ready_roles,
            admission_ready=admission_ready,
        ),
    }

    payload: dict[str, Any] = {
        "schema_version": WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION,
        "fix": WORK_PACKAGE_READINESS_LANE_ADMISSION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_169,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_169,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_169,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_169,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_169,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_169,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_169,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_169,
        "invariant": WORK_PACKAGE_READINESS_LANE_ADMISSION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "lane_admission_record_count": len(records),
        "agent_package_count": len(packages),
        "ready_agent_count": len(ready_roles),
        "eligible_lane_count": len(eligible_lanes),
        "selected_path_id": work_packages.get("selected_path_id") or handoff_data.get("selected_path_id"),
        "all_recommendations_executable": False,
        "work_package_readiness_lane_admission_cognition": True,
        "lane_admission_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in LANE_ADMISSION_PRINCIPLES
        ],
        "sources": {
            "bounded_delivery_work_packages": wp_result.ok,
            "execution_handoff_coordination": handoff_result.ok,
            "work_package_records": work_packages.get("work_package_record_count", 0),
            "lane_admission_records": len(records),
        },
    }
    return WorkPackageReadinessLaneAdmissionResult(
        ok=True,
        session_id=sid,
        work_package_readiness_lane_admission=payload,
        detail="Work package readiness + lane admission assembled (recommendation-only — no execution authority).",
    )
