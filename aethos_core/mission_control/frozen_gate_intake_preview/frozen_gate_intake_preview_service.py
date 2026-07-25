# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — frozen gate intake preview (composes FIX 177)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable

from aethos_core.governance.governance_friction_approval_contract import FIX_178_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_178,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_178,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178,
    CODE_WRITE_ENABLED_FIX_178,
    EXECUTION_PERFORMED_FIX_178,
    FORBIDDEN_INTAKE_ACTIONS,
    FROZEN_GATE_INTAKE_PREVIEW_FIX,
    FROZEN_GATE_INTAKE_PREVIEW_INVARIANT,
    FROZEN_GATE_INTAKE_PREVIEW_PRINCIPLES,
    FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION,
    FROZEN_SOFTWARE_DELIVERY_GATES,
    GATE_BYPASS_ENABLED_FIX_178,
    GATE_EXECUTION_PERFORMED_FIX_178,
    GATE_EXISTING_COMMAND_HINTS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_178,
    HANDOFF_PACKET_SHAPE_FIELDS,
    INTAKE_PREVIEW_TIER,
    LANE_ADMISSION_EXECUTED_FIX_178,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
    MERGE_DEPLOY_ENABLED_FIX_178,
    MUTATION_PERFORMED_FIX_178,
    PR_ACTION_ENABLED_FIX_178,
    RAILWAY_MUTATION_ENABLED_FIX_178,
    TIER_ESCALATION_ENABLED_FIX_178,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_177,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
    list_frozen_gate_intake_preview_records,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
    build_gate_routed_lane_entry_handoff,
)


@dataclass(frozen=True)
class FrozenGateIntakePreviewResult:
    ok: bool
    session_id: str
    frozen_gate_intake_preview: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _handoff_packet(handoff: dict[str, Any]) -> dict[str, Any]:
    rows = _sections(handoff).get("gate_handoff_packet") or []
    return rows[0] if rows else {}


def _handoff_upstream_read(*, handoff: dict[str, Any]) -> list[dict[str, Any]]:
    packet = _handoff_packet(handoff)
    return [
        {
            "read_id": "fix-177-handoff-read",
            "upstream_fix": "FIX 177",
            "handoff_ready": handoff.get("handoff_ready"),
            "target_gate_id": handoff.get("target_gate_id"),
            "decision_value": packet.get("decision_value"),
            "read_only": True,
            "recomputed_by_fix_178": False,
        }
    ]


def _matching_frozen_gate_identification(
    *,
    handoff: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "gate_match_note")]
    gate_id = handoff.get("target_gate_id")
    rows: list[dict[str, Any]] = list(stored)
    if gate_id:
        rows.append(
            {
                "match_id": f"match-{gate_id}",
                "gate_id": gate_id,
                "frozen_software_delivery_gate": gate_id in FROZEN_SOFTWARE_DELIVERY_GATES,
                "handoff_ready": handoff.get("handoff_ready"),
                "gate_execution_performed": False,
                "lane_entry_execution_performed": False,
                "read_only": True,
            }
        )
    if not rows:
        rows.append(
            {
                "match_id": "pending-gate",
                "detail": "Matching frozen gate unidentified until FIX 177 handoff targets a gate.",
                "read_only": True,
            }
        )
    return rows


def _validate_packet_shape(*, handoff: dict[str, Any]) -> list[dict[str, Any]]:
    packet = _handoff_packet(handoff)
    if not packet:
        return [
            {
                "validation_id": "packet-missing",
                "valid": False,
                "detail": "FIX 177 gate handoff packet missing — intake preview blocked.",
                "read_only": True,
            }
        ]

    missing_fields = [f for f in HANDOFF_PACKET_SHAPE_FIELDS if f not in packet]
    invalid_flags = []
    if packet.get("lane_entry_execution_performed") is True:
        invalid_flags.append("lane_entry_execution_performed")
    if packet.get("gate_bypass") is True:
        invalid_flags.append("gate_bypass")
    if packet.get("approval_bypass") is True:
        invalid_flags.append("approval_bypass")

    valid = not missing_fields and not invalid_flags and bool(packet.get("target_gate_id"))
    return [
        {
            "validation_id": "handoff-packet-shape",
            "valid": valid,
            "missing_fields": missing_fields,
            "invalid_flags": invalid_flags,
            "target_gate_id": packet.get("target_gate_id"),
            "decision_value": packet.get("decision_value"),
            "detail": "Handoff packet shape valid for intake preview."
            if valid
            else "Handoff packet shape incomplete or invalid for intake preview.",
            "read_only": True,
        }
    ]


