# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F5 / FIX 351 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_351,
    AUTOMATIC_PLAN_DOWNGRADE_FIX_351,
    AUTOMATIC_PLAN_UPGRADE_FIX_351,
    COMMERCIAL_AUTHORITY_FIX_351,
    COMMERCIAL_VALIDATION_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_351,
    LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351,
    MUTATION_PERFORMED_FIX_351,
    PAYMENT_PROCESSING_FIX_351,
    PRICING_MUTATION_FIX_351,
    TRUST_MUTATION_AUTHORITY_FIX_351,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_intent import (
    handle_commercial_validation_intent,
    parse_commercial_validation_intent,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_renderer import (
    render_commercial_validation_program,
)
from aethos_core.workstreams.commercial_validation_program.commercial_validation_program_service import (
    build_commercial_validation_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": COMMERCIAL_VALIDATION_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.commercial_validation_program.commercial_validation_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_351 is False else "true",
        "commercial_authority": "false" if COMMERCIAL_AUTHORITY_FIX_351 is False else "true",
        "payment_processing": "false" if PAYMENT_PROCESSING_FIX_351 is False else "true",
        "automatic_plan_upgrade": "false" if AUTOMATIC_PLAN_UPGRADE_FIX_351 is False else "true",
        "automatic_plan_downgrade": "false" if AUTOMATIC_PLAN_DOWNGRADE_FIX_351 is False else "true",
        "pricing_mutation": "false" if PRICING_MUTATION_FIX_351 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_351 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_351 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_351 is False else "true",
        "local_commercial_validation_executable": "true"
        if LOCAL_COMMERCIAL_VALIDATION_EXECUTABLE_FIX_351 is True
        else "false",
        "mutation_scope": "commercial_validation_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "commercial_validation_not_commercial_authority",
        **extra,
    }


def route_commercial_validation_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_commercial_validation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_commercial_validation_intent(intent, session_id=sid)

    if handled.get("action") == "cohort":
        entry = handled.get("entry") or {}
        body = (
            f"Commercial cohort customer **{entry.get('customer_id')}** registered "
            f"({entry.get('plan')} / {entry.get('segment')}). "
            "Commercial validation ≠ commercial authority."
        )
        return (
            body,
            "workstream_commercial_validation_program_cohort",
            _meta(sid, stage="cohort"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Commercial validation note recorded ({record.get('kind', 'note')}). "
            "Validation measures outcomes — no billing or plan mutation."
        )
        return (
            body,
            "workstream_commercial_validation_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "commercial_validation_dashboard")
    result = build_commercial_validation_program(session_id=sid)
    markdown = render_commercial_validation_program(
        result.commercial_validation_program,
        focus=focus,
    )
    metrics = result.commercial_validation_program.get("metrics") or {}
    headline = (
        f"Activation **{metrics.get('activation_rate')}** · "
        f"Retention **{metrics.get('retention_rate')}** · "
        f"Sustainability **{metrics.get('commercial_sustainability_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_commercial_validation_program",
        _meta(sid, stage="view", focus=focus),
    )
