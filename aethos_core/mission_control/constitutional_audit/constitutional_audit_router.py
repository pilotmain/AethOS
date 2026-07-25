# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — chat router for constitutional audit."""

from __future__ import annotations

from aethos_core.mission_control.constitutional_audit.constitutional_audit_contract import (
    AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160,
    CONSTITUTIONAL_AUDIT_ROUTE_ID,
    MUTATION_PERFORMED_FIX_160,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_intent import (
    is_constitutional_audit_intent,
    parse_audit_record_intent,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_renderer import (
    render_constitutional_audit,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import (
    build_constitutional_audit,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_store import (
    append_constitutional_audit_record,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import build_constitutional_ethics


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CONSTITUTIONAL_AUDIT_ROUTE_ID,
        "matched_module": "mission_control.constitutional_audit.constitutional_audit_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_160 is False else "true",
        "autonomous_disclosure_enabled": "false"
        if AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160 is False
        else "true",
        "mutation_scope": "constitutional_audit_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "accountability_cognition_not_disclosure_authority",
        **extra,
    }


def route_constitutional_audit(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_audit_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        ethics = build_constitutional_ethics(session_id=session_id)
        eth = ethics.constitutional_ethics if ethics.ok else {}
        record, blockers = append_constitutional_audit_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(eth.get("plan_id") or "") or None,
            correlation_id=str(eth.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Constitutional audit record blocked: {', '.join(blockers)}"
            return body, "mission_control_constitutional_audit_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Constitutional audit record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous disclosure or public communication authority."
        )
        return (
            body,
            "mission_control_constitutional_audit_record",
            _meta(
                session_id,
                stage="constitutional_audit_record",
                record_id=str(record.get("record_id") or ""),
                constitutional_audit_memory_only="true",
            ),
        )

    if not is_constitutional_audit_intent(text):
        return None

    result = build_constitutional_audit(session_id=session_id)
    if not result.ok:
        body = f"Constitutional audit unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_constitutional_audit_blocked", _meta(session_id, stage="blocked")

    body = render_constitutional_audit(result.constitutional_audit)
    return (
        body,
        "mission_control_constitutional_audit",
        _meta(
            session_id,
            stage="constitutional_audit",
            audit_record_count=str(result.constitutional_audit.get("audit_record_count", 0)),
        ),
    )
