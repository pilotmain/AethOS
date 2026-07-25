# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow rehearsal router (separate from execution_contract)."""

from __future__ import annotations

import re

from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    record_production_confirmations_from_text,
)
from aethos_core.providers.railway.execution_contract.production_shadow_certification import (
    build_production_shadow_certification_report,
)
from aethos_core.providers.railway.execution_contract.production_shadow_executor import (
    run_production_shadow_forward,
    run_production_shadow_rollback,
)
from aethos_core.providers.railway.execution_contract.production_shadow_gate import (
    assess_production_shadow_gate,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_renderer import (
    render_production_freeze_status,
    render_production_incident_mode_status,
    render_production_quorum_status,
    render_production_shadow_certification,
    render_production_shadow_orchestration_result,
    render_production_shadow_status,
)

_SIMULATE_PROD_DEPLOY_RX = re.compile(
    r"\bsimulate\s+production\s+railway\s+deployment\b",
    re.I,
)
_SIMULATE_PROD_ROLLBACK_RX = re.compile(
    r"\bsimulate\s+production\s+railway\s+rollback\b",
    re.I,
)
_SHADOW_STATUS_RX = re.compile(r"\bshow\s+railway\s+production\s+shadow\s+status\b", re.I)
_SHADOW_CERT_RX = re.compile(r"\bshow\s+railway\s+production\s+certification\b", re.I)
_QUORUM_STATUS_RX = re.compile(r"\bshow\s+railway\s+production\s+quorum\s+status\b", re.I)
_FREEZE_STATUS_RX = re.compile(r"\bshow\s+railway\s+production\s+freeze\s+status\b", re.I)
_INCIDENT_STATUS_RX = re.compile(r"\bshow\s+railway\s+production\s+incident\s+mode\b", re.I)


def is_railway_production_shadow_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _SIMULATE_PROD_DEPLOY_RX.search(raw)
        or _SIMULATE_PROD_ROLLBACK_RX.search(raw)
        or _SHADOW_STATUS_RX.search(raw)
        or _SHADOW_CERT_RX.search(raw)
        or _QUORUM_STATUS_RX.search(raw)
        or _FREEZE_STATUS_RX.search(raw)
        or _INCIDENT_STATUS_RX.search(raw)
    )


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": "railway_production_shadow",
        "matched_module": "providers.railway.execution_contract.production_shadow_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "production_shadow_stage": stage,
        **extra,
    }


def route_railway_production_shadow(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_railway_production_shadow_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=True,
    )
    plan = lane.plan or {}
    execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""
    shadow_journal = load_shadow_journal(execution_id=execution_id) if execution_id else None

    if execution_id and raw:
        record_production_confirmations_from_text(
            execution_id=execution_id,
            user_text=raw,
            session_id=session_id,
        )

    if _INCIDENT_STATUS_RX.search(raw):
        body = render_production_incident_mode_status()
        return body, "railway_production_incident_mode", _meta(session_id, stage="incident_mode")

    if _FREEZE_STATUS_RX.search(raw):
        body = render_production_freeze_status()
        return body, "railway_production_freeze_status", _meta(session_id, stage="freeze_status")

    if _QUORUM_STATUS_RX.search(raw):
        body = render_production_quorum_status(execution_id=execution_id)
        return body, "railway_production_quorum_status", _meta(
            session_id,
            stage="quorum_status",
            execution_id=execution_id,
        )

    if _SHADOW_CERT_RX.search(raw):
        report = build_production_shadow_certification_report(
            plan=plan,
            execution_id=execution_id,
            user_text=raw,
        )
        body = render_production_shadow_certification(report)
        return body, "railway_production_shadow_certification", _meta(
            session_id,
            stage="certification",
            certification_ok=str(report.ok).lower(),
        )

    if _SHADOW_STATUS_RX.search(raw):
        gate = assess_production_shadow_gate(
            plan=plan,
            user_text=raw,
            execution_id=execution_id,
            journal=shadow_journal,
            require_quorum=False,
        )
        body = render_production_shadow_status(gate=gate, execution_id=execution_id)
        return body, "railway_production_shadow_status", _meta(
            session_id,
            stage="shadow_status",
            gate_ready=str(gate.ready).lower(),
        )

    if _SIMULATE_PROD_DEPLOY_RX.search(raw):
        if not execution_id:
            body = "No execution_id for production plan. Complete plan enrollment first."
            return body, "railway_production_shadow_blocked", _meta(session_id, stage="blocked")
        result = run_production_shadow_forward(
            execution_id=execution_id,
            plan=plan,
            session_id=session_id,
            user_text=raw,
        )
        body = render_production_shadow_orchestration_result(result)
        intent = (
            "railway_production_shadow_forward"
            if result.shadow_completed
            else "railway_production_shadow_blocked"
        )
        return body, intent, _meta(
            session_id,
            stage="shadow_forward",
            execution_id=execution_id,
            policy_blocked=str(result.policy_blocked).lower(),
        )

    if _SIMULATE_PROD_ROLLBACK_RX.search(raw):
        if not execution_id:
            body = "No execution_id for production plan. Complete plan enrollment first."
            return body, "railway_production_shadow_blocked", _meta(session_id, stage="blocked")
        result = run_production_shadow_rollback(
            execution_id=execution_id,
            plan=plan,
            session_id=session_id,
            user_text=raw,
        )
        body = render_production_shadow_orchestration_result(result)
        intent = (
            "railway_production_shadow_rollback"
            if result.shadow_completed
            else "railway_production_shadow_blocked"
        )
        return body, intent, _meta(
            session_id,
            stage="shadow_rollback",
            execution_id=execution_id,
            policy_blocked=str(result.policy_blocked).lower(),
        )

    return None
