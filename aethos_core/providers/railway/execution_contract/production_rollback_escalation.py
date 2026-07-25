# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — production rollback escalation framework (manual escalation only)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
    load_railway_production_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_contract import (
    INCIDENT_COMMANDER_ACK_PHRASE,
    PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE,
    RollbackDecisionState,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
    append_audit_event,
    load_escalation,
    record_rollback_rehearsal_confirmation,
    rollback_rehearsal_quorum_count,
    save_escalation,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
)

_ACK_RX = re.compile(
    r"\backnowledge\s+production\s+rollback\s+escalation\b",
    re.I,
)
_DECISION_RX = re.compile(
    r"\brecord\s+production\s+rollback\s+decision\s+(?P<state>[a-z_]+)\b",
    re.I,
)
_ESCALATION_RX = re.compile(r"\bshow\s+railway\s+production\s+rollback\s+escalation\b", re.I)
_AUDIT_RX = re.compile(r"\bshow\s+railway\s+production\s+rollback\s+audit\s+trail\b", re.I)
_QUORUM_RX = re.compile(
    r"\bshow\s+railway\s+production\s+rollback\s+rehearsal\s+quorum\b",
    re.I,
)


@dataclass(frozen=True)
class RollbackEscalationGateResult:
    ready_for_shadow_rehearsal: bool
    escalation_present: bool
    decision_state: str
    incident_commander_acknowledged: bool
    rollback_rehearsal_quorum_satisfied: bool
    autonomous_rollback_permitted: bool
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


def is_production_rollback_escalation_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _ESCALATION_RX.search(raw)
        or _AUDIT_RX.search(raw)
        or _ACK_RX.search(raw)
        or _DECISION_RX.search(raw)
        or _QUORUM_RX.search(raw)
    )


def extract_incident_commander_ack(text: str) -> bool:
    return INCIDENT_COMMANDER_ACK_PHRASE in (text or "")


def extract_rollback_rehearsal_quorum(text: str) -> bool:
    return PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE in (text or "")


def load_rollback_escalation_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "railway_production_rollback_escalation_enabled", True)),
        "rehearsal_quorum_required": int(
            getattr(settings, "railway_production_rollback_rehearsal_quorum", 2) or 2
        ),
        "require_incident_commander_ack": bool(
            getattr(settings, "railway_production_rollback_require_incident_commander_ack", True)
        ),
    }


