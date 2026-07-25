# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — gate-routed package outcome review service (review before lane action)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_173_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_173,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_173,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173,
    CODE_WRITE_ENABLED_FIX_173,
    EXECUTION_PERFORMED_FIX_173,
    FORBIDDEN_REVIEW_ACTIONS,
    FORBIDDEN_REVIEW_LANES,
    FROZEN_SOFTWARE_DELIVERY_GATES,
    GATE_BYPASS_ENABLED_FIX_173,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_FIX,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_INVARIANT,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_PRINCIPLES,
    GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_173,
    MERGE_DEPLOY_ENABLED_FIX_173,
    MUTATION_PERFORMED_FIX_173,
    PR_ACTION_ENABLED_FIX_173,
    RAILWAY_MUTATION_ENABLED_FIX_173,
    REVIEW_TIER,
    TIER_ESCALATION_ENABLED_FIX_173,
)
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
    list_gate_routed_package_outcome_review_records,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_service import (
    build_governed_task_execution_coordination,
)


@dataclass(frozen=True)
class GateRoutedPackageOutcomeReviewResult:
    ok: bool
    session_id: str
    gate_routed_package_outcome_review: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _quality_for_state(state: str | None) -> str:
    if state == "gate_routed":
        return "complete"
    if state == "coordinating":
        return "partial"
    if state == "blocked":
        return "blocked"
    if state == "ready":
        return "partial"
    return "incomplete"


def _coordination_context_read(*, coordination: dict[str, Any]) -> list[dict[str, Any]]:
    if not coordination.get("coordination_ready"):
        return [
            {
                "read_id": "pending-coordination",
                "detail": "No FIX 172 execution coordination — gate review blocked until coordination ready.",
                "review_ready": False,
                "read_only": True,
            }
        ]
    ctx = (_sections(coordination).get("participation_context_read") or [{}])[0]
    return [
        {
            "read_id": "coordination-context-read",
            "coordination_ready": coordination.get("coordination_ready"),
            "package_count": coordination.get("package_count"),
            "allowed_lanes": ctx.get("allowed_lanes") or [],
            "review_ready": True,
            "execution_authority": False,
            "read_only": True,
        }
    ]


def _package_outcome_collection(
    *,
    coordination: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "gate_review_artifact")]
    outcomes = _sections(coordination).get("gate_routed_package_outcomes") or []
    lifecycle = _sections(coordination).get("package_lifecycle_tracking") or []
    rows: list[dict[str, Any]] = list(stored)
    for row in lifecycle:
        if not row.get("lifecycle_id"):
            continue
        gate_outcomes = [
            o for o in outcomes if o.get("gate_id") and row.get("agent_role_id")
        ]
        rows.append(
            {
                "outcome_id": row.get("lifecycle_id"),
                "package_id": row.get("package_id"),
                "agent_role_id": row.get("agent_role_id"),
                "lifecycle_state": row.get("lifecycle_state"),
                "outcome_source": "fix_172_coordination",
                "execution_performed": False,
                "read_only": True,
            }
        )
    for row in outcomes:
        if row.get("outcome_id"):
            rows.append({**row, "outcome_source": "fix_172_gate_routed", "read_only": True})
    if not rows:
        rows.append(
            {
                "outcome_id": "no-outcomes",
                "detail": "No package outcomes available until coordination produces lifecycle and gate routes.",
                "read_only": True,
            }
        )
    return rows


def _outcome_quality_classification(*, coordination: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(coordination).get("package_lifecycle_tracking") or []:
        if not row.get("lifecycle_id"):
            continue
        state = str(row.get("lifecycle_state") or "pending")
        quality = _quality_for_state(state)
        rows.append(
            {
                "classification_id": f"quality-{row.get('agent_role_id')}",
                "package_id": row.get("package_id"),
                "agent_role_id": row.get("agent_role_id"),
                "lifecycle_state": state,
                "outcome_quality": quality,
                "approval_bypass": False,
                "read_only": True,
            }
        )
    if not rows:
        rows.append(
            {
                "classification_id": "no-quality-data",
                "outcome_quality": "incomplete",
                "detail": "Outcome quality unavailable until packages are coordinated.",
                "read_only": True,
            }
        )
    return rows


def _incomplete_package_detection(*, coordination: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "incomplete_package_note")]
    incomplete: list[dict[str, Any]] = list(stored)
    for row in _sections(coordination).get("package_lifecycle_tracking") or []:
        state = str(row.get("lifecycle_state") or "")
        if state in {"pending", "blocked"}:
            incomplete.append(
                {
                    "detection_id": f"incomplete-{row.get('agent_role_id')}",
                    "package_id": row.get("package_id"),
                    "agent_role_id": row.get("agent_role_id"),
                    "lifecycle_state": state,
                    "incomplete": True,
                    "lane_entry_blocked": True,
                    "read_only": True,
                }
            )
    if not incomplete:
        incomplete.append(
            {
                "detection_id": "all-packages-addressed",
                "incomplete": False,
                "detail": "No incomplete packages detected in current coordination lifecycle.",
                "read_only": True,
            }
        )
    return incomplete


