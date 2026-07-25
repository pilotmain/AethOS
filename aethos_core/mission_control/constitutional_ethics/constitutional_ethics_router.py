# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — chat router for constitutional ethics."""

from __future__ import annotations

from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_contract import (
    AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159,
    CONSTITUTIONAL_ETHICS_ROUTE_ID,
    MUTATION_PERFORMED_FIX_159,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_intent import (
    is_constitutional_ethics_intent,
    parse_ethics_record_intent,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_renderer import (
    render_constitutional_ethics,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import (
    build_constitutional_ethics,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_store import (
    append_constitutional_ethics_record,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
    build_institutional_existential_risk,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CONSTITUTIONAL_ETHICS_ROUTE_ID,
        "matched_module": "mission_control.constitutional_ethics.constitutional_ethics_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_159 is False else "true",
        "autonomous_moral_authority_enabled": "false"
        if AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159 is False
        else "true",
        "mutation_scope": "constitutional_ethics_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "ethical_cognition_not_moral_authority",
        **extra,
    }


def route_constitutional_ethics(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_ethics_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        existential = build_institutional_existential_risk(session_id=session_id)
        ex = existential.existential_risk if existential.ok else {}
        record, blockers = append_constitutional_ethics_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ex.get("plan_id") or "") or None,
            correlation_id=str(ex.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Constitutional ethics record blocked: {', '.join(blockers)}"
            return body, "mission_control_constitutional_ethics_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Constitutional ethics record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous moral authority or value enforcement."
        )
        return (
            body,
            "mission_control_constitutional_ethics_record",
            _meta(
                session_id,
                stage="constitutional_ethics_record",
                record_id=str(record.get("record_id") or ""),
                constitutional_ethics_memory_only="true",
            ),
        )

    if not is_constitutional_ethics_intent(text):
        return None

    result = build_constitutional_ethics(session_id=session_id)
    if not result.ok:
        body = f"Constitutional ethics unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_constitutional_ethics_blocked", _meta(session_id, stage="blocked")

    body = render_constitutional_ethics(result.constitutional_ethics)
    return (
        body,
        "mission_control_constitutional_ethics",
        _meta(
            session_id,
            stage="constitutional_ethics",
            ethics_record_count=str(result.constitutional_ethics.get("ethics_record_count", 0)),
        ),
    )
