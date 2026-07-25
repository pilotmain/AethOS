# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F4 / FIX 350 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_350,
    AUTOMATED_OUTREACH_FIX_350,
    CUSTOMER_AUTHORITY_FIX_350,
    CUSTOMER_MANIPULATION_FIX_350,
    CUSTOMER_SCALE_VALIDATION_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_350,
    LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350,
    MUTATION_PERFORMED_FIX_350,
    TRUST_MUTATION_AUTHORITY_FIX_350,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_intent import (
    handle_customer_scale_validation_intent,
    parse_customer_scale_validation_intent,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_renderer import (
    render_customer_scale_validation_program,
)
from aethos_core.workstreams.customer_scale_validation_program.customer_scale_validation_program_service import (
    build_customer_scale_validation_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_SCALE_VALIDATION_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.customer_scale_validation_program.customer_scale_validation_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_350 is False else "true",
        "customer_authority": "false" if CUSTOMER_AUTHORITY_FIX_350 is False else "true",
        "customer_manipulation": "false" if CUSTOMER_MANIPULATION_FIX_350 is False else "true",
        "automated_outreach": "false" if AUTOMATED_OUTREACH_FIX_350 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_350 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_350 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_350 is False else "true",
        "local_scale_validation_executable": "true"
        if LOCAL_SCALE_VALIDATION_EXECUTABLE_FIX_350 is True
        else "false",
        "mutation_scope": "customer_scale_validation_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "scale_validation_not_customer_authority",
        **extra,
    }


def route_customer_scale_validation_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_scale_validation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_scale_validation_intent(intent, session_id=sid)

    if handled.get("action") == "cohort":
        entry = handled.get("entry") or {}
        body = (
            f"Scale cohort customer **{entry.get('customer_id')}** registered "
            f"({entry.get('provider')} / {entry.get('environment')}). "
            "Scale validation ≠ customer authority."
        )
        return (
            body,
            "workstream_customer_scale_validation_program_cohort",
            _meta(sid, stage="cohort"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Customer scale note recorded ({record.get('kind', 'note')}). "
            "Scale validation measures capability — no governance bypass."
        )
        return (
            body,
            "workstream_customer_scale_validation_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_scale_dashboard")
    result = build_customer_scale_validation_program(session_id=sid)
    markdown = render_customer_scale_validation_program(
        result.customer_scale_validation_program,
        focus=focus,
    )
    metrics = result.customer_scale_validation_program.get("metrics") or {}
    headline = (
        f"Concurrent **{metrics.get('concurrent_customers')}** · "
        f"Throughput **{metrics.get('delivery_throughput')}** · "
        f"Bottlenecks **{metrics.get('bottleneck_frequency')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_customer_scale_validation_program",
        _meta(sid, stage="view", focus=focus),
    )
