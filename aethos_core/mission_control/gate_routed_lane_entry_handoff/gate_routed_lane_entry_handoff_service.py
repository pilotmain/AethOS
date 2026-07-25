# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — gate-routed lane entry handoff (composes FIX 176)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_177_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_177,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_177,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177,
    CODE_WRITE_ENABLED_FIX_177,
    EXECUTION_PERFORMED_FIX_177,
    FORBIDDEN_HANDOFF_ACTIONS,
    FROZEN_SOFTWARE_DELIVERY_GATES,
    GATE_BYPASS_ENABLED_FIX_177,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_FIX,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_INVARIANT,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_PRINCIPLES,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_177,
    HANDOFF_TIER,
    LANE_ADMISSION_EXECUTED_FIX_177,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
    MERGE_DEPLOY_ENABLED_FIX_177,
    MUTATION_PERFORMED_FIX_177,
    PR_ACTION_ENABLED_FIX_177,
    RAILWAY_MUTATION_ENABLED_FIX_177,
    TIER_ESCALATION_ENABLED_FIX_177,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_176,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    list_gate_routed_lane_entry_handoff_records,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
    build_human_lane_admission_decision,
)


@dataclass(frozen=True)
class GateRoutedLaneEntryHandoffResult:
    ok: bool
    session_id: str
    gate_routed_lane_entry_handoff: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _latest_decision(decision: dict[str, Any]) -> dict[str, Any]:
    rows = _sections(decision).get("selected_lane_admission_decision") or []
    for row in reversed(rows):
        if row.get("decision_value"):
            return row
    return rows[-1] if rows else {}


def _identify_gate_from_text(text: str) -> str | None:
    lower = (text or "").lower()
    for gate in FROZEN_SOFTWARE_DELIVERY_GATES:
        if gate.replace("_", " ") in lower or gate in lower:
            return gate
    if "verification" in lower:
        return "workspace_verification"
    if "implementation" in lower or "plan" in lower:
        return "implementation_plan"
    return None


def _human_decision_upstream_read(*, decision: dict[str, Any]) -> list[dict[str, Any]]:
    packet = (_sections(decision).get("lane_admission_decision_packet") or [{}])[0]
    latest = _latest_decision(decision)
    return [
        {
            "read_id": "fix-176-decision-read",
            "upstream_fix": "FIX 176",
            "human_decision_recorded": decision.get("human_decision_recorded"),
            "decision_value": latest.get("decision_value") or packet.get("decision_value"),
            "decision_ready": decision.get("decision_ready"),
            "read_only": True,
            "recomputed_by_fix_177": False,
        }
    ]


def _target_frozen_gate_identification(
    *,
    decision: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "target_gate_note")]
    latest = _latest_decision(decision)
    content = str(latest.get("decision_content") or "")
    gate_id = _identify_gate_from_text(content)
    rows: list[dict[str, Any]] = list(stored)
    if gate_id:
        rows.append(
            {
                "identification_id": f"target-{gate_id}",
                "gate_id": gate_id,
                "frozen_software_delivery_gate": gate_id in FROZEN_SOFTWARE_DELIVERY_GATES,
                "decision_value": latest.get("decision_value"),
                "gate_bypass": False,
                "lane_entry_execution_performed": False,
                "read_only": True,
            }
        )
    if not rows:
        rows.append(
            {
                "identification_id": "pending-gate",
                "detail": "Target frozen gate unidentified until human decision references a gate.",
                "read_only": True,
            }
        )
    return rows


