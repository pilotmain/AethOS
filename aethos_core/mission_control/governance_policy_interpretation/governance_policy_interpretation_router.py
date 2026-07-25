# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — chat router for governance policy interpretation."""

from __future__ import annotations

from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_contract import (
    AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152,
    GOVERNANCE_POLICY_INTERPRETATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_152,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_intent import (
    is_governance_policy_interpretation_intent,
    parse_interpretation_record_intent,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_renderer import (
    render_governance_policy_interpretation,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
    build_governance_policy_interpretation,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    append_governance_policy_interpretation_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNANCE_POLICY_INTERPRETATION_ROUTE_ID,
        "matched_module": "mission_control.governance_policy_interpretation.governance_policy_interpretation_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_152 is False else "true",
        "automatic_doctrine_enforcement_enabled": "false"
        if AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152 is False
        else "true",
        "mutation_scope": "governance_policy_interpretation_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "interpretation_not_enforcement",
        **extra,
    }


def route_governance_policy_interpretation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_interpretation_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        doctrine = build_governance_doctrine(session_id=session_id)
        doc = doctrine.doctrine if doctrine.ok else {}
        record, blockers = append_governance_policy_interpretation_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(doc.get("plan_id") or "") or None,
            correlation_id=str(doc.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Interpretation record blocked: {', '.join(blockers)}"
            return body, "mission_control_governance_policy_interpretation_record_blocked", _meta(
                session_id, stage="blocked"
            )
        body = (
            f"Interpretation record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Interpretation assistance only — no autonomous enforcement or rulings."
        )
        return (
            body,
            "mission_control_governance_policy_interpretation_record",
            _meta(
                session_id,
                stage="interpretation_record",
                record_id=str(record.get("record_id") or ""),
                interpretation_memory_only="true",
            ),
        )

    if not is_governance_policy_interpretation_intent(text):
        return None

    result = build_governance_policy_interpretation(session_id=session_id)
    if not result.ok:
        body = f"Governance policy interpretation unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_governance_policy_interpretation_blocked", _meta(session_id, stage="blocked")

    body = render_governance_policy_interpretation(result.interpretation)
    return (
        body,
        "mission_control_governance_policy_interpretation",
        _meta(
            session_id,
            stage="governance_policy_interpretation",
            interpretation_record_count=str(result.interpretation.get("interpretation_record_count", 0)),
        ),
    )