def _intake_preview_packet(
    *,
    handoff: dict[str, Any],
    gate_id: str | None,
    shape_valid: bool,
    intake_preview_ready: bool,
) -> list[dict[str, Any]]:
    packet = _handoff_packet(handoff)
    return [
        {
            "preview_id": "frozen-gate-intake-preview-packet",
            "target_gate_id": gate_id,
            "decision_value": packet.get("decision_value"),
            "intake_preview_ready": intake_preview_ready and shape_valid and bool(gate_id),
            "gate_execution_performed": False,
            "lane_entry_execution_performed": False,
            "lane_admission_executed": False,
            "gate_bypass": False,
            "approval_bypass": False,
            "detail": "Frozen gate intake preview — gate execution remains in frozen lane.",
            "read_only": True,
        }
    ]


def _lane_entry_confirmation() -> list[dict[str, Any]]:
    return [
        {
            "confirmation_id": "no-lane-entry",
            "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
            "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_178,
            "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_178,
            "detail": "Intake preview confirms no lane entry or gate execution performed.",
            "read_only": True,
        }
    ]


def _prerequisite_checkers() -> dict[str, list[tuple[str, str, Callable[..., bool]]]]:
    def _plan_exists(*, session_id: str, plan_id: str) -> bool:
        from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

        plan = load_issue_plan_for_session(session_id=session_id)
        return bool(plan) and (not plan_id or str(plan.get("plan_id") or "") == plan_id)

    def _planning_approved(*, session_id: str, plan_id: str) -> bool:
        from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

        plan = load_issue_plan_for_session(session_id=session_id)
        return str((plan or {}).get("status") or "") == "planning_approved"

    def _patch_proposal_approved(*, session_id: str, plan_id: str) -> bool:
        from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
        from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan

        plan = load_issue_plan_for_session(session_id=session_id)
        pid = plan_id or str((plan or {}).get("plan_id") or "")
        if not pid:
            return False
        patch = load_patch_proposal_for_plan(plan_id=pid)
        return str((patch or {}).get("status") or "") == "approved"

    def _workspace_applied(*, session_id: str, plan_id: str) -> bool:
        from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
        from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan

        plan = load_issue_plan_for_session(session_id=session_id)
        pid = plan_id or str((plan or {}).get("plan_id") or "")
        if not pid:
            return False
        apply_rec = load_workspace_application_for_plan(plan_id=pid)
        return str((apply_rec or {}).get("status") or "") == "applied"

    def _workspace_verification_passed(*, session_id: str, plan_id: str) -> bool:
        from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
        from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

        plan = load_issue_plan_for_session(session_id=session_id)
        pid = plan_id or str((plan or {}).get("plan_id") or "")
        return workspace_verification_passed(plan_id=pid) if pid else False

    def _github_preflight_approved(*, session_id: str, plan_id: str) -> bool:
        from aethos_core.software_delivery.github_pr_preflight_store import (
            github_pr_creation_approved_for_plan,
        )
        from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

        plan = load_issue_plan_for_session(session_id=session_id)
        pid = plan_id or str((plan or {}).get("plan_id") or "")
        return github_pr_creation_approved_for_plan(plan_id=pid) if pid else False

    return {
        "issue_intake": [("issue_intake", "Issue plan exists", _plan_exists)],
        "implementation_plan": [
            ("issue_intake", "Issue plan exists", _plan_exists),
        ],
        "planning_approved": [
            ("issue_intake", "Issue plan exists", _plan_exists),
        ],
        "patch_proposal_approved": [
            ("issue_intake", "Issue plan exists", _plan_exists),
            ("planning_approved", "Planning approved", _planning_approved),
        ],
        "workspace_apply_approved": [
            ("issue_intake", "Issue plan exists", _plan_exists),
            ("planning_approved", "Planning approved", _planning_approved),
            ("patch_proposal_approved", "Patch proposal approved", _patch_proposal_approved),
        ],
        "workspace_verification": [
            ("issue_intake", "Issue plan exists", _plan_exists),
            ("planning_approved", "Planning approved", _planning_approved),
            ("patch_proposal_approved", "Patch proposal approved", _patch_proposal_approved),
            ("workspace_apply_approved", "Workspace apply completed", _workspace_applied),
        ],
        "github_preflight_approved": [
            ("issue_intake", "Issue plan exists", _plan_exists),
            ("planning_approved", "Planning approved", _planning_approved),
            ("workspace_verification", "Workspace verification passed", _workspace_verification_passed),
        ],
        "software_delivery-stage": [
            ("issue_intake", "Issue plan exists", _plan_exists),
            ("planning_approved", "Planning approved", _planning_approved),
        ],
    }


