# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — chat router for governance evolution + institutional continuity."""

from __future__ import annotations

from aethos_core.mission_control.governance_evolution.governance_evolution_contract import (
    AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155,
    GOVERNANCE_EVOLUTION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_155,
)
from aethos_core.mission_control.governance_evolution.governance_evolution_intent import (
    is_governance_evolution_intent,
    parse_evolution_record_intent,
)
from aethos_core.mission_control.governance_evolution.governance_evolution_renderer import render_governance_evolution
from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution
from aethos_core.mission_control.governance_evolution.governance_evolution_store import append_governance_evolution_record
from aethos_core.mission_control.governance_resilience.governance_resilience_service import build_governance_resilience


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_EVOLUTION_ROUTE_ID,
        "matched_module": "mission_control.governance_evolution.governance_evolution_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_155 is False else "true",
        "autonomous_governance_evolution_enabled": "false"
        if AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155 is False
        else "true",
        "mutation_scope": "governance_evolution_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "evolution_not_mutation",
        **extra,
    }


def route_governance_evolution(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_evolution_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        resilience = build_governance_resilience(session_id=session_id)
        res = resilience.resilience if resilience.ok else {}
        record, blockers = append_governance_evolution_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(res.get("plan_id") or "") or None,
            correlation_id=str(res.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Evolution record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_evolution_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Evolution record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous evolution or doctrine migration."
        )
        return (
            body,
            "mission_control_governance_evolution_record",
            _meta(
                session_id,
                stage="evolution_record",
                record_id=str(record.get("record_id") or ""),
                evolution_memory_only="true",
            ),
        )

    if not is_governance_evolution_intent(text):
        return None

    result = build_governance_evolution(session_id=session_id)
    if not result.ok:
        body = f"Governance evolution unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_evolution_blocked", _meta(session_id, stage="blocked")

    body = render_governance_evolution(result.evolution)
    return (
        body,
        "mission_control_governance_evolution",
        _meta(
            session_id,
            stage="governance_evolution",
            evolution_record_count=str(result.evolution.get("evolution_record_count", 0)),
        ),
    )
