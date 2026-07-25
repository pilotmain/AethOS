# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — chat router for limited beta launch program."""

from __future__ import annotations

from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312,
    AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
    AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312,
    AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312,
    BETA_AUTHORITY_FIX_312,
    LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID,
    MUTATION_PERFORMED_FIX_312,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_intent import (
    handle_limited_beta_launch_program_intent,
    parse_limited_beta_launch_program_intent,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_renderer import (
    render_limited_beta_launch_program,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
    build_limited_beta_launch_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": LIMITED_BETA_LAUNCH_PROGRAM_ROUTE_ID,
        "matched_module": (
            "mission_control.limited_beta_launch_program.limited_beta_launch_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_312 is False else "true",
        "beta_authority": "false" if BETA_AUTHORITY_FIX_312 is False else "true",
        "automatic_user_admission_enabled": "false"
        if AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312 is False
        else "true",
        "automatic_customer_provisioning_enabled": "false"
        if AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312 is False
        else "true",
        "automatic_plan_assignment_enabled": "false"
        if AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312 is False
        else "true",
        "automatic_beta_expansion_enabled": "false"
        if AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312 is False
        else "true",
        "mutation_scope": "limited_beta_launch_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "beta_management_not_provisioning_authority",
        **extra,
    }


def route_limited_beta_launch_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_limited_beta_launch_program_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_limited_beta_launch_program_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded beta program note ({record.get('kind', 'note')}). "
            "Beta program management ≠ customer provisioning authority."
        )
        return (
            body,
            "mission_control_limited_beta_launch_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "beta_operations_dashboard")
    result = build_limited_beta_launch_program(session_id=sid)
    markdown = render_limited_beta_launch_program(result.limited_beta_launch_program, focus=focus)
    recommendation = result.limited_beta_launch_program.get("beta_launch_recommendation", "—")
    headline = (
        f"Beta launch recommendation **{recommendation}**. "
        "Controlled beta framework — humans remain responsible for admissions."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_limited_beta_launch_program",
        _meta(sid, stage="view", focus=focus, recommendation=str(recommendation)),
    )