def _decision_rationale_in_handoff(*, decision: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(decision).get("decision_rationale") or []:
        if row.get("content") or row.get("detail"):
            rows.append({**row, "upstream_fix": "FIX 176", "read_only": True})
    if not rows:
        rows.append(
            {
                "rationale_id": "no-rationale",
                "detail": "No decision rationale from upstream FIX 176.",
                "read_only": True,
            }
        )
    return rows


def _accepted_risks_in_handoff(*, decision: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(decision).get("accepted_risks_tradeoffs") or []:
        if row.get("content") or row.get("detail"):
            rows.append({**row, "upstream_fix": "FIX 176", "read_only": True})
    if not rows:
        rows.append(
            {
                "risk_id": "no-risks",
                "detail": "No accepted risks recorded in upstream FIX 176.",
                "read_only": True,
            }
        )
    return rows


def _remaining_blockers_in_handoff(*, decision: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(decision).get("acknowledged_remaining_blockers") or []:
        if row.get("acknowledgment_id") and row.get("acknowledgment_id") != "no-blockers":
            rows.append({**row, "upstream_fix": "FIX 176", "read_only": True})
    if not rows:
        rows.append(
            {
                "blocker_id": "no-blockers",
                "detail": "No remaining blockers acknowledged in upstream FIX 176.",
                "read_only": True,
            }
        )
    return rows[:12]


def _gate_validation_requirements(
    *,
    decision: dict[str, Any],
    gate_id: str | None,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "validation_requirement_note")]
    latest = _latest_decision(decision)
    decision_value = latest.get("decision_value")
    reqs: list[dict[str, Any]] = list(stored)
    if gate_id and decision_value == "admit":
        reqs.extend(
            [
                {
                    "requirement_id": f"validate-{gate_id}",
                    "gate_id": gate_id,
                    "detail": f"Frozen gate `{gate_id}` must validate prerequisites and approvals before lane entry.",
                    "gate_bypass": False,
                    "approval_bypass": False,
                    "read_only": True,
                },
                {
                    "requirement_id": "validate-human-decision",
                    "detail": "Gate must confirm human admit decision matches bounded authorization envelope.",
                    "read_only": True,
                },
            ]
        )
    elif decision_value == "hold":
        reqs.append(
            {
                "requirement_id": "hold-no-handoff",
                "detail": "Hold decision — gate handoff blocked until human re-engages with admit or reject.",
                "read_only": True,
            }
        )
    elif decision_value == "reject":
        reqs.append(
            {
                "requirement_id": "reject-no-handoff",
                "detail": "Reject decision — no lane handoff to frozen gates.",
                "read_only": True,
            }
        )
    if not reqs:
        reqs.append(
            {
                "requirement_id": "pending-validation",
                "detail": "Gate validation requirements pending human decision from FIX 176.",
                "read_only": True,
            }
        )
    return reqs


def _required_next_commands(
    *,
    decision: dict[str, Any],
    gate_id: str | None,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "handoff_command_note")]
    latest = _latest_decision(decision)
    decision_value = latest.get("decision_value")
    cmds: list[dict[str, Any]] = list(stored)
    if decision_value == "admit" and gate_id:
        cmds.append(
            {
                "command_id": f"next-{gate_id}",
                "command_hint": f"proceed to frozen gate `{gate_id}` — gate validates before lane entry",
                "lane_entry_execution_performed": False,
                "read_only": True,
            }
        )
    elif decision_value == "hold":
        cmds.append(
            {
                "command_id": "hold-reengage",
                "command_hint": "human re-engagement required — resolve hold before gate handoff",
                "read_only": True,
            }
        )
    if not cmds:
        cmds.append(
            {
                "command_id": "pending-commands",
                "detail": "Required next commands available after FIX 176 human decision.",
                "read_only": True,
            }
        )
    return cmds


def _gate_handoff_packet(
    *,
    decision: dict[str, Any],
    gate_id: str | None,
    handoff_ready: bool,
) -> list[dict[str, Any]]:
    latest = _latest_decision(decision)
    decision_value = latest.get("decision_value")
    return [
        {
            "packet_id": "gate-routed-lane-entry-handoff-packet",
            "decision_value": decision_value,
            "target_gate_id": gate_id,
            "handoff_ready": handoff_ready and decision_value == "admit" and bool(gate_id),
            "lane_entry_execution_performed": False,
            "lane_admission_executed": False,
            "gate_bypass": False,
            "approval_bypass": False,
            "detail": "Gate handoff packet — frozen gate decides lane entry after validation.",
            "read_only": True,
        }
    ]


def _forbidden_handoff_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_HANDOFF_ACTIONS
    ]


def _next_step_handoff_sequence(*, handoff_ready: bool) -> list[dict[str, Any]]:
    if not handoff_ready:
        return [
            {
                "step": 1,
                "command_hint": "human lane admission decision — record admit, hold, or reject (FIX 176)",
                "lane_entry_execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "gate handoff artifact: <summary> — persist handoff record",
            "lane_entry_execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "deliver handoff packet to frozen gate — gate validates and decides lane entry",
            "gate_bypass": False,
            "read_only": True,
        },
    ]


