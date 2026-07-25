# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F7 / FIX 353 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_contract import (
    AUTHORITY_EXPANSION_FIX_353,
    BUSINESS_AUTOMATION_FIX_353,
    BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ROUTE_ID,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_353,
    GOVERNANCE_MUTATION_FIX_353,
    LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353,
    MUTATION_PERFORMED_FIX_353,
    OPERATING_AUTHORITY_FIX_353,
    ORGANIZATIONAL_RESTRUCTURING_FIX_353,
    PRICING_MUTATION_FIX_353,
    PROVIDER_MUTATION_FIX_353,
    TRUST_MUTATION_AUTHORITY_FIX_353,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_intent import (
    handle_operating_model_intent,
    parse_operating_model_intent,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_renderer import (
    render_business_operating_model_validation_program,
)
from aethos_core.workstreams.business_operating_model_validation_program.business_operating_model_validation_program_service import (
    build_business_operating_model_validation_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": BUSINESS_OPERATING_MODEL_VALIDATION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.business_operating_model_validation_program."
            "business_operating_model_validation_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_353 is False else "true",
        "operating_authority": "false" if OPERATING_AUTHORITY_FIX_353 is False else "true",
        "governance_mutation": "false" if GOVERNANCE_MUTATION_FIX_353 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_353 is False else "true",
        "pricing_mutation": "false" if PRICING_MUTATION_FIX_353 is False else "true",
        "provider_mutation": "false" if PROVIDER_MUTATION_FIX_353 is False else "true",
        "organizational_restructuring": "false"
        if ORGANIZATIONAL_RESTRUCTURING_FIX_353 is False
        else "true",
        "business_automation": "false" if BUSINESS_AUTOMATION_FIX_353 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_353 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_353 is False else "true",
        "local_operating_model_validation_executable": "true"
        if LOCAL_OPERATING_MODEL_VALIDATION_EXECUTABLE_FIX_353 is True
        else "false",
        "mutation_scope": "business_operating_model_validation_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "operating_model_validation_not_operating_authority",
        **extra,
    }


def route_business_operating_model_validation_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_operating_model_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_operating_model_intent(intent, session_id=sid)

    if handled.get("action") == "cohort":
        entry = handled.get("entry") or {}
        body = (
            f"Operating model cohort customer **{entry.get('customer_id')}** registered "
            f"({entry.get('provider')} / {entry.get('support_profile')}). "
            "Operating model validation ≠ operating authority."
        )
        return (
            body,
            "workstream_business_operating_model_validation_program_cohort",
            _meta(sid, stage="cohort"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Operating model note recorded ({record.get('kind', 'note')}). "
            "Validation measures sustainability — no governance or provider mutation."
        )
        return (
            body,
            "workstream_business_operating_model_validation_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "operating_model_dashboard")
    result = build_business_operating_model_validation_program(session_id=sid)
    markdown = render_business_operating_model_validation_program(
        result.business_operating_model_validation_program,
        focus=focus,
    )
    metrics = result.business_operating_model_validation_program.get("metrics") or {}
    headline = (
        f"Leverage **{metrics.get('operating_leverage_score')}** · "
        f"Sustainability **{metrics.get('business_sustainability_score')}** · "
        f"Delivery **{metrics.get('delivery_efficiency')}**."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_business_operating_model_validation_program",
        _meta(sid, stage="view", focus=focus),
    )
