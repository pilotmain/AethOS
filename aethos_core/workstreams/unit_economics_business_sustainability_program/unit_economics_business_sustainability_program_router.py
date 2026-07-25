# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F6 / FIX 352 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_contract import (
    AUTHORITY_EXPANSION_FIX_352,
    BILLING_EXECUTION_FIX_352,
    COMMERCIAL_AUTHORITY_FIX_352,
    FINANCIAL_FORECASTING_AS_FACT_FIX_352,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_352,
    LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352,
    MUTATION_PERFORMED_FIX_352,
    PAYMENT_PROCESSING_FIX_352,
    PLAN_MUTATION_FIX_352,
    PRICING_MUTATION_FIX_352,
    TRUST_MUTATION_AUTHORITY_FIX_352,
    UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ROUTE_ID,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_intent import (
    handle_business_sustainability_intent,
    parse_business_sustainability_intent,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_renderer import (
    render_unit_economics_business_sustainability_program,
)
from aethos_core.workstreams.unit_economics_business_sustainability_program.unit_economics_business_sustainability_program_service import (
    build_unit_economics_business_sustainability_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": UNIT_ECONOMICS_BUSINESS_SUSTAINABILITY_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.unit_economics_business_sustainability_program."
            "unit_economics_business_sustainability_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_352 is False else "true",
        "commercial_authority": "false" if COMMERCIAL_AUTHORITY_FIX_352 is False else "true",
        "payment_processing": "false" if PAYMENT_PROCESSING_FIX_352 is False else "true",
        "billing_execution": "false" if BILLING_EXECUTION_FIX_352 is False else "true",
        "pricing_mutation": "false" if PRICING_MUTATION_FIX_352 is False else "true",
        "plan_mutation": "false" if PLAN_MUTATION_FIX_352 is False else "true",
        "financial_forecasting_as_fact": "false"
        if FINANCIAL_FORECASTING_AS_FACT_FIX_352 is False
        else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_352 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_352 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_352 is False else "true",
        "local_economic_validation_executable": "true"
        if LOCAL_ECONOMIC_VALIDATION_EXECUTABLE_FIX_352 is True
        else "false",
        "mutation_scope": "unit_economics_business_sustainability_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "economic_validation_not_commercial_authority",
        **extra,
    }


def route_unit_economics_business_sustainability_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_business_sustainability_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_business_sustainability_intent(intent, session_id=sid)

    if handled.get("action") == "cohort":
        entry = handled.get("entry") or {}
        body = (
            f"Economic cohort customer **{entry.get('customer_id')}** registered "
            f"({entry.get('plan')} / {entry.get('segment')}). "
            "Economic validation ≠ commercial authority."
        )
        return (
            body,
            "workstream_unit_economics_business_sustainability_program_cohort",
            _meta(sid, stage="cohort"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Business sustainability note recorded ({record.get('kind', 'note')}). "
            "Validation measures signals — no billing or pricing mutation."
        )
        return (
            body,
            "workstream_unit_economics_business_sustainability_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "business_sustainability_dashboard")
    result = build_unit_economics_business_sustainability_program(session_id=sid)
    markdown = render_unit_economics_business_sustainability_program(
        result.unit_economics_business_sustainability_program,
        focus=focus,
    )
    metrics = result.unit_economics_business_sustainability_program.get("metrics") or {}
    headline = (
        f"Sustainability **{metrics.get('sustainability_score')}** · "
        f"Delivery cost **{metrics.get('delivery_cost')}** · "
        f"Retention **{metrics.get('retention_strength')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_unit_economics_business_sustainability_program",
        _meta(sid, stage="view", focus=focus),
    )
