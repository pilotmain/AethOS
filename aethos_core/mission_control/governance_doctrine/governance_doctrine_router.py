# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — chat router for governance doctrine + policy charter."""

from __future__ import annotations

from aethos_core.mission_control.governance_doctrine.governance_doctrine_contract import (
    AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151,
    GOVERNANCE_DOCTRINE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_151,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_intent import (
    is_governance_doctrine_intent,
    parse_doctrine_record_intent,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_renderer import render_governance_doctrine
from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import append_governance_doctrine_record
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
    build_governance_role_architecture,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_DOCTRINE_ROUTE_ID,
        "matched_module": "mission_control.governance_doctrine.governance_doctrine_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_151 is False else "true",
        "autonomous_doctrine_evolution_enabled": "false"
        if AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151 is False
        else "true",
        "mutation_scope": "governance_doctrine_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "doctrine_not_execution",
        **extra,
    }


def route_governance_doctrine(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_doctrine_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        architecture = build_governance_role_architecture(session_id=session_id)
        arch = architecture.architecture if architecture.ok else {}
        record, blockers = append_governance_doctrine_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(arch.get("plan_id") or "") or None,
            correlation_id=str(arch.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Doctrine record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_doctrine_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Doctrine record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Amendment proposals only — no autonomous policy mutation."
        )
        return (
            body,
            "mission_control_governance_doctrine_record",
            _meta(
                session_id,
                stage="doctrine_record",
                record_id=str(record.get("record_id") or ""),
                doctrine_memory_only="true",
            ),
        )

    if not is_governance_doctrine_intent(text):
        return None

    result = build_governance_doctrine(session_id=session_id)
    if not result.ok:
        body = f"Governance doctrine unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_doctrine_blocked", _meta(session_id, stage="blocked")

    body = render_governance_doctrine(result.doctrine)
    return (
        body,
        "mission_control_governance_doctrine",
        _meta(
            session_id,
            stage="governance_doctrine",
            amendment_proposal_count=str(result.doctrine.get("amendment_proposal_count", 0)),
        ),
    )