def _escalation_trigger_detection(
    *,
    coordination: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "escalation_review_note")]
    triggers: list[dict[str, Any]] = list(stored)
    for row in _sections(coordination).get("escalation_monitoring") or []:
        if row.get("monitor_id"):
            triggers.append({**row, "read_only": True})
    blocked_count = sum(
        1
        for row in _sections(coordination).get("package_lifecycle_tracking") or []
        if row.get("lifecycle_state") == "blocked"
    )
    if blocked_count:
        triggers.append(
            {
                "trigger_id": "blocked-packages",
                "escalation_required": True,
                "blocked_package_count": blocked_count,
                "detail": "Blocked packages require human re-engagement before lane handoff.",
                "read_only": True,
            }
        )
    return triggers


def _frozen_gate_mapping(
    *,
    coordination: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "gate_mapping_note")]
    mappings: list[dict[str, Any]] = list(stored)
    seen: set[str] = set()
    for row in _sections(coordination).get("gate_routed_package_outcomes") or []:
        gate_id = str(row.get("gate_id") or "")
        if not gate_id or gate_id in seen:
            continue
        seen.add(gate_id)
        frozen = gate_id in FROZEN_SOFTWARE_DELIVERY_GATES or any(
            gate_id.startswith(f"{g}") or g in gate_id for g in FROZEN_SOFTWARE_DELIVERY_GATES
        )
        forbidden = any(lane in gate_id for lane in FORBIDDEN_REVIEW_LANES)
        mappings.append(
            {
                "mapping_id": f"map-{gate_id}",
                "gate_id": gate_id,
                "frozen_software_delivery_gate": frozen and not forbidden,
                "forbidden_lane": forbidden,
                "gate_bypass": False,
                "routes_through_existing_gate": True,
                "read_only": True,
            }
        )
    if not mappings:
        for gate in FROZEN_SOFTWARE_DELIVERY_GATES[:3]:
            mappings.append(
                {
                    "mapping_id": f"map-default-{gate}",
                    "gate_id": gate,
                    "frozen_software_delivery_gate": True,
                    "gate_bypass": False,
                    "detail": "Default frozen gate mapping — outcomes route here when coordination completes.",
                    "read_only": True,
                }
            )
    return mappings


def _gate_review_packet(
    *,
    coordination: dict[str, Any],
    quality_rows: list[dict[str, Any]],
    incomplete_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    complete = sum(1 for q in quality_rows if q.get("outcome_quality") == "complete")
    partial = sum(1 for q in quality_rows if q.get("outcome_quality") == "partial")
    incomplete = sum(1 for q in quality_rows if q.get("outcome_quality") in {"incomplete", "blocked"})
    return [
        {
            "packet_id": "gate-review-packet",
            "coordination_session": coordination.get("session_id"),
            "package_count": coordination.get("package_count"),
            "outcomes_complete": complete,
            "outcomes_partial": partial,
            "outcomes_incomplete": incomplete,
            "incomplete_packages_detected": any(r.get("incomplete") for r in incomplete_rows),
            "execution_performed": False,
            "approval_bypass": False,
            "gate_bypass": False,
            "detail": "Gate review packet — ready for handoff to existing frozen software delivery gates.",
            "read_only": True,
        }
    ]


def _gate_handler_routing(*, coordination: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    quality_by_role = {
        str(q.get("agent_role_id")): q.get("outcome_quality")
        for q in _outcome_quality_classification(coordination=coordination)
        if q.get("agent_role_id")
    }
    for row in _sections(coordination).get("gate_routed_package_outcomes") or []:
        gate_id = str(row.get("gate_id") or "")
        if not gate_id:
            continue
        routes.append(
            {
                "route_id": row.get("outcome_id"),
                "gate_id": gate_id,
                "handling_gate": gate_id,
                "lane": "software_delivery",
                "gate_bypass": False,
                "execution_performed": False,
                "detail": f"Outcome routes to frozen gate `{gate_id}` — existing gate decides lane action.",
                "read_only": True,
            }
        )
    for assignment in _sections(coordination).get("package_agent_assignments") or []:
        role = str(assignment.get("agent_role_id") or "")
        pkg = assignment.get("package_id")
        if not role or not pkg:
            continue
        quality = quality_by_role.get(role, "incomplete")
        default_gate = "workspace_verification" if role == "verification_agent" else "implementation_plan"
        routes.append(
            {
                "route_id": f"handler-{role}",
                "package_id": pkg,
                "agent_role_id": role,
                "outcome_quality": quality,
                "handling_gate": default_gate,
                "lane": "software_delivery",
                "gate_bypass": False,
                "read_only": True,
            }
        )
    return routes[:8]


def _forbidden_review_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_review_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_REVIEW_ACTIONS
    ]
    return stored + catalog


def _next_step_gate_review_sequence(*, review_ready: bool, outcome_count: int) -> list[dict[str, Any]]:
    if not review_ready:
        return [
            {
                "step": 1,
                "command_hint": "governed task execution coordination — coordinate packages before gate review",
                "execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "gate review artifact: <outcome summary> — persist gate review record",
            "execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "review outcome quality and incomplete packages — map to frozen gates",
            "gate_bypass": False,
            "read_only": True,
        },
        {
            "step": 3,
            "command_hint": f"hand {outcome_count} coordinated outcomes to existing gates — review does not execute",
            "execution_performed": False,
            "read_only": True,
        },
    ]


def _gate_review_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    review_ready: bool,
    outcome_count: int,
    incomplete_count: int,
) -> list[dict[str, Any]]:
    score = 25 + (35 if review_ready else 0) + min(outcome_count * 5, 25)
    if incomplete_count == 0 and review_ready:
        score += 10
    if _by_kind(records, "gate_review_artifact"):
        score += 10
    score = min(100, score)
    label = "review_ready" if score >= 80 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "gate-routed-outcome-review-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "execution_performed": EXECUTION_PERFORMED_FIX_173,
            "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_173,
            "execution_authority": False,
            "detail": "Gate review integrity — classify and map without execution authority.",
            "read_only": True,
        }
    ]


