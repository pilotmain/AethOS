# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — chat router for institutional external relations."""

from __future__ import annotations

from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_contract import (
    AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157,
    INSTITUTIONAL_EXTERNAL_RELATIONS_ROUTE_ID,
    MUTATION_PERFORMED_FIX_157,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_intent import (
    is_institutional_external_relations_intent,
    parse_external_relations_record_intent,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_renderer import (
    render_institutional_external_relations,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
    build_institutional_external_relations,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_store import (
    append_institutional_external_relations_record,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_service import build_institutional_identity


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INSTITUTIONAL_EXTERNAL_RELATIONS_ROUTE_ID,
        "matched_module": "mission_control.institutional_external_relations.institutional_external_relations_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_157 is False else "true",
        "autonomous_external_negotiation_enabled": "false"
        if AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157 is False
        else "true",
        "mutation_scope": "institutional_external_relations_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "external_relations_not_negotiation",
        **extra,
    }


def route_institutional_external_relations(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_external_relations_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        identity = build_institutional_identity(session_id=session_id)
        ident = identity.identity if identity.ok else {}
        record, blockers = append_institutional_external_relations_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ident.get("plan_id") or "") or None,
            correlation_id=str(ident.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"External relations record blocked: {', '.join(blockers)}"
            return body, "mission_control_institutional_external_relations_record_blocked", _meta(
                session_id, stage="blocked"
            )
        body = (
            f"External relations record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous negotiation or sovereignty delegation."
        )
        return (
            body,
            "mission_control_institutional_external_relations_record",
            _meta(
                session_id,
                stage="external_relations_record",
                record_id=str(record.get("record_id") or ""),
                external_relations_memory_only="true",
            ),
        )

    if not is_institutional_external_relations_intent(text):
        return None

    result = build_institutional_external_relations(session_id=session_id)
    if not result.ok:
        body = f"Institutional external relations unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_institutional_external_relations_blocked", _meta(session_id, stage="blocked")

    body = render_institutional_external_relations(result.external_relations)
    return (
        body,
        "mission_control_institutional_external_relations",
        _meta(
            session_id,
            stage="institutional_external_relations",
            external_relations_record_count=str(result.external_relations.get("external_relations_record_count", 0)),
        ),
    )
