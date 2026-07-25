# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — chat router for institutional identity + constitutional intent."""

from __future__ import annotations

from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution
from aethos_core.mission_control.institutional_identity.institutional_identity_contract import (
    AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156,
    INSTITUTIONAL_IDENTITY_ROUTE_ID,
    MUTATION_PERFORMED_FIX_156,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_intent import (
    is_institutional_identity_intent,
    parse_identity_record_intent,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_renderer import (
    render_institutional_identity,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_service import build_institutional_identity
from aethos_core.mission_control.institutional_identity.institutional_identity_store import (
    append_institutional_identity_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INSTITUTIONAL_IDENTITY_ROUTE_ID,
        "matched_module": "mission_control.institutional_identity.institutional_identity_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_156 is False else "true",
        "autonomous_institutional_redirection_enabled": "false"
        if AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156 is False
        else "true",
        "mutation_scope": "institutional_identity_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "identity_not_redirection",
        **extra,
    }


def route_institutional_identity(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_identity_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        evolution = build_governance_evolution(session_id=session_id)
        evo = evolution.evolution if evolution.ok else {}
        record, blockers = append_institutional_identity_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(evo.get("plan_id") or "") or None,
            correlation_id=str(evo.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Identity record blocked: {', '.join(blockers)}"
            return body, "mission_control_institutional_identity_record_blocked", _meta(session_id, stage="blocked")
        body = (
            f"Identity record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Recommendation-only — no autonomous redirection or constitutional rewriting."
        )
        return (
            body,
            "mission_control_institutional_identity_record",
            _meta(
                session_id,
                stage="identity_record",
                record_id=str(record.get("record_id") or ""),
                identity_memory_only="true",
            ),
        )

    if not is_institutional_identity_intent(text):
        return None

    result = build_institutional_identity(session_id=session_id)
    if not result.ok:
        body = f"Institutional identity unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_institutional_identity_blocked", _meta(session_id, stage="blocked")

    body = render_institutional_identity(result.identity)
    return (
        body,
        "mission_control_institutional_identity",
        _meta(
            session_id,
            stage="institutional_identity",
            identity_record_count=str(result.identity.get("identity_record_count", 0)),
        ),
    )