def create_or_refresh_escalation_from_verification(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """Create escalation ticket from latest verification receipt + evidence bundle."""
    existing = load_escalation(execution_id=execution_id)
    if existing:
        return existing

    receipt = load_verification_receipt(execution_id=execution_id)
    assessment = (receipt or {}).get("assessment") or {}
    policy = assess_railway_production_policy(plan=plan or {}, execution_id=execution_id)

    recommendation = str(assessment.get("rollback_recommendation") or "blocked_pending_evidence")
    if assessment.get("verification_passed"):
        recommendation = "none"

    state: RollbackDecisionState = "recommendation_recorded"
    if recommendation not in ("none", "blocked_pending_evidence"):
        state = "pending_incident_commander_review"

    record = {
        "execution_id": execution_id,
        "decision_state": state,
        "rollback_recommendation": recommendation,
        "incident_escalation": str(assessment.get("incident_escalation") or "none"),
        "verification_passed": bool(assessment.get("verification_passed")),
        "evidence_bundle": (receipt or {}).get("evidence") or {},
        "verification_receipt_id": (receipt or {}).get("receipt_id") or "",
        "rollback_rehearsal_confirmations": [],
        "audit_trail": [],
        "human_decision_notes": "",
    }
    record = save_escalation(record)
    return append_audit_event(
        record,
        action="escalation_created",
        actor="system",
        state=state,
        detail=f"rollback_recommendation={recommendation}",
        session_id=session_id,
    )


def acknowledge_incident_commander(
    *,
    execution_id: str,
    user_text: str,
    session_id: str = "",
) -> dict[str, Any]:
    record = load_escalation(execution_id=execution_id) or create_or_refresh_escalation_from_verification(
        execution_id=execution_id,
        session_id=session_id,
    )
    if not extract_incident_commander_ack(user_text):
        return append_audit_event(
            record,
            action="incident_commander_ack_rejected",
            actor="operator",
            detail="Exact incident commander phrase required.",
            session_id=session_id,
        )

    current = str(record.get("decision_state") or "")
    if current not in {
        "shadow_rehearsal_authorized",
        "shadow_rehearsal_completed",
        "human_declined_rollback",
        "escalation_closed",
    }:
        record["decision_state"] = "incident_commander_acknowledged"
    record = save_escalation(record)
    record = record_rollback_rehearsal_confirmation(
        record,
        phrase_kind="incident_commander_ack",
        session_id=session_id,
    )
    return append_audit_event(
        record,
        action="incident_commander_acknowledged",
        actor="incident_commander",
        state="incident_commander_acknowledged",
        session_id=session_id,
    )


def record_human_rollback_decision(
    *,
    execution_id: str,
    decision_state: str,
    user_text: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    record = load_escalation(execution_id=execution_id) or create_or_refresh_escalation_from_verification(
        execution_id=execution_id,
        session_id=session_id,
    )
    allowed = {
        "human_declined_rollback",
        "escalation_closed",
        "shadow_rehearsal_authorized",
    }
    if decision_state not in allowed:
        return append_audit_event(
            record,
            action="decision_rejected",
            actor="operator",
            detail=f"Unsupported decision state: {decision_state}",
            session_id=session_id,
        )

    record["decision_state"] = decision_state
    if user_text.strip():
        record["human_decision_notes"] = user_text.strip()[:2000]
    record = save_escalation(record)
    return append_audit_event(
        record,
        action="human_decision_recorded",
        actor="operator",
        state=decision_state,
        session_id=session_id,
    )


def record_rollback_rehearsal_quorum_from_text(
    *,
    execution_id: str,
    user_text: str,
    session_id: str = "",
) -> dict[str, Any]:
    record = load_escalation(execution_id=execution_id) or create_or_refresh_escalation_from_verification(
        execution_id=execution_id,
        session_id=session_id,
    )
    if extract_rollback_rehearsal_quorum(user_text):
        record = record_rollback_rehearsal_confirmation(
            record,
            phrase_kind="rollback_rehearsal_quorum",
            session_id=session_id,
        )
        record = append_audit_event(
            record,
            action="rollback_rehearsal_quorum_recorded",
            actor="operator",
            session_id=session_id,
        )

    cfg = load_rollback_escalation_config()
    required = max(1, int(cfg["rehearsal_quorum_required"]))
    if rollback_rehearsal_quorum_count(record) >= required:
        current = str(record.get("decision_state") or "")
        if current == "incident_commander_acknowledged":
            record["decision_state"] = "rollback_rehearsal_quorum_recorded"
        elif current in {"recommendation_recorded", "pending_incident_commander_review"}:
            record["decision_state"] = "rollback_rehearsal_quorum_recorded"
        record = save_escalation(record)
        record = append_audit_event(
            record,
            action="rollback_rehearsal_quorum_satisfied",
            actor="system",
            state=str(record.get("decision_state") or ""),
            session_id=session_id,
        )
    return record


def assess_rollback_escalation_gate(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
    user_text: str = "",
    session_id: str = "",
) -> RollbackEscalationGateResult:
    _ = plan
    cfg = load_rollback_escalation_config()
    blockers: list[str] = []
    messages: list[str] = []

    if not cfg["enabled"]:
        blockers.append("rollback_escalation_disabled")
        messages.append("Production rollback escalation framework is disabled.")

    record = load_escalation(execution_id=execution_id)
    if not record:
        blockers.append("escalation_ticket_missing")
        messages.append("Open escalation with verification evidence first.")
        return RollbackEscalationGateResult(
            ready_for_shadow_rehearsal=False,
            escalation_present=False,
            decision_state="",
            incident_commander_acknowledged=False,
            rollback_rehearsal_quorum_satisfied=False,
            autonomous_rollback_permitted=False,
            blockers=blockers,
            messages=messages,
        )

    if user_text:
        record = record_rollback_rehearsal_quorum_from_text(
            execution_id=execution_id,
            user_text=user_text,
            session_id=session_id,
        )

    state = str(record.get("decision_state") or "")
    ic_ack = state in {
        "incident_commander_acknowledged",
        "rollback_rehearsal_quorum_recorded",
        "shadow_rehearsal_authorized",
        "shadow_rehearsal_completed",
    } or "incident_commander_ack" in {
        str(c.get("kind") or "") for c in (record.get("rollback_rehearsal_confirmations") or [])
    }

    required = max(1, int(cfg["rehearsal_quorum_required"]))
    quorum_ok = rollback_rehearsal_quorum_count(record) >= required

    authorized_rehearsal = state in {"shadow_rehearsal_authorized", "shadow_rehearsal_completed"}

    policy_cfg = load_railway_production_policy_config()
    if (
        policy_cfg.incident_mode
        and not extract_incident_commander_ack(user_text)
        and not ic_ack
        and not authorized_rehearsal
    ):
        blockers.append("production_incident_mode_active")

    if not authorized_rehearsal:
        if cfg["require_incident_commander_ack"] and not ic_ack:
            blockers.append("incident_commander_ack_required")
            messages.append(f"Incident commander phrase: {INCIDENT_COMMANDER_ACK_PHRASE}")

        if not quorum_ok:
            blockers.append("rollback_rehearsal_quorum_unsatisfied")
            messages.append(
                f"Rollback rehearsal quorum requires {required} confirmations including: "
                f"{PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE}"
            )

        if str(record.get("rollback_recommendation") or "none") == "none":
            blockers.append("no_rollback_recommendation")

    blockers.append("autonomous_production_rollback_prohibited")
    messages.append("Live production rollback is never permitted — shadow rehearsal only.")

    ready = not any(
        b
        for b in blockers
        if b not in {"autonomous_production_rollback_prohibited"}
    )

    return RollbackEscalationGateResult(
        ready_for_shadow_rehearsal=ready,
        escalation_present=True,
        decision_state=state,
        incident_commander_acknowledged=ic_ack,
        rollback_rehearsal_quorum_satisfied=quorum_ok,
        autonomous_rollback_permitted=False,
        blockers=blockers,
        messages=messages,
    )


def mark_shadow_rehearsal_completed(*, execution_id: str, session_id: str = "") -> dict[str, Any]:
    record = load_escalation(execution_id=execution_id)
    if not record:
        return {}
    record["decision_state"] = "shadow_rehearsal_completed"
    record = save_escalation(record)
    return append_audit_event(
        record,
        action="shadow_rehearsal_completed",
        actor="system",
        state="shadow_rehearsal_completed",
        detail="Production shadow rollback rehearsal finished; no live mutation.",
        session_id=session_id,
    )


def parse_decision_state_from_text(text: str) -> str:
    match = _DECISION_RX.search((text or "").strip())
    return str(match.group("state") or "").strip().lower() if match else ""
