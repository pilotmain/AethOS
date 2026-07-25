# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F3 / FIX 349 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_349,
    AUTOMATED_OUTREACH_FIX_349,
    CUSTOMER_AUTHORITY_FIX_349,
    CUSTOMER_MANIPULATION_FIX_349,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_349,
    LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349,
    MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ROUTE_ID,
    MUTATION_PERFORMED_FIX_349,
    TRUST_MUTATION_AUTHORITY_FIX_349,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_intent import (
    handle_multi_customer_value_proof_intent,
    parse_multi_customer_value_proof_intent,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_renderer import (
    render_multi_customer_value_proof_program,
)
from aethos_core.workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_service import (
    build_multi_customer_value_proof_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MULTI_CUSTOMER_VALUE_PROOF_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.multi_customer_value_proof_program.multi_customer_value_proof_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_349 is False else "true",
        "customer_authority": "false" if CUSTOMER_AUTHORITY_FIX_349 is False else "true",
        "customer_manipulation": "false" if CUSTOMER_MANIPULATION_FIX_349 is False else "true",
        "automated_outreach": "false" if AUTOMATED_OUTREACH_FIX_349 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_349 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_349 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_349 is False else "true",
        "local_multi_customer_proof_executable": "true"
        if LOCAL_MULTI_CUSTOMER_PROOF_EXECUTABLE_FIX_349 is True
        else "false",
        "mutation_scope": "multi_customer_value_proof_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "multi_customer_proof_not_customer_authority",
        **extra,
    }


def route_multi_customer_value_proof_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_multi_customer_value_proof_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_multi_customer_value_proof_intent(intent, session_id=sid)

    if handled.get("action") == "cohort":
        entry = handled.get("entry") or {}
        body = (
            f"Cohort customer **{entry.get('customer_id')}** registered "
            f"({entry.get('delivery_type')} / {entry.get('environment')}). "
            "Multi-customer validation ≠ customer authority."
        )
        return (
            body,
            "workstream_multi_customer_value_proof_program_cohort",
            _meta(sid, stage="cohort"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Multi-customer note recorded ({record.get('kind', 'note')}). "
            "Humans remain responsible for customer acceptance and success decisions."
        )
        return (
            body,
            "workstream_multi_customer_value_proof_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "multi_customer_value_dashboard")
    result = build_multi_customer_value_proof_program(session_id=sid)
    markdown = render_multi_customer_value_proof_program(
        result.multi_customer_value_proof_program,
        focus=focus,
    )
    metrics = result.multi_customer_value_proof_program.get("metrics") or {}
    headline = (
        f"Repeatability **{metrics.get('repeatability_score')}** · "
        f"Cohort adoption **{metrics.get('adoption_rate')}** · "
        f"Value score **{metrics.get('value_realization_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_multi_customer_value_proof_program",
        _meta(sid, stage="view", focus=focus),
    )
