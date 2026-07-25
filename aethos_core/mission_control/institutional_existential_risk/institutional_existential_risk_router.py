# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — chat router for institutional existential risk."""

from __future__ import annotations

from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_contract import (
    AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158,
    INSTITUTIONAL_EXISTENTIAL_RISK_ROUTE_ID,
    MUTATION_PERFORMED_FIX_158,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_intent import (
    is_institutional_existential_risk_intent,
    parse_existential_risk_record_intent,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_renderer import (
    render_institutional_existential_risk,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
    build_institutional_existential_risk,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_store import (
    append_institutional_existential_risk_record,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
    build_institutional_external_relations,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INSTITUTIONAL_EXISTENTIAL_RISK_ROUTE_ID,
        "matched_module": "mission_control.institutional_existential_risk.institutional_existential_risk_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_158 is False else "true",
        "autonomous_self_preservation_enabled": "false"
        if AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158 is False
        else "true",
        "mutation_scope": "institutional_existential_risk_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "existential_risk_not_self_preservation",
        **extra,
    }


def route_institutional_existential_risk(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_existential_risk_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        external = build_institutional_external_relations(session_id=session_id)
        ext = external.external_relations if external.ok else {}
        record, blockers = append_institutional_existential_risk_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(ext.get("plan_id") or "") or None,
            correlation_id=str(ext.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Existential risk record blocked: {', '.join(blockers)}"
            return body, "mission_control_institutional_existential_risk_record_blocked", _meta(
                session_id, stage="blocked"
            )
        body = (
            f"Existential risk record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous self-preservation or constitutional override."
        )
        return (
            body,
            "mission_control_institutional_existential_risk_record",
            _meta(
                session_id,
                stage="existential_risk_record",
                record_id=str(record.get("record_id") or ""),
                existential_risk_memory_only="true",
            ),
        )

    if not is_institutional_existential_risk_intent(text):
        return None

    result = build_institutional_existential_risk(session_id=session_id)
    if not result.ok:
        body = f"Institutional existential risk unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_institutional_existential_risk_blocked", _meta(session_id, stage="blocked")

    body = render_institutional_existential_risk(result.existential_risk)
    return (
        body,
        "mission_control_institutional_existential_risk",
        _meta(
            session_id,
            stage="institutional_existential_risk",
            existential_risk_record_count=str(result.existential_risk.get("existential_risk_record_count", 0)),
        ),
    )
