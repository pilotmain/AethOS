# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command + human escalation (governance only)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_incident_command_contract import (
    ALLOWED_INCIDENT_DECISIONS,
    AUTOMATIC_INCIDENT_CLOSURE_PERMITTED,
    AUTONOMOUS_INCIDENT_MUTATION_PERMITTED,
    AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED,
    INCIDENT_COMMANDER_ACCEPTANCE_PHRASE,
    IncidentStatus,
)
from aethos_core.providers.railway.execution_contract.production_incident_command_store import (
    append_incident_decision,
    append_incident_event,
    load_incident,
    load_incident_for_execution,
    save_incident,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    load_railway_production_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    load_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
)

_OPEN_RX = re.compile(r"\bopen\s+railway\s+production\s+incident\b", re.I)
_SHOW_INCIDENT_RX = re.compile(r"\bshow\s+railway\s+production\s+incident\b", re.I)
_TIMELINE_RX = re.compile(r"\bshow\s+railway\s+production\s+incident\s+timeline\b", re.I)
_CLOSE_RX = re.compile(r"\bclose\s+railway\s+production\s+incident\b", re.I)
_ASSIGN_COMMANDER_RX = re.compile(r"\bassign\s+railway\s+incident\s+commander\b", re.I)
_ACK_COMMAND_RX = re.compile(r"\backnowledge\s+railway\s+incident\s+command\b", re.I)
_COMMANDER_STATUS_RX = re.compile(r"\bshow\s+railway\s+incident\s+commander\s+status\b", re.I)
_DECISION_RX = re.compile(r"\brecord\s+railway\s+incident\s+decision\s+(?P<decision>[a-z_]+)\b", re.I)
_SHOW_DECISIONS_RX = re.compile(r"\bshow\s+railway\s+incident\s+decisions\b", re.I)
_ROLLBACK_REC_RX = re.compile(r"\bshow\s+railway\s+incident\s+rollback\s+recommendation\b", re.I)
_BRIEFING_RX = re.compile(r"\bshow\s+railway\s+incident\s+briefing\b", re.I)
_CHECKLIST_RX = re.compile(r"\bshow\s+railway\s+incident\s+operator\s+checklist\b", re.I)
_CUSTOMER_DRAFT_RX = re.compile(r"\bshow\s+railway\s+incident\s+customer\s+update\s+draft\b", re.I)


@dataclass(frozen=True)
class IncidentContextBundle:
    verification_passed: bool | None
    verification_status: str
    rollback_recommendation: str
    escalation_ticket_id: str
    rollout_stage: str
    incident_mode_active: bool
    canary_shadow_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_passed": self.verification_passed,
            "verification_status": self.verification_status,
            "rollback_recommendation": self.rollback_recommendation,
            "escalation_ticket_id": self.escalation_ticket_id,
            "rollout_stage": self.rollout_stage,
            "incident_mode_active": self.incident_mode_active,
            "canary_shadow_summary": self.canary_shadow_summary,
        }


@dataclass(frozen=True)
class IncidentCommandResult:
    ok: bool
    incident: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_production_incident_command_intent(text: str) -> bool:
    raw = (text or "").strip()
    patterns = (
        _OPEN_RX,
        _SHOW_INCIDENT_RX,
        _TIMELINE_RX,
        _CLOSE_RX,
        _ASSIGN_COMMANDER_RX,
        _ACK_COMMAND_RX,
        _COMMANDER_STATUS_RX,
        _DECISION_RX,
        _SHOW_DECISIONS_RX,
        _ROLLBACK_REC_RX,
        _BRIEFING_RX,
        _CHECKLIST_RX,
        _CUSTOMER_DRAFT_RX,
    )
    return any(rx.search(raw) for rx in patterns)


def extract_incident_commander_phrase(text: str) -> bool:
    return INCIDENT_COMMANDER_ACCEPTANCE_PHRASE in (text or "")


def parse_incident_decision(text: str) -> str:
    match = _DECISION_RX.search((text or "").strip())
    return str(match.group("decision") or "").strip().lower() if match else ""


def load_incident_command_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "railway_production_incident_command_enabled", True)),
        "default_severity": str(getattr(settings, "railway_production_incident_default_severity", "sev2")),
    }


def is_open_production_incident_active(*, execution_id: str) -> bool:
    incident = load_incident_for_execution(execution_id=execution_id)
    if not incident:
        return False
    return str(incident.get("status") or "") not in {"closed", "resolved"}


