# SPDX-License-Identifier: Apache-2.0
"""FIX 162 — chat router for constitutional pluralism."""

from __future__ import annotations

from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
    build_constitutional_legitimacy,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_contract import (
    AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162,
    CONSTITUTIONAL_PLURALISM_ROUTE_ID,
    MUTATION_PERFORMED_FIX_162,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_intent import (
    is_constitutional_pluralism_intent,
    parse_pluralism_record_intent,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_renderer import (
    render_constitutional_pluralism,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
    build_constitutional_pluralism,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
    append_constitutional_pluralism_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CONSTITUTIONAL_PLURALISM_ROUTE_ID,
        "matched_module": "mission_control.constitutional_pluralism.constitutional_pluralism_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_162 is False else "true",
        "authoritative_worldview_selection_enabled": "false"
        if AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162 is False
        else "true",
        "mutation_scope": "constitutional_pluralism_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "pluralism_cognition_not_arbitration_authority",
        **extra,
    }


def route_constitutional_pluralism(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_pluralism_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        legitimacy = build_constitutional_legitimacy(session_id=session_id)
        leg = legitimacy.constitutional_legitimacy if legitimacy.ok else {}
        record, blockers = append_constitutional_pluralism_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(leg.get("plan_id") or "") or None,
            correlation_id=str(leg.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Constitutional pluralism record blocked: {', '.join(blockers)}"
            return body, "mission_control_constitutional_pluralism_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Constitutional pluralism record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no authoritative worldview selection or autonomous arbitration."
        )
        return (
            body,
            "mission_control_constitutional_pluralism_record",
            _meta(
                session_id,
                stage="constitutional_pluralism_record",
                record_id=str(record.get("record_id") or ""),
                constitutional_pluralism_memory_only="true",
            ),
        )

    if not is_constitutional_pluralism_intent(text):
        return None

    result = build_constitutional_pluralism(session_id=session_id)
    if not result.ok:
        body = f"Constitutional pluralism unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_constitutional_pluralism_blocked", _meta(session_id, stage="blocked")

    body = render_constitutional_pluralism(result.constitutional_pluralism)
    return (
        body,
        "mission_control_constitutional_pluralism",
        _meta(
            session_id,
            stage="constitutional_pluralism",
            pluralism_record_count=str(result.constitutional_pluralism.get("pluralism_record_count", 0)),
        ),
    )
