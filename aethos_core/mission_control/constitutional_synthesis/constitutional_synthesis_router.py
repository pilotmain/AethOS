# SPDX-License-Identifier: Apache-2.0
"""FIX 163 — chat router for constitutional synthesis."""

from __future__ import annotations

from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
    build_constitutional_pluralism,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_contract import (
    AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163,
    CONSTITUTIONAL_SYNTHESIS_ROUTE_ID,
    MUTATION_PERFORMED_FIX_163,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_intent import (
    is_constitutional_synthesis_intent,
    parse_synthesis_record_intent,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_renderer import (
    render_constitutional_synthesis,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
    build_constitutional_synthesis,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_store import (
    append_constitutional_synthesis_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CONSTITUTIONAL_SYNTHESIS_ROUTE_ID,
        "matched_module": "mission_control.constitutional_synthesis.constitutional_synthesis_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_163 is False else "true",
        "autonomous_constitutional_decisions_enabled": "false"
        if AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163 is False
        else "true",
        "mutation_scope": "constitutional_synthesis_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "synthesis_cognition_not_constitutional_authority",
        **extra,
    }


def route_constitutional_synthesis(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_synthesis_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        pluralism = build_constitutional_pluralism(session_id=session_id)
        pl = pluralism.constitutional_pluralism if pluralism.ok else {}
        record, blockers = append_constitutional_synthesis_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(pl.get("plan_id") or "") or None,
            correlation_id=str(pl.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Constitutional synthesis record blocked: {', '.join(blockers)}"
            return body, "mission_control_constitutional_synthesis_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Constitutional synthesis record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous constitutional decisions or authority."
        )
        return (
            body,
            "mission_control_constitutional_synthesis_record",
            _meta(
                session_id,
                stage="constitutional_synthesis_record",
                record_id=str(record.get("record_id") or ""),
                constitutional_synthesis_memory_only="true",
            ),
        )

    if not is_constitutional_synthesis_intent(text):
        return None

    result = build_constitutional_synthesis(session_id=session_id)
    if not result.ok:
        body = f"Constitutional synthesis unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_constitutional_synthesis_blocked", _meta(session_id, stage="blocked")

    body = render_constitutional_synthesis(result.constitutional_synthesis)
    return (
        body,
        "mission_control_constitutional_synthesis",
        _meta(
            session_id,
            stage="constitutional_synthesis",
            synthesis_record_count=str(result.constitutional_synthesis.get("synthesis_record_count", 0)),
        ),
    )