def _target_from_plan(plan: dict[str, Any] | None) -> dict[str, str]:
    plan = plan or {}
    return {
        "project": str(plan.get("project") or plan.get("railway_project") or "unknown"),
        "environment": str(plan.get("environment") or "production"),
        "service": str(plan.get("service") or plan.get("service_name") or "aethos-api"),
    }


def build_incident_context_bundle(*, execution_id: str, plan: dict[str, Any] | None = None) -> IncidentContextBundle:
    verification = load_verification_receipt(execution_id=execution_id) or {}
    assessment = verification.get("assessment") or {}
    verification_passed = assessment.get("verification_passed")
    verification_status = str(verification.get("status") or "unknown")

    rollback_rec = str(assessment.get("rollback_recommendation") or "none")
    escalation_id = ""

    from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
        load_escalation,
    )

    esc = load_escalation(execution_id=execution_id)
    if esc:
        escalation_id = str(esc.get("escalation_id") or "")
        if rollback_rec == "none":
            rollback_rec = str(esc.get("rollback_recommendation") or "none")

    rollout = load_rollout_journal(execution_id=execution_id) or {}
    rollout_stage = str(rollout.get("current_stage") or "not_enrolled")

    policy_cfg = load_railway_production_policy_config()
    canary_summary = "governed synthetic-only"

    return IncidentContextBundle(
        verification_passed=verification_passed if verification else None,
        verification_status=verification_status,
        rollback_recommendation=rollback_rec,
        escalation_ticket_id=escalation_id,
        rollout_stage=rollout_stage,
        incident_mode_active=policy_cfg.incident_mode,
        canary_shadow_summary=canary_summary,
    )


def attach_context_to_incident(incident: dict[str, Any], *, plan: dict[str, Any] | None = None) -> dict[str, Any]:
    execution_id = str(incident.get("execution_id") or "")
    bundle = build_incident_context_bundle(execution_id=execution_id, plan=plan)
    incident["attached_context"] = bundle.to_dict()
    incident["rollback_recommendation"] = bundle.rollback_recommendation
    return save_incident(incident)


def open_production_incident(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
    severity: str = "",
) -> IncidentCommandResult:
    cfg = load_incident_command_config()
    if not cfg["enabled"]:
        return IncidentCommandResult(
            ok=False,
            incident={},
            blockers=["incident_command_disabled"],
            detail="Production incident command is disabled.",
        )

    existing = load_incident_for_execution(execution_id=execution_id)
    if existing and str(existing.get("status") or "") not in {"closed"}:
        return IncidentCommandResult(
            ok=True,
            incident=existing,
            detail="Open incident already exists for this execution.",
        )

    import uuid

    from datetime import UTC, datetime

    bundle = build_incident_context_bundle(execution_id=execution_id, plan=plan)
    status: IncidentStatus = "triage" if bundle.verification_passed is False else "open"
    if bundle.rollback_recommendation not in ("none", ""):
        status = "rollback_recommended"

    incident = {
        "incident_id": f"rpic-{uuid.uuid4().hex[:12]}",
        "execution_id": execution_id,
        "target": _target_from_plan(plan),
        "status": status,
        "severity": severity or cfg["default_severity"],
        "commander": None,
        "created_at": datetime.now(UTC).isoformat(),
        "events": [],
        "decisions": [],
        "rollback_recommendation": bundle.rollback_recommendation,
        "attached_context": bundle.to_dict(),
        "mutation_performed": False,
    }
    incident = save_incident(incident)
    incident = append_incident_event(
        incident,
        action="incident_opened",
        actor="operator",
        detail=f"status={status}",
        session_id=session_id,
    )
    return IncidentCommandResult(ok=True, incident=incident, detail="Production incident opened.")


def assign_incident_commander(
    *,
    execution_id: str,
    user_text: str,
    session_id: str = "",
) -> IncidentCommandResult:
    incident = load_incident_for_execution(execution_id=execution_id)
    if not incident:
        return IncidentCommandResult(ok=False, incident={}, detail="No open incident for execution.")

    if not extract_incident_commander_phrase(user_text):
        incident = append_incident_event(
            incident,
            action="commander_assignment_rejected",
            detail="Exact incident commander phrase required.",
            session_id=session_id,
        )
        return IncidentCommandResult(
            ok=False,
            incident=incident,
            blockers=["incident_commander_phrase_required"],
            detail=f"Phrase required: {INCIDENT_COMMANDER_ACCEPTANCE_PHRASE}",
        )

    incident["commander"] = "incident_commander"
    incident["status"] = "incident_commander_assigned"
    incident = save_incident(incident)
    incident = append_incident_event(
        incident,
        action="incident_commander_assigned",
        session_id=session_id,
    )
    return IncidentCommandResult(ok=True, incident=incident, detail="Incident commander assigned.")