def build_gate_routed_package_outcome_review(*, session_id: str) -> GateRoutedPackageOutcomeReviewResult:
    sid = (session_id or "default").strip()[:64] or "default"

    coordination_result = build_governed_task_execution_coordination(session_id=sid)
    coordination = (
        coordination_result.governed_task_execution_coordination if coordination_result.ok else {}
    )

    plan_id = str(coordination.get("plan_id") or "") or None
    correlation_id = str(coordination.get("correlation_id") or "") or None

    records = list_gate_routed_package_outcome_review_records(session_id=sid, plan_id=plan_id)
    review_ready = bool(coordination.get("coordination_ready"))
    outcome_collection = _package_outcome_collection(coordination=coordination, records=records)
    quality_rows = _outcome_quality_classification(coordination=coordination)
    incomplete_rows = _incomplete_package_detection(coordination=coordination, records=records)
    incomplete_count = sum(1 for r in incomplete_rows if r.get("incomplete"))

    sections = {
        "coordination_context_read": _coordination_context_read(coordination=coordination),
        "package_outcome_collection": outcome_collection,
        "outcome_quality_classification": quality_rows,
        "incomplete_package_detection": incomplete_rows,
        "escalation_trigger_detection": _escalation_trigger_detection(
            coordination=coordination,
            records=records,
        ),
        "frozen_gate_mapping": _frozen_gate_mapping(coordination=coordination, records=records),
        "gate_review_packet": _gate_review_packet(
            coordination=coordination,
            quality_rows=quality_rows,
            incomplete_rows=incomplete_rows,
        ),
        "gate_handler_routing": _gate_handler_routing(coordination=coordination),
        "forbidden_review_actions": _forbidden_review_actions(records=records),
        "next_step_gate_review_sequence": _next_step_gate_review_sequence(
            review_ready=review_ready,
            outcome_count=len(outcome_collection),
        ),
        "gate_review_integrity_scoring": _gate_review_integrity_scoring(
            records=records,
            review_ready=review_ready,
            outcome_count=len(outcome_collection),
            incomplete_count=incomplete_count,
        ),
    }

    gate_routed_package_outcome_review: dict[str, Any] = {
        "schema_version": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION,
        "fix": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_173,
        "execution_performed": EXECUTION_PERFORMED_FIX_173,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_173,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_173,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_173,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_173,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_173,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_173,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_173,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_173,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_173,
        "invariant": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "gate_review_record_count": len(records),
        "outcome_count": len(outcome_collection),
        "incomplete_package_count": incomplete_count,
        "review_tier": REVIEW_TIER if review_ready else None,
        "review_ready": review_ready,
        "fix_173_certification_requirements": list(FIX_173_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "gate_routed_package_outcome_review_cognition": True,
        "review_not_execution_authority": True,
        "gate_routed_package_outcome_review_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_PRINCIPLES
        ],
        "sources": {
            "governed_task_execution_coordination": coordination_result.ok,
            "coordination_ready": review_ready,
            "gate_review_records": len(records),
        },
    }
    return GateRoutedPackageOutcomeReviewResult(
        ok=True,
        session_id=sid,
        gate_routed_package_outcome_review=gate_routed_package_outcome_review,
        detail="Gate-routed package outcome review assembled (review before lane action — existing gates decide).",
    )
