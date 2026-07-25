# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — chat router for launch operations center."""

from __future__ import annotations

from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313,
    AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313,
    AUTOMATIC_LAUNCH_ENABLED_FIX_313,
    AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313,
    LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
    LAUNCH_OPERATIONS_CENTER_ROUTE_ID,
    MUTATION_PERFORMED_FIX_313,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_intent import (
    handle_launch_operations_center_intent,
    parse_launch_operations_center_intent,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_renderer import (
    render_launch_operations_center,
)
from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
    build_launch_operations_center,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": LAUNCH_OPERATIONS_CENTER_ROUTE_ID,
        "matched_module": "mission_control.launch_operations_center.launch_operations_center_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_313 is False else "true",
        "launch_operations_authority": "false" if LAUNCH_OPERATIONS_AUTHORITY_FIX_313 is False else "true",
        "automatic_launch_enabled": "false" if AUTOMATIC_LAUNCH_ENABLED_FIX_313 is False else "true",
        "automatic_beta_expansion_enabled": "false"
        if AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313 is False
        else "true",
        "automatic_customer_admission_enabled": "false"
        if AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313 is False
        else "true",
        "automatic_provider_mutation_enabled": "false"
        if AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313 is False
        else "true",
        "mutation_scope": "launch_operations_center",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "launch_operations_visibility_not_launch_authority",
        **extra,
    }


def route_launch_operations_center(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_launch_operations_center_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_launch_operations_center_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded launch operations note ({record.get('kind', 'note')}). "
            "Launch operations visibility ≠ launch authority."
        )
        return (
            body,
            "mission_control_launch_operations_center_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "launch_operations_dashboard")
    result = build_launch_operations_center(session_id=sid)
    markdown = render_launch_operations_center(result.launch_operations_center, focus=focus)
    recommendation = result.launch_operations_center.get("launch_recommendation", "—")
    phase = result.launch_operations_center.get("current_launch_phase", "—")
    headline = (
        f"Launch phase **{phase}** · recommendation **{recommendation}**. "
        "Unified launch operations — humans decide launch, not AethOS."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_launch_operations_center",
        _meta(
            sid,
            stage="view",
            focus=focus,
            recommendation=str(recommendation),
            phase=str(phase),
        ),
    )
