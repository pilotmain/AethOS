# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence chat router."""

from __future__ import annotations

from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
    AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328,
    AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328,
    AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328,
    MUTATION_PERFORMED_FIX_328,
    ORGANIZATIONAL_AUTHORITY_FIX_328,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_intent import (
    handle_organizational_effectiveness_intelligence_intent,
    parse_organizational_effectiveness_intelligence_intent,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_renderer import (
    render_organizational_effectiveness_intelligence,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_service import (
    build_organizational_effectiveness_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.organizational_effectiveness_intelligence."
            "organizational_effectiveness_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_328 is False else "true",
        "organizational_authority": "false" if ORGANIZATIONAL_AUTHORITY_FIX_328 is False else "true",
        "automatic_role_changes_enabled": "false" if AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328 is False else "true",
        "automatic_governance_changes_enabled": "false"
        if AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328 is False
        else "true",
        "automatic_resource_reallocation_enabled": "false"
        if AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328 is False
        else "true",
        "automatic_organizational_changes_enabled": "false"
        if AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328 is False
        else "true",
        "mutation_scope": "organizational_effectiveness_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "organizational_effectiveness_without_organizational_authority",
        **extra,
    }


def route_organizational_effectiveness_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_organizational_effectiveness_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_organizational_effectiveness_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded organization review note ({record.get('kind', 'note')}). "
            "AethOS evaluates organizational effectiveness; humans manage organizations."
        )
        return (
            body,
            "mission_control_organizational_effectiveness_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "organizational_effectiveness_dashboard")
    result = build_organizational_effectiveness_intelligence(session_id=sid)
    markdown = render_organizational_effectiveness_intelligence(
        result.organizational_effectiveness_intelligence,
        focus=focus,
    )
    dashboard = result.organizational_effectiveness_intelligence.get("sections", {}).get(
        "organizational_effectiveness_dashboard",
        [{}],
    )[0]
    headline = (
        "Organizational effectiveness intelligence — evaluation only. "
        f"Effectiveness **{dashboard.get('overall_effectiveness_level', 'STABLE')}**, "
        f"friction signals **{dashboard.get('friction_signal_count', 0)}**. "
        "No automatic organizational changes."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_organizational_effectiveness_intelligence",
        _meta(
            sid,
            stage="view",
            focus=focus,
            effectiveness_level=str(dashboard.get("overall_effectiveness_level", "STABLE")),
        ),
    )
