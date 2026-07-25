# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — chat router for constitutional legitimacy."""

from __future__ import annotations

from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import build_constitutional_audit
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_contract import (
    AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161,
    CONSTITUTIONAL_LEGITIMACY_ROUTE_ID,
    MUTATION_PERFORMED_FIX_161,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_intent import (
    is_constitutional_legitimacy_intent,
    parse_legitimacy_record_intent,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_renderer import (
    render_constitutional_legitimacy,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
    build_constitutional_legitimacy,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_store import (
    append_constitutional_legitimacy_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CONSTITUTIONAL_LEGITIMACY_ROUTE_ID,
        "matched_module": "mission_control.constitutional_legitimacy.constitutional_legitimacy_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_161 is False else "true",
        "autonomous_legitimacy_enforcement_enabled": "false"
        if AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161 is False
        else "true",
        "mutation_scope": "constitutional_legitimacy_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "legitimacy_cognition_not_trust_authority",
        **extra,
    }


def route_constitutional_legitimacy(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_legitimacy_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        audit = build_constitutional_audit(session_id=session_id)
        aud = audit.constitutional_audit if audit.ok else {}
        record, blockers = append_constitutional_legitimacy_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(aud.get("plan_id") or "") or None,
            correlation_id=str(aud.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Constitutional legitimacy record blocked: {', '.join(blockers)}"
            return body, "mission_control_constitutional_legitimacy_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Constitutional legitimacy record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous legitimacy enforcement or public trust manipulation."
        )
        return (
            body,
            "mission_control_constitutional_legitimacy_record",
            _meta(
                session_id,
                stage="constitutional_legitimacy_record",
                record_id=str(record.get("record_id") or ""),
                constitutional_legitimacy_memory_only="true",
            ),
        )

    if not is_constitutional_legitimacy_intent(text):
        return None

    result = build_constitutional_legitimacy(session_id=session_id)
    if not result.ok:
        body = f"Constitutional legitimacy unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_constitutional_legitimacy_blocked", _meta(session_id, stage="blocked")

    body = render_constitutional_legitimacy(result.constitutional_legitimacy)
    return (
        body,
        "mission_control_constitutional_legitimacy",
        _meta(
            session_id,
            stage="constitutional_legitimacy",
            legitimacy_record_count=str(result.constitutional_legitimacy.get("legitimacy_record_count", 0)),
        ),
    )
