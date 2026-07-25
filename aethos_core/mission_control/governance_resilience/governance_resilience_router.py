# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — chat router for governance resilience + stress simulation."""

from __future__ import annotations

from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence
from aethos_core.mission_control.governance_resilience.governance_resilience_contract import (
    AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154,
    GOVERNANCE_RESILIENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_154,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_intent import (
    is_governance_resilience_intent,
    parse_resilience_record_intent,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_renderer import (
    render_governance_resilience,
)
from aethos_core.mission_control.governance_resilience.governance_resilience_service import build_governance_resilience
from aethos_core.mission_control.governance_resilience.governance_resilience_store import append_governance_resilience_record


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_RESILIENCE_ROUTE_ID,
        "matched_module": "mission_control.governance_resilience.governance_resilience_router",
        "session_id": session_id,
        "readonly": "true",
        "simulation_only": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_154 is False else "true",
        "autonomous_resilience_correction_enabled": "false"
        if AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154 is False
        else "true",
        "mutation_scope": "governance_resilience_simulation_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "resilience_simulation_not_adaptation",
        **extra,
    }


def route_governance_resilience(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_resilience_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        coherence = build_governance_coherence(session_id=session_id)
        coh = coherence.coherence if coherence.ok else {}
        record, blockers = append_governance_resilience_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(coh.get("plan_id") or "") or None,
            correlation_id=str(coh.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Resilience record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_resilience_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Resilience record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Simulation-only — no autonomous adaptation or resilience correction."
        )
        return (
            body,
            "mission_control_governance_resilience_record",
            _meta(
                session_id,
                stage="resilience_record",
                record_id=str(record.get("record_id") or ""),
                resilience_memory_only="true",
            ),
        )

    if not is_governance_resilience_intent(text):
        return None

    result = build_governance_resilience(session_id=session_id)
    if not result.ok:
        body = f"Governance resilience unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_resilience_blocked", _meta(session_id, stage="blocked")

    body = render_governance_resilience(result.resilience)
    return (
        body,
        "mission_control_governance_resilience",
        _meta(
            session_id,
            stage="governance_resilience",
            resilience_record_count=str(result.resilience.get("resilience_record_count", 0)),
        ),
    )