def acknowledge_incident_command(
    *,
    execution_id: str,
    user_text: str,
    session_id: str = "",
) -> IncidentCommandResult:
    return assign_incident_commander(
        execution_id=execution_id,
        user_text=user_text,
        session_id=session_id,
    )


def record_incident_decision(
    *,
    execution_id: str,
    decision: str,
    user_text: str = "",
    session_id: str = "",
) -> IncidentCommandResult:
    incident = load_incident_for_execution(execution_id=execution_id)
    if not incident:
        return IncidentCommandResult(ok=False, incident={}, detail="No open incident.")

    if decision not in ALLOWED_INCIDENT_DECISIONS:
        incident = append_incident_event(
            incident,
            action="decision_rejected",
            detail=f"Unsupported decision: {decision}",
            session_id=session_id,
        )
        return IncidentCommandResult(
            ok=False,
            incident=incident,
            blockers=["unsupported_incident_decision"],
        )

    incident = append_incident_decision(
        incident,
        decision=decision,
        detail=(user_text or "")[:500],
        session_id=session_id,
    )
    incident = append_incident_event(
        incident,
        action="incident_decision_recorded",
        detail=decision,
        session_id=session_id,
    )

    if decision == "begin_triage":
        incident["status"] = "triage"
    elif decision == "mitigation_plan_recorded":
        incident["status"] = "mitigation_planning"
    elif decision == "authorize_rollback_rehearsal":
        incident["status"] = "rollback_rehearsal_authorized"
    elif decision == "manual_action_required":
        incident["status"] = "manual_action_required"
    elif decision == "mark_resolved":
        incident["status"] = "resolved"
    elif decision == "escalate_to_manual_review":
        incident["status"] = "manual_action_required"

    incident = save_incident(incident)
    return IncidentCommandResult(ok=True, incident=incident, detail=f"Decision recorded: {decision}")


def close_production_incident(
    *,
    execution_id: str,
    session_id: str = "",
) -> IncidentCommandResult:
    incident = load_incident_for_execution(execution_id=execution_id)
    if not incident:
        return IncidentCommandResult(ok=False, incident={}, detail="No open incident to close.")

    if AUTOMATIC_INCIDENT_CLOSURE_PERMITTED:
        return IncidentCommandResult(
            ok=False,
            incident=incident,
            blockers=["automatic_closure_prohibited"],
        )

    incident["status"] = "closed"
    incident = save_incident(incident)
    incident = append_incident_event(
        incident,
        action="incident_closed",
        actor="operator",
        session_id=session_id,
    )
    return IncidentCommandResult(ok=True, incident=incident, detail="Incident closed (manual only).")


def sync_incident_from_verification_failure(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> dict[str, Any] | None:
    """Attach verification failure context to open incident or create triage incident."""
    if not load_incident_command_config()["enabled"]:
        return None
    incident = load_incident_for_execution(execution_id=execution_id)
    if not incident:
        result = open_production_incident(
            execution_id=execution_id,
            plan=plan,
            session_id=session_id,
        )
        return result.incident if result.ok else None
    incident = attach_context_to_incident(incident, plan=plan)
    if str(incident.get("rollback_recommendation") or "none") not in ("none", ""):
        incident["status"] = "rollback_recommended"
    else:
        incident["status"] = "triage"
    incident = save_incident(incident)
    return append_incident_event(
        incident,
        action="verification_failure_attached",
        actor="system",
        detail="FIX 119 verification evidence linked.",
        session_id=session_id,
    )


def incident_blocks_rollout_advance(*, execution_id: str) -> tuple[bool, str]:
    policy_cfg = load_railway_production_policy_config()
    if policy_cfg.incident_mode:
        return True, "production_incident_mode_active"
    incident = load_incident_for_execution(execution_id=execution_id)
    if incident and str(incident.get("status") or "") not in {"closed", "resolved"}:
        return True, f"open_production_incident:{incident.get('incident_id')}"
    return False, ""
