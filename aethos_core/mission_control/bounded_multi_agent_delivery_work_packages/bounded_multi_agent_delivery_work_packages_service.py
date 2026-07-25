# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — bounded multi-agent delivery work packages service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_168,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_168,
    BOUNDED_DELIVERY_AGENT_ROLE_IDS,
    BOUNDED_DELIVERY_WORK_PACKAGES_FIX,
    BOUNDED_DELIVERY_WORK_PACKAGES_INVARIANT,
    BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION,
    CODE_WRITE_ENABLED_FIX_168,
    DELIVERY_AGENT_CATALOG,
    FORBIDDEN_PACKAGE_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_168,
    MERGE_DEPLOY_ENABLED_FIX_168,
    MUTATION_PERFORMED_FIX_168,
    PR_ACTION_ENABLED_FIX_168,
    RAILWAY_MUTATION_ENABLED_FIX_168,
    WORK_PACKAGES_PRINCIPLES,
    WORK_PACKAGES_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_roles import (
    PACKAGE_RUNNERS,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
    list_bounded_delivery_work_packages_records,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
    build_execution_handoff_coordination,
)


@dataclass(frozen=True)
class BoundedDeliveryWorkPackagesResult:
    ok: bool
    session_id: str
    bounded_delivery_work_packages: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _handoff_artifact_read(*, handoff: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "work_package_artifact")]
    handoff_pkg = _sections(handoff).get("execution_handoff_package") or []
    artifact_rows = [r for r in handoff_pkg if r.get("content") or r.get("package_id")]
    if not artifact_rows and not stored:
        return [
            {
                "read_id": "pending-handoff-artifact",
                "detail": "No handoff artifact recorded — work packages require FIX 167 handoff context.",
                "packages_ready": False,
                "read_only": True,
            }
        ]
    reads: list[dict[str, Any]] = list(stored)
    for row in artifact_rows:
        if row.get("content"):
            reads.append({**row, "source": "handoff_record", "read_only": True})
        elif row.get("package_id"):
            reads.append(
                {
                    "read_id": row.get("package_id"),
                    "selected_path": handoff.get("selected_path_id"),
                    "eligible_lane_count": handoff.get("eligible_lane_count", 0),
                    "execution_authority": False,
                    "packages_ready": True,
                    "read_only": True,
                }
            )
    return reads


def _generate_packages(*, handoff: dict[str, Any], plan_id: str | None) -> list[dict[str, Any]]:
    packages: list[dict[str, Any]] = []
    for role_id in BOUNDED_DELIVERY_AGENT_ROLE_IDS:
        runner = PACKAGE_RUNNERS.get(role_id)
        if not runner:
            continue
        packages.append(runner(handoff=handoff, plan_id=plan_id))
    return packages


def _role_scoped_work_packages(
    *,
    packages: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "work_package_artifact")]
    return stored + packages


def _agent_package_assignments(*, packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for role_id, display, focus in DELIVERY_AGENT_CATALOG:
        pkg = next((p for p in packages if p.get("agent_role_id") == role_id), None)
        assignments.append(
            {
                "assignment_id": f"assign-{role_id}",
                "agent_role_id": role_id,
                "display_name": display,
                "focus": focus,
                "package_id": pkg.get("package_id") if pkg else None,
                "assigned": pkg is not None,
                "execution_authority": False,
                "read_only": True,
            }
        )
    assignments.append(
        {
            "assignment_id": "bounded-delivery-completeness",
            "agent_count": len(packages),
            "bounded_roles": list(BOUNDED_DELIVERY_AGENT_ROLE_IDS),
            "executor_agent_enabled": False,
            "read_only": True,
        }
    )
    return assignments


def _package_inputs_outputs(*, packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pkg in packages:
        rows.append(
            {
                "package_id": pkg.get("package_id"),
                "agent_role_id": pkg.get("agent_role_id"),
                "inputs": pkg.get("inputs") or [],
                "outputs": pkg.get("outputs") or [],
                "executable": False,
                "read_only": True,
            }
        )
    return rows


def _required_package_gates(
    *,
    packages: list[dict[str, Any]],
    handoff: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "package_gate_note")]
    gates: list[dict[str, Any]] = list(stored)
    seen: set[str] = set()
    for pkg in packages:
        for gate in pkg.get("required_gates") or []:
            gate_id = str(gate)
            if gate_id in seen:
                continue
            seen.add(gate_id)
            gates.append(
                {
                    "gate_id": gate_id,
                    "agent_role_id": pkg.get("agent_role_id"),
                    "gate_passed": False,
                    "autonomous_pass": False,
                    "read_only": True,
                }
            )
    for row in (_sections(handoff).get("required_lane_gates") or [])[:4]:
        gate_id = str(row.get("gate_id") or "")
        if gate_id and gate_id not in seen:
            seen.add(gate_id)
            gates.append({**row, "source": "handoff", "read_only": True})
    if not gates:
        gates.append(
            {
                "gate_id": "handoff-gates-required",
                "detail": "Complete FIX 167 handoff before package gate sequencing.",
                "read_only": True,
            }
        )
    return gates


def _package_forbidden_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "package_forbidden_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_PACKAGE_ACTIONS
    ]
    return stored + catalog


