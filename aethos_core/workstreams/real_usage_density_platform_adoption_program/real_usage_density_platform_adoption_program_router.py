# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G2 / FIX 355 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_contract import (
    AUTHORITY_EXPANSION_FIX_355,
    AUTOMATED_OUTREACH_FIX_355,
    BEHAVIORAL_MANIPULATION_FIX_355,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_355,
    LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355,
    MUTATION_PERFORMED_FIX_355,
    PLAN_MUTATION_FIX_355,
    REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_355,
    TRUST_MUTATION_FIX_355,
    USER_AUTHORITY_FIX_355,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_intent import (
    handle_platform_adoption_intent,
    parse_platform_adoption_intent,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_renderer import (
    render_real_usage_density_platform_adoption_program,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_service import (
    build_real_usage_density_platform_adoption_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REAL_USAGE_DENSITY_PLATFORM_ADOPTION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.real_usage_density_platform_adoption_program."
            "real_usage_density_platform_adoption_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_355 is False else "true",
        "user_authority": "false" if USER_AUTHORITY_FIX_355 is False else "true",
        "automated_outreach": "false" if AUTOMATED_OUTREACH_FIX_355 is False else "true",
        "behavioral_manipulation": "false" if BEHAVIORAL_MANIPULATION_FIX_355 is False else "true",
        "plan_mutation": "false" if PLAN_MUTATION_FIX_355 is False else "true",
        "trust_mutation": "false" if TRUST_MUTATION_FIX_355 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_355 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_355 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_355 is False else "true",
        "local_usage_adoption_executable": "true" if LOCAL_USAGE_ADOPTION_EXECUTABLE_FIX_355 is True else "false",
        "mutation_scope": "real_usage_density_platform_adoption_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "usage_density_not_user_authority",
        **extra,
    }


def route_real_usage_density_platform_adoption_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_platform_adoption_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_platform_adoption_intent(intent, session_id=sid)

    if handled.get("action") == "session":
        entry = handled.get("entry") or {}
        body = (
            f"Usage session **{entry.get('usage_session_id')}** registered "
            f"({entry.get('surface')}). Usage density ≠ user authority."
        )
        return (
            body,
            "workstream_real_usage_density_platform_adoption_program_session",
            _meta(sid, stage="session"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Platform adoption note recorded ({record.get('kind', 'note')}). "
            "Usage measurement observes behavior — no outreach or plan mutation."
        )
        return (
            body,
            "workstream_real_usage_density_platform_adoption_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "platform_adoption_dashboard")
    result = build_real_usage_density_platform_adoption_program(session_id=sid)
    markdown = render_real_usage_density_platform_adoption_program(
        result.real_usage_density_platform_adoption_program,
        focus=focus,
    )
    metrics = result.real_usage_density_platform_adoption_program.get("metrics") or {}
    headline = (
        f"Active **{metrics.get('active_users')}** · "
        f"Adoption **{metrics.get('workflow_adoption_rate')}** · "
        f"Dependence **{metrics.get('platform_dependence_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_real_usage_density_platform_adoption_program",
        _meta(sid, stage="view", focus=focus),
    )