def _missing_gate_prerequisites(
    *,
    session_id: str,
    plan_id: str | None,
    gate_id: str | None,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "prerequisite_note")]
    rows: list[dict[str, Any]] = list(stored)
    if not gate_id:
        rows.append(
            {
                "prerequisite_id": "target-gate-missing",
                "detail": "Cannot assess prerequisites without target frozen gate.",
                "read_only": True,
            }
        )
        return rows

    pid = plan_id or ""
    missing: list[dict[str, Any]] = []
    for prereq_id, label, checker in _prerequisite_checkers().get(gate_id, ()):
        if not checker(session_id=session_id, plan_id=pid):
            missing.append(
                {
                    "prerequisite_id": prereq_id,
                    "label": label,
                    "gate_id": gate_id,
                    "satisfied": False,
                    "detail": f"Missing prerequisite `{prereq_id}` for frozen gate `{gate_id}`.",
                    "read_only": True,
                }
            )

    if missing:
        rows.extend(missing)
    else:
        rows.append(
            {
                "prerequisite_id": "prerequisites-met",
                "gate_id": gate_id,
                "satisfied": True,
                "detail": f"All known prerequisites satisfied for `{gate_id}` intake preview.",
                "read_only": True,
            }
        )
    return rows[:16]


def _required_existing_commands(
    *,
    gate_id: str | None,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "intake_command_note")]
    rows: list[dict[str, Any]] = list(stored)
    if gate_id and gate_id in GATE_EXISTING_COMMAND_HINTS:
        for idx, (command_hint, command_detail) in enumerate(GATE_EXISTING_COMMAND_HINTS[gate_id]):
            rows.append(
                {
                    "command_id": f"existing-{gate_id}-{idx}",
                    "gate_id": gate_id,
                    "command_hint": command_hint,
                    "detail": command_detail,
                    "gate_execution_performed": False,
                    "executable": False,
                    "read_only": True,
                }
            )
    if not rows:
        rows.append(
            {
                "command_id": "pending-commands",
                "detail": "Required existing commands available after FIX 177 handoff targets a gate.",
                "read_only": True,
            }
        )
    return rows


def _forbidden_intake_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_INTAKE_ACTIONS
    ]


def _next_step_intake_sequence(*, intake_preview_ready: bool) -> list[dict[str, Any]]:
    if not intake_preview_ready:
        return [
            {
                "step": 1,
                "command_hint": "gate-routed lane entry handoff — complete FIX 177 handoff packet",
                "gate_execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "gate intake artifact: <summary> — persist intake preview record",
            "gate_execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "use frozen lane existing commands — gate executes only after prerequisites met",
            "gate_bypass": False,
            "read_only": True,
        },
    ]


