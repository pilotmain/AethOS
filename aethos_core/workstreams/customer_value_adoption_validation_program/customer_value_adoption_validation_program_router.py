# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F2 / FIX 348 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_348,
    AUTOMATED_OUTREACH_FIX_348,
    CUSTOMER_MANIPULATION_FIX_348,
    CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_348,
    LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348,
    MUTATION_PERFORMED_FIX_348,
    TRUST_MUTATION_AUTHORITY_FIX_348,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_intent import (
    handle_customer_value_adoption_validation_intent,
    parse_customer_value_adoption_validation_intent,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_renderer import (
    render_customer_value_adoption_validation_program,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_service import (
    build_customer_value_adoption_validation_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_VALUE_ADOPTION_VALIDATION_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_348 is False else "true",
        "customer_manipulation": "false" if CUSTOMER_MANIPULATION_FIX_348 is False else "true",
        "automated_outreach": "false" if AUTOMATED_OUTREACH_FIX_348 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_348 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_348 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_348 is False else "true",
        "local_value_validation_executable": "true"
        if LOCAL_VALUE_VALIDATION_EXECUTABLE_FIX_348 is True
        else "false",
        "mutation_scope": "customer_value_adoption_validation_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "value_validation_not_customer_manipulation",
        **extra,
    }


def route_customer_value_adoption_validation_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_value_adoption_validation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_value_adoption_validation_intent(intent, session_id=sid)

    if handled.get("action") == "observe":
        observation = handled.get("observation") or {}
        body = (
            f"Customer usage observation recorded — workflow **{observation.get('workflow', '—')}**, "
            f"executions **{observation.get('executions', 0)}**. "
            "Value validation ≠ customer manipulation."
        )
        return (
            body,
            "workstream_customer_value_adoption_validation_program_observe",
            _meta(sid, stage="observe"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Customer value note recorded ({record.get('kind', 'note')}). "
            "AethOS measures outcomes — no customer manipulation or automated outreach."
        )
        return (
            body,
            "workstream_customer_value_adoption_validation_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_value_dashboard")
    result = build_customer_value_adoption_validation_program(session_id=sid)
    markdown = render_customer_value_adoption_validation_program(
        result.customer_value_adoption_validation_program,
        focus=focus,
    )
    metrics = result.customer_value_adoption_validation_program.get("metrics") or {}
    headline = (
        f"Adoption **{metrics.get('adoption_rate')}** · "
        f"Retention **{metrics.get('retention_rate')}** · "
        f"Value score **{metrics.get('value_realization_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_customer_value_adoption_validation_program",
        _meta(sid, stage="view", focus=focus),
    )