def _handoff_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    handoff_ready: bool,
    gate_identified: bool,
) -> list[dict[str, Any]]:
    score = 20 + (30 if handoff_ready else 0) + (20 if gate_identified else 0)
    if _by_kind(records, "gate_handoff_artifact"):
        score += 15
    score = min(100, score)
    label = "handoff_ready" if score >= 75 else "partial" if score >= 45 else "blocked"
    return [
        {
            "score_id": "gate-routed-lane-entry-handoff-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
            "composes_upstream_layers": True,
            "detail": "Handoff integrity — composes FIX 176 without lane entry execution.",
            "read_only": True,
        }
    ]


def build_gate_routed_lane_entry_handoff(*, session_id: str) -> GateRoutedLaneEntryHandoffResult:
    sid = (session_id or "default").strip()[:64] or "default"

    decision_result = build_human_lane_admission_decision(session_id=sid)
    decision = decision_result.human_lane_admission_decision if decision_result.ok else {}

    plan_id = str(decision.get("plan_id") or "") or None
    correlation_id = str(decision.get("correlation_id") or "") or None

    records = list_gate_routed_lane_entry_handoff_records(session_id=sid, plan_id=plan_id)
    handoff_ready = bool(decision.get("human_decision_recorded")) and decision_result.ok

    gate_rows = _target_frozen_gate_identification(decision=decision, records=records)
    gate_id = next((r.get("gate_id") for r in gate_rows if r.get("gate_id")), None)
    gate_identified = bool(gate_id)

    sections = {
        "human_decision_upstream_read": _human_decision_upstream_read(decision=decision),
        "target_frozen_gate_identification": gate_rows,
        "decision_rationale_in_handoff": _decision_rationale_in_handoff(decision=decision),
        "accepted_risks_in_handoff": _accepted_risks_in_handoff(decision=decision),
        "remaining_blockers_in_handoff": _remaining_blockers_in_handoff(decision=decision),
        "gate_validation_requirements": _gate_validation_requirements(
            decision=decision,
            gate_id=gate_id,
            records=records,
        ),
        "required_next_commands": _required_next_commands(
            decision=decision,
            gate_id=gate_id,
            records=records,
        ),
        "gate_handoff_packet": _gate_handoff_packet(
            decision=decision,
            gate_id=gate_id,
            handoff_ready=handoff_ready,
        ),
        "forbidden_handoff_actions": _forbidden_handoff_actions(),
        "next_step_handoff_sequence": _next_step_handoff_sequence(handoff_ready=handoff_ready),
        "handoff_integrity_scoring": _handoff_integrity_scoring(
            records=records,
            handoff_ready=handoff_ready,
            gate_identified=gate_identified,
        ),
    }

    gate_routed_lane_entry_handoff: dict[str, Any] = {
        "schema_version": GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION,
        "fix": GATE_ROUTED_LANE_ENTRY_HANDOFF_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_177,
        "execution_performed": EXECUTION_PERFORMED_FIX_177,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_177,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_177,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_177,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_177,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_177,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_177,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_177,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_177,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_177,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_177,
        "invariant": GATE_ROUTED_LANE_ENTRY_HANDOFF_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "gate_handoff_record_count": len(records),
        "target_gate_id": gate_id,
        "handoff_tier": HANDOFF_TIER if handoff_ready else None,
        "handoff_ready": handoff_ready and _latest_decision(decision).get("decision_value") == "admit",
        "human_decision_recorded_upstream": decision.get("human_decision_recorded"),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_176_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_176),
        },
        "fix_177_certification_requirements": list(FIX_177_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "gate_routed_lane_entry_handoff_cognition": True,
        "gate_routed_handoff_not_lane_entry_execution": True,
        "gate_routed_lane_entry_handoff_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GATE_ROUTED_LANE_ENTRY_HANDOFF_PRINCIPLES
        ],
        "sources": {
            "composes_human_lane_admission_decision": decision_result.ok,
            "human_lane_admission_decision_fix": "FIX 176",
            "gate_handoff_records": len(records),
        },
    }
    return GateRoutedLaneEntryHandoffResult(
        ok=True,
        session_id=sid,
        gate_routed_lane_entry_handoff=gate_routed_lane_entry_handoff,
        detail="Gate-routed lane entry handoff assembled (composes FIX 176 — handoff ≠ lane entry execution).",
    )
