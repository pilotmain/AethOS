# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — chat router for public launch readiness freeze."""

from __future__ import annotations

from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314,
    AUTOMATIC_LAUNCH_ENABLED_FIX_314,
    LAUNCH_DECISION_AUTHORITY_FIX_314,
    LAUNCH_FREEZE_AUTHORITY_FIX_314,
    MUTATION_PERFORMED_FIX_314,
    PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_314,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_intent import (
    handle_public_launch_readiness_freeze_intent,
    parse_public_launch_readiness_freeze_intent,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_renderer import (
    render_public_launch_readiness_freeze,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
    build_public_launch_readiness_freeze,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID,
        "matched_module": (
            "mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_314 is False else "true",
        "launch_freeze_authority": "false" if LAUNCH_FREEZE_AUTHORITY_FIX_314 is False else "true",
        "automatic_launch_enabled": "false" if AUTOMATIC_LAUNCH_ENABLED_FIX_314 is False else "true",
        "automatic_beta_expansion_enabled": "false"
        if AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_314 is False else "true",
        "launch_decision_authority": "false" if LAUNCH_DECISION_AUTHORITY_FIX_314 is False else "true",
        "mutation_scope": "public_launch_readiness_freeze",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "launch_readiness_freeze_not_launch_authority",
        **extra,
    }


def route_public_launch_readiness_freeze(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_public_launch_readiness_freeze_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_public_launch_readiness_freeze_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded launch freeze note ({record.get('kind', 'note')}). "
            "Launch readiness freeze ≠ launch authority."
        )
        return (
            body,
            "mission_control_public_launch_readiness_freeze_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "launch_readiness_freeze_dashboard")
    result = build_public_launch_readiness_freeze(session_id=sid)
    markdown = render_public_launch_readiness_freeze(result.public_launch_readiness_freeze, focus=focus)
    recommendation = result.public_launch_readiness_freeze.get("launch_recommendation_freeze", "—")
    headline = (
        f"Launch recommendation freeze **{recommendation}**. "
        "Official evidence baseline frozen — humans decide launch, not AethOS."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_public_launch_readiness_freeze",
        _meta(sid, stage="view", focus=focus, recommendation=str(recommendation)),
    )
