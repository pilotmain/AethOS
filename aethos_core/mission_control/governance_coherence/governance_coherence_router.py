# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — chat router for governance coherence + constitutional integrity."""

from __future__ import annotations

from aethos_core.mission_control.governance_coherence.governance_coherence_contract import (
    AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153,
    GOVERNANCE_COHERENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_153,
)
from aethos_core.mission_control.governance_coherence.governance_coherence_intent import (
    is_governance_coherence_intent,
    parse_coherence_record_intent,
)
from aethos_core.mission_control.governance_coherence.governance_coherence_renderer import render_governance_coherence
from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence
from aethos_core.mission_control.governance_coherence.governance_coherence_store import append_governance_coherence_record
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
    build_governance_policy_interpretation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_COHERENCE_ROUTE_ID,
        "matched_module": "mission_control.governance_coherence.governance_coherence_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_153 is False else "true",
        "autonomous_governance_correction_enabled": "false"
        if AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153 is False
        else "true",
        "mutation_scope": "governance_coherence_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "coherence_not_enforcement",
        **extra,
    }


def route_governance_coherence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_coherence_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        interpretation = build_governance_policy_interpretation(session_id=session_id)
        interp = interpretation.interpretation if interpretation.ok else {}
        record, blockers = append_governance_coherence_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(interp.get("plan_id") or "") or None,
            correlation_id=str(interp.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Coherence record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_coherence_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Coherence record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous correction or constitutional override."
        )
        return (
            body,
            "mission_control_governance_coherence_record",
            _meta(
                session_id,
                stage="coherence_record",
                record_id=str(record.get("record_id") or ""),
                coherence_memory_only="true",
            ),
        )

    if not is_governance_coherence_intent(text):
        return None

    result = build_governance_coherence(session_id=session_id)
    if not result.ok:
        body = f"Governance coherence unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_coherence_blocked", _meta(session_id, stage="blocked")

    body = render_governance_coherence(result.coherence)
    return (
        body,
        "mission_control_governance_coherence",
        _meta(
            session_id,
            stage="governance_coherence",
            coherence_record_count=str(result.coherence.get("coherence_record_count", 0)),
        ),
    )
