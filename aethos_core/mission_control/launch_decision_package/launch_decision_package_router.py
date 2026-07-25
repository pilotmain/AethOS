# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — chat router for launch decision package."""

from __future__ import annotations

from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315,
    AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315,
    AUTOMATIC_LAUNCH_ENABLED_FIX_315,
    LAUNCH_DECISION_AUTHORITY_FIX_315,
    LAUNCH_DECISION_PACKAGE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_315,
    TRUST_MUTATION_AUTHORITY_FIX_315,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_intent import (
    handle_launch_decision_package_intent,
    parse_launch_decision_package_intent,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_renderer import (
    render_launch_decision_package,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
    build_launch_decision_package,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": LAUNCH_DECISION_PACKAGE_ROUTE_ID,
        "matched_module": "mission_control.launch_decision_package.launch_decision_package_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_315 is False else "true",
        "launch_decision_authority": "false" if LAUNCH_DECISION_AUTHORITY_FIX_315 is False else "true",
        "automatic_launch_approval_enabled": "false"
        if AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315 is False
        else "true",
        "automatic_launch_enabled": "false" if AUTOMATIC_LAUNCH_ENABLED_FIX_315 is False else "true",
        "automatic_beta_expansion_enabled": "false"
        if AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_315 is False else "true",
        "mutation_scope": "launch_decision_package",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "launch_decision_package_not_launch_decision",
        **extra,
    }


def route_launch_decision_package(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_launch_decision_package_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_launch_decision_package_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded launch decision note ({record.get('kind', 'note')}). "
            "Launch decision package ≠ launch decision."
        )
        return (
            body,
            "mission_control_launch_decision_package_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "launch_decision_dashboard")
    result = build_launch_decision_package(session_id=sid)
    markdown = render_launch_decision_package(result.launch_decision_package, focus=focus)
    recommendation = result.launch_decision_package.get("launch_recommendation_package", "—")
    headline = (
        f"Launch recommendation package **{recommendation}**. "
        "Official review package prepared — humans approve launch, not AethOS."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_launch_decision_package",
        _meta(sid, stage="view", focus=focus, recommendation=str(recommendation)),
    )
