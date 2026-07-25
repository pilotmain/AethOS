# SPDX-License-Identifier: Apache-2.0
"""FIX 172 — governed task execution coordination service (coordinate without executing)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_172_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
    build_bounded_execution_participation,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_172,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_172,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172,
    CODE_WRITE_ENABLED_FIX_172,
    COORDINATION_TIER,
    EXECUTION_PERFORMED_FIX_172,
    FORBIDDEN_COORDINATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_172,
    GOVERNANCE_MUTATION_PERFORMED_FIX_172,
    GOVERNED_TASK_EXECUTION_COORDINATION_FIX,
    GOVERNED_TASK_EXECUTION_COORDINATION_INVARIANT,
    GOVERNED_TASK_EXECUTION_COORDINATION_PRINCIPLES,
    GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION,
    MERGE_DEPLOY_ENABLED_FIX_172,
    MUTATION_PERFORMED_FIX_172,
    PACKAGE_DEPENDENCY_ORDER,
    PACKAGE_LIFECYCLE_STATES,
    PR_ACTION_ENABLED_FIX_172,
    RAILWAY_MUTATION_ENABLED_FIX_172,
    TIER_ESCALATION_ENABLED_FIX_172,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
    list_governed_task_execution_coordination_records,
)


@dataclass(frozen=True)
class GovernedTaskExecutionCoordinationResult:
    ok: bool
    session_id: str
    governed_task_execution_coordination: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _packages_by_role(work_packages: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = _sections(work_packages).get("role_scoped_work_packages") or []
    return {str(row.get("agent_role_id")): row for row in rows if row.get("agent_role_id")}


def _participation_context_read(*, participation: dict[str, Any]) -> list[dict[str, Any]]:
    if not participation.get("participation_ready"):
        return [
            {
                "read_id": "pending-bounded-participation",
                "detail": "No FIX 171 bounded execution participation — coordination blocked until participation ready.",
                "coordination_ready": False,
                "read_only": True,
            }
        ]
    envelope_read = (_sections(participation).get("authorization_envelope_read") or [{}])[0]
    return [
        {
            "read_id": "participation-context-read",
            "participation_ready": participation.get("participation_ready"),
            "participation_tier": participation.get("participation_tier"),
            "allowed_lanes": envelope_read.get("allowed_lanes") or [],
            "coordination_ready": True,
            "execution_authority": False,
            "read_only": True,
        }
    ]


def _package_agent_assignments(
    *,
    work_packages: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "package_assignment_note")]
    assignments = _sections(work_packages).get("agent_package_assignments") or []
    rows: list[dict[str, Any]] = list(stored)
    for row in assignments:
        if row.get("assignment_id") == "bounded-delivery-completeness":
            rows.append(
                {
                    **row,
                    "execution_authority": False,
                    "coordination_only": True,
                    "read_only": True,
                }
            )
            continue
        rows.append(
            {
                "assignment_id": row.get("assignment_id"),
                "agent_role_id": row.get("agent_role_id"),
                "package_id": row.get("package_id"),
                "assigned": row.get("assigned"),
                "execution_authority": False,
                "coordination_only": True,
                "detail": f"Package `{row.get('package_id')}` assigned to bounded agent — coordination not execution.",
                "read_only": True,
            }
        )
    return rows


def _package_lifecycle_tracking(
    *,
    packages_by_role: dict[str, dict[str, Any]],
    coordination_ready: bool,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "lifecycle_note")]
    if not coordination_ready:
        return stored + [
            {
                "lifecycle_id": "no-lifecycle",
                "detail": "Lifecycle tracking unavailable until participation is ready.",
                "read_only": True,
            }
        ]
    rows: list[dict[str, Any]] = list(stored)
    for idx, (role_id, deps) in enumerate(PACKAGE_DEPENDENCY_ORDER):
        pkg = packages_by_role.get(role_id)
        if not pkg:
            continue
        deps_ready = all(packages_by_role.get(dep) for dep in deps)
        if not deps:
            state = "ready" if pkg else "pending"
        elif deps_ready:
            state = "coordinating" if idx < len(PACKAGE_DEPENDENCY_ORDER) - 1 else "gate_routed"
        else:
            state = "blocked"
        rows.append(
            {
                "lifecycle_id": f"lifecycle-{role_id}",
                "package_id": pkg.get("package_id"),
                "agent_role_id": role_id,
                "lifecycle_state": state if state in PACKAGE_LIFECYCLE_STATES else "pending",
                "execution_performed": False,
                "coordination_only": True,
                "read_only": True,
            }
        )
    return rows


def _dependency_and_sequencing_coordination(
    *,
    packages_by_role: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "dependency_note")]
    rows: list[dict[str, Any]] = list(stored)
    for seq, (role_id, deps) in enumerate(PACKAGE_DEPENDENCY_ORDER, start=1):
        pkg = packages_by_role.get(role_id)
        rows.append(
            {
                "sequence_step": seq,
                "agent_role_id": role_id,
                "package_id": pkg.get("package_id") if pkg else None,
                "depends_on": list(deps),
                "parallel_group": "post_verification" if role_id in {"diff_audit_agent", "delivery_agent"} else None,
                "autonomous_lane_entry": False,
                "gate_bypass": False,
                "read_only": True,
            }
        )
    return rows


def _parallel_readiness_coordination(
    *,
    packages_by_role: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    parallel_roles = ("diff_audit_agent", "delivery_agent")
    ready = [role for role in parallel_roles if packages_by_role.get(role)]
    return [
        {
            "coordination_id": "parallel-readiness-post-verification",
            "parallel_roles": list(parallel_roles),
            "ready_count": len(ready),
            "verification_prerequisite": "verification_agent",
            "verification_ready": packages_by_role.get("verification_agent") is not None,
            "gate_bypass": False,
            "coordination_only": True,
            "detail": "Parallel package readiness coordinated after verification — gates still decide.",
            "read_only": True,
        }
    ]


def _escalation_monitoring(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "escalation_note")]
    return stored + [
        {
            "monitor_id": "scope-expansion",
            "escalation_required": True,
            "autonomous_expansion": False,
            "detail": "Human re-engagement when coordination scope expands beyond envelope.",
            "read_only": True,
        },
        {
            "monitor_id": "gate-failure",
            "escalation_required": True,
            "detail": "Human re-engagement when package outcome requires gate escalation.",
            "read_only": True,
        },
        {
            "monitor_id": "merge-deploy-request",
            "escalation_required": True,
            "detail": "Human re-engagement when merge or deploy is requested.",
            "read_only": True,
        },
        {
            "monitor_id": "bounded-stage-complete",
            "escalation_required": False,
            "detail": "Package stage completion within envelope does not require re-engagement.",
            "read_only": True,
        },
    ]


def _gate_routed_package_outcomes(
    *,
    work_packages: dict[str, Any],
    participation: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "coordination_artifact")]
    gates = _sections(work_packages).get("required_package_gates") or []
    participation_gates = _sections(participation).get("gate_routed_participation") or []
    rows: list[dict[str, Any]] = list(stored)
    seen: set[str] = set()
    for row in gates[:6]:
        gate_id = str(row.get("gate_id") or "")
        if not gate_id or gate_id in seen:
            continue
        seen.add(gate_id)
        rows.append(
            {
                "outcome_id": f"package-outcome-{gate_id}",
                "gate_id": gate_id,
                "routes_through_existing_gate": True,
                "gate_bypass": False,
                "execution_performed": False,
                "detail": "Package outcome routes through existing gate — coordination does not bypass.",
                "read_only": True,
            }
        )
    for row in participation_gates[:3]:
        gate_id = str(row.get("participation_action_id") or "")
        if gate_id and gate_id not in seen:
            seen.add(gate_id)
            rows.append(
                {
                    "outcome_id": f"participation-outcome-{gate_id}",
                    "gate_id": gate_id,
                    "routes_through_existing_gate": True,
                    "gate_bypass": False,
                    "read_only": True,
                }
            )
    if not rows:
        rows.append(
            {
                "outcome_id": "gate-routed-default",
                "routes_through_existing_gate": True,
                "gate_bypass": False,
                "execution_performed": False,
                "read_only": True,
            }
        )
    return rows


def _forbidden_coordination_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_coordination_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_COORDINATION_ACTIONS
    ]
    return stored + catalog


def _next_step_coordination_sequence(
    *,
    coordination_ready: bool,
    package_count: int,
) -> list[dict[str, Any]]:
    if not coordination_ready:
        return [
            {
                "step": 1,
                "command_hint": "bounded execution participation — establish participation before coordination",
                "execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "coordination artifact: <package sequencing summary> — persist coordination record",
            "execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "assign bounded agents to work packages — track lifecycle without executing",
            "execution_performed": False,
            "read_only": True,
        },
        {
            "step": 3,
            "command_hint": f"coordinate {package_count} packages through dependency order — existing gates decide",
            "gate_bypass": False,
            "read_only": True,
        },
    ]


def _coordination_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    coordination_ready: bool,
    package_count: int,
) -> list[dict[str, Any]]:
    score = 25 + (35 if coordination_ready else 0) + min(package_count * 6, 30)
    if _by_kind(records, "coordination_artifact"):
        score += 10
    score = min(100, score)
    label = "coordinating" if score >= 80 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "governed-task-execution-coordination-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "execution_performed": EXECUTION_PERFORMED_FIX_172,
            "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_172,
            "execution_authority": False,
            "detail": "Coordination integrity — assign and track without execution authority.",
            "read_only": True,
        }
    ]


def build_governed_task_execution_coordination(
    *,
    session_id: str,
) -> GovernedTaskExecutionCoordinationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    participation_result = build_bounded_execution_participation(session_id=sid)
    participation = (
        participation_result.bounded_execution_participation if participation_result.ok else {}
    )
    packages_result = build_bounded_delivery_work_packages(session_id=sid)
    work_packages = packages_result.bounded_delivery_work_packages if packages_result.ok else {}
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
        build_bounded_multi_agent_delivery_execution,
    )

    agent_execution_result = build_bounded_multi_agent_delivery_execution(session_id=sid)
    agent_execution = (
        agent_execution_result.bounded_multi_agent_delivery_execution if agent_execution_result.ok else {}
    )

    plan_id = str(participation.get("plan_id") or work_packages.get("plan_id") or "") or None
    correlation_id = (
        str(participation.get("correlation_id") or work_packages.get("correlation_id") or "") or None
    )

    records = list_governed_task_execution_coordination_records(session_id=sid, plan_id=plan_id)
    packages_by_role = _packages_by_role(work_packages)
    package_count = len(packages_by_role)
    coordination_ready = bool(participation.get("participation_ready"))

    sections = {
        "agent_execution_context_read": [
            {
                "read_id": "fix-189-agent-execution-packages",
                "pipeline_state": agent_execution.get("pipeline_state"),
                "execution_ready": agent_execution.get("execution_ready"),
                "agent_execution_authority": False,
                "coordination_follows_agent_work": True,
                "read_only": True,
            }
        ],
        "participation_context_read": _participation_context_read(participation=participation),
        "package_agent_assignments": _package_agent_assignments(
            work_packages=work_packages,
            records=records,
        ),
        "package_lifecycle_tracking": _package_lifecycle_tracking(
            packages_by_role=packages_by_role,
            coordination_ready=coordination_ready,
            records=records,
        ),
        "dependency_and_sequencing_coordination": _dependency_and_sequencing_coordination(
            packages_by_role=packages_by_role,
            records=records,
        ),
        "parallel_readiness_coordination": _parallel_readiness_coordination(
            packages_by_role=packages_by_role,
        ),
        "escalation_monitoring": _escalation_monitoring(records=records),
        "gate_routed_package_outcomes": _gate_routed_package_outcomes(
            work_packages=work_packages,
            participation=participation,
            records=records,
        ),
        "forbidden_coordination_actions": _forbidden_coordination_actions(records=records),
        "next_step_coordination_sequence": _next_step_coordination_sequence(
            coordination_ready=coordination_ready,
            package_count=package_count,
        ),
        "coordination_integrity_scoring": _coordination_integrity_scoring(
            records=records,
            coordination_ready=coordination_ready,
            package_count=package_count,
        ),
    }

    governed_task_execution_coordination: dict[str, Any] = {
        "schema_version": GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION,
        "fix": GOVERNED_TASK_EXECUTION_COORDINATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_172,
        "execution_performed": EXECUTION_PERFORMED_FIX_172,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_172,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_172,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_172,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_172,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_172,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_172,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_172,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_172,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_172,
        "invariant": GOVERNED_TASK_EXECUTION_COORDINATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "coordination_record_count": len(records),
        "package_count": package_count,
        "coordination_tier": COORDINATION_TIER if coordination_ready else None,
        "coordination_ready": coordination_ready,
        "fix_172_certification_requirements": list(FIX_172_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "governed_task_execution_coordination_cognition": True,
        "execution_coordination_not_execution_authority": True,
        "governed_task_execution_coordination_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_TASK_EXECUTION_COORDINATION_PRINCIPLES
        ],
        "sources": {
            "bounded_execution_participation": participation_result.ok,
            "bounded_delivery_work_packages": packages_result.ok,
            "bounded_multi_agent_delivery_execution": agent_execution_result.ok,
            "participation_ready": coordination_ready,
            "coordination_records": len(records),
        },
    }
    return GovernedTaskExecutionCoordinationResult(
        ok=True,
        session_id=sid,
        governed_task_execution_coordination=governed_task_execution_coordination,
        detail="Governed task execution coordination assembled (coordinate without executing).",
    )