def _intake_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    intake_preview_ready: bool,
    gate_identified: bool,
    shape_valid: bool,
) -> list[dict[str, Any]]:
    score = 15 + (25 if intake_preview_ready else 0) + (20 if gate_identified else 0)
    score += 20 if shape_valid else 0
    if _by_kind(records, "intake_preview_artifact"):
        score += 10
    score = min(100, score)
    label = "preview_ready" if score >= 75 else "partial" if score >= 45 else "blocked"
    return [
        {
            "score_id": "frozen-gate-intake-preview-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_178,
            "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
            "composes_upstream_layers": True,
            "detail": "Intake preview integrity — composes FIX 177 without gate execution.",
            "read_only": True,
        }
    ]


def build_frozen_gate_intake_preview(*, session_id: str) -> FrozenGateIntakePreviewResult:
    sid = (session_id or "default").strip()[:64] or "default"

    handoff_result = build_gate_routed_lane_entry_handoff(session_id=sid)
    handoff = handoff_result.gate_routed_lane_entry_handoff if handoff_result.ok else {}

    plan_id = str(handoff.get("plan_id") or "") or None
    correlation_id = str(handoff.get("correlation_id") or "") or None

    records = list_frozen_gate_intake_preview_records(session_id=sid, plan_id=plan_id)
    handoff_ready = bool(handoff.get("handoff_ready")) and handoff_result.ok

    gate_id = handoff.get("target_gate_id")
    gate_identified = bool(gate_id)

    shape_rows = _validate_packet_shape(handoff=handoff)
    shape_valid = bool(shape_rows and shape_rows[0].get("valid"))

    intake_preview_ready = handoff_ready and gate_identified and shape_valid

    sections = {
        "handoff_upstream_read": _handoff_upstream_read(handoff=handoff),
        "matching_frozen_gate_identification": _matching_frozen_gate_identification(
            handoff=handoff,
            records=records,
        ),
        "intake_preview_packet": _intake_preview_packet(
            handoff=handoff,
            gate_id=gate_id,
            shape_valid=shape_valid,
            intake_preview_ready=intake_preview_ready,
        ),
        "packet_shape_validation": shape_rows,
        "required_existing_commands": _required_existing_commands(gate_id=gate_id, records=records),
        "missing_gate_prerequisites": _missing_gate_prerequisites(
            session_id=sid,
            plan_id=plan_id,
            gate_id=gate_id,
            records=records,
        ),
        "lane_entry_confirmation": _lane_entry_confirmation(),
        "forbidden_intake_actions": _forbidden_intake_actions(),
        "next_step_intake_sequence": _next_step_intake_sequence(intake_preview_ready=intake_preview_ready),
        "intake_integrity_scoring": _intake_integrity_scoring(
            records=records,
            intake_preview_ready=intake_preview_ready,
            gate_identified=gate_identified,
            shape_valid=shape_valid,
        ),
    }

    frozen_gate_intake_preview: dict[str, Any] = {
        "schema_version": FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION,
        "fix": FROZEN_GATE_INTAKE_PREVIEW_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_178,
        "execution_performed": EXECUTION_PERFORMED_FIX_178,
        "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_178,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_178,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_178,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_178,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_178,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_178,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_178,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_178,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_178,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_178,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_178,
        "invariant": FROZEN_GATE_INTAKE_PREVIEW_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "intake_preview_record_count": len(records),
        "target_gate_id": gate_id,
        "intake_preview_tier": INTAKE_PREVIEW_TIER if intake_preview_ready else None,
        "intake_preview_ready": intake_preview_ready,
        "handoff_ready_upstream": handoff.get("handoff_ready"),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_177_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_177),
        },
        "fix_178_certification_requirements": list(FIX_178_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "frozen_gate_intake_preview_cognition": True,
        "gate_intake_preview_not_gate_execution": True,
        "frozen_gate_intake_preview_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in FROZEN_GATE_INTAKE_PREVIEW_PRINCIPLES
        ],
        "sources": {
            "composes_gate_routed_lane_entry_handoff": handoff_result.ok,
            "gate_routed_lane_entry_handoff_fix": "FIX 177",
            "intake_preview_records": len(records),
        },
    }
    return FrozenGateIntakePreviewResult(
        ok=True,
        session_id=sid,
        frozen_gate_intake_preview=frozen_gate_intake_preview,
        detail="Frozen gate intake preview assembled (composes FIX 177 — intake preview ≠ gate execution).",
    )