def _package_artifact_registry(*, records: list[dict[str, Any]], packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in records]
    generated = [
        {
            "registry_id": pkg.get("package_id"),
            "agent_role_id": pkg.get("agent_role_id"),
            "title": pkg.get("title"),
            "persisted": False,
            "generated": True,
            "executable": False,
            "read_only": True,
        }
        for pkg in packages
    ]
    return stored + generated


def _next_step_readiness_sequence(*, handoff: dict[str, Any], packages_ready: bool) -> list[dict[str, Any]]:
    if not packages_ready:
        return [
            {
                "step": 1,
                "command_hint": "execution handoff — confirm handoff artifact before work packages",
                "autonomous_execution": False,
                "read_only": True,
            }
        ]
    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "command_hint": "review role-scoped work packages for each bounded agent",
            "autonomous_execution": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "work package artifact: <scoped package summary> — persist for human review",
            "autonomous_execution": False,
            "read_only": True,
        },
    ]
    for idx, row in enumerate((_sections(handoff).get("next_step_command_sequence") or [])[:3], start=3):
        steps.append(
            {
                "step": idx,
                "command_hint": row.get("command_hint"),
                "source": "handoff",
                "autonomous_execution": False,
                "read_only": True,
            }
        )
    return steps


def _delivery_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    packages: list[dict[str, Any]],
    packages_ready: bool,
) -> list[dict[str, Any]]:
    score = 30 + (25 if packages_ready else 0) + min(len(packages) * 8, 40) + min(len(records) * 2, 10)
    has_artifact = bool(_by_kind(records, "work_package_artifact"))
    if has_artifact:
        score += 10
    score = min(100, score)
    label = "packages_ready" if score >= 80 else "packages_partial" if score >= 50 else "packages_blocked"
    return [
        {
            "score_id": "delivery-work-packages-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "agent_packages_generated": len(packages),
            "human_review_required": True,
            "execution_authority": False,
            "detail": "Work package integrity — scopes bounded delivery without execution authority.",
            "read_only": True,
        }
    ]


def build_bounded_delivery_work_packages(*, session_id: str) -> BoundedDeliveryWorkPackagesResult:
    sid = (session_id or "default").strip()[:64] or "default"

    handoff_result = build_execution_handoff_coordination(session_id=sid)
    handoff = handoff_result.execution_handoff_coordination if handoff_result.ok else {}

    plan_id = str(handoff.get("plan_id") or "") or None
    correlation_id = str(handoff.get("correlation_id") or "") or None

    records = list_bounded_delivery_work_packages_records(session_id=sid, plan_id=plan_id)
    packages = _generate_packages(handoff=handoff, plan_id=plan_id)
    packages_ready = handoff.get("selected_path_id") is not None and handoff.get("selected_path_id") != "hold_no_go_path"

    sections = {
        "handoff_artifact_read": _handoff_artifact_read(handoff=handoff, records=records),
        "role_scoped_work_packages": _role_scoped_work_packages(packages=packages, records=records),
        "agent_package_assignments": _agent_package_assignments(packages=packages),
        "package_inputs_outputs": _package_inputs_outputs(packages=packages),
        "required_package_gates": _required_package_gates(packages=packages, handoff=handoff, records=records),
        "package_forbidden_actions": _package_forbidden_actions(records=records),
        "package_artifact_registry": _package_artifact_registry(records=records, packages=packages),
        "next_step_readiness_sequence": _next_step_readiness_sequence(handoff=handoff, packages_ready=packages_ready),
        "delivery_integrity_scoring": _delivery_integrity_scoring(
            records=records,
            packages=packages,
            packages_ready=packages_ready,
        ),
    }

    bounded_delivery_work_packages: dict[str, Any] = {
        "schema_version": BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION,
        "fix": BOUNDED_DELIVERY_WORK_PACKAGES_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_168,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_168,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_168,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_168,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_168,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_168,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_168,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_168,
        "invariant": BOUNDED_DELIVERY_WORK_PACKAGES_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "work_package_record_count": len(records),
        "agent_package_count": len(packages),
        "selected_path_id": handoff.get("selected_path_id"),
        "all_recommendations_executable": False,
        "bounded_delivery_work_packages_cognition": True,
        "bounded_multi_agent_delivery": True,
        "work_packages_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in WORK_PACKAGES_PRINCIPLES
        ],
        "sources": {
            "execution_handoff_coordination": handoff_result.ok,
            "handoff_artifact_available": packages_ready,
            "work_package_records": len(records),
            "bounded_agent_roles": list(BOUNDED_DELIVERY_AGENT_ROLE_IDS),
        },
    }
    return BoundedDeliveryWorkPackagesResult(
        ok=True,
        session_id=sid,
        bounded_delivery_work_packages=bounded_delivery_work_packages,
        detail="Bounded delivery work packages assembled (recommendation-only — no execution authority).",
    )
