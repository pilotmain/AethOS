# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G3 / FIX 356 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_contract import (
    AUTHORITY_EXPANSION_FIX_356,
    BILLING_EXECUTION_FIX_356,
    COMMERCIAL_AUTHORITY_FIX_356,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_356,
    LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356,
    MUTATION_PERFORMED_FIX_356,
    PAYMENT_PROCESSING_FIX_356,
    PLAN_UPGRADE_FIX_356,
    PRICING_MUTATION_FIX_356,
    REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ROUTE_ID,
    SUBSCRIPTION_MUTATION_FIX_356,
    TRUST_MUTATION_AUTHORITY_FIX_356,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_intent import (
    handle_revenue_density_intent,
    parse_revenue_density_intent,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_renderer import (
    render_revenue_density_business_viability_program,
)
from aethos_core.workstreams.revenue_density_business_viability_program.revenue_density_business_viability_program_service import (
    build_revenue_density_business_viability_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REVENUE_DENSITY_BUSINESS_VIABILITY_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.revenue_density_business_viability_program."
            "revenue_density_business_viability_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_356 is False else "true",
        "commercial_authority": "false" if COMMERCIAL_AUTHORITY_FIX_356 is False else "true",
        "payment_processing": "false" if PAYMENT_PROCESSING_FIX_356 is False else "true",
        "billing_execution": "false" if BILLING_EXECUTION_FIX_356 is False else "true",
        "subscription_mutation": "false" if SUBSCRIPTION_MUTATION_FIX_356 is False else "true",
        "plan_upgrade": "false" if PLAN_UPGRADE_FIX_356 is False else "true",
        "pricing_mutation": "false" if PRICING_MUTATION_FIX_356 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_356 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_356 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_356 is False else "true",
        "local_revenue_density_executable": "true" if LOCAL_REVENUE_DENSITY_EXECUTABLE_FIX_356 is True else "false",
        "mutation_scope": "revenue_density_business_viability_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "revenue_density_not_commercial_authority",
        **extra,
    }


def route_revenue_density_business_viability_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_revenue_density_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_revenue_density_intent(intent, session_id=sid)

    if handled.get("action") == "cohort":
        entry = handled.get("entry") or {}
        body = (
            f"Revenue cohort customer **{entry.get('customer_id')}** registered "
            f"({entry.get('plan')} / {entry.get('segment')}). "
            "Revenue density ≠ commercial authority."
        )
        return (
            body,
            "workstream_revenue_density_business_viability_program_cohort",
            _meta(sid, stage="cohort"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Revenue density note recorded ({record.get('kind', 'note')}). "
            "Validation measures signals — no billing or plan mutation."
        )
        return (
            body,
            "workstream_revenue_density_business_viability_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "business_viability_dashboard")
    result = build_revenue_density_business_viability_program(session_id=sid)
    markdown = render_revenue_density_business_viability_program(
        result.revenue_density_business_viability_program,
        focus=focus,
    )
    metrics = result.revenue_density_business_viability_program.get("metrics") or {}
    headline = (
        f"Viability **{metrics.get('business_viability_score')}** · "
        f"Revenue density **{metrics.get('revenue_density_score')}** · "
        f"Expansion **{metrics.get('expansion_score')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_revenue_density_business_viability_program",
        _meta(sid, stage="view", focus=focus),
    )
