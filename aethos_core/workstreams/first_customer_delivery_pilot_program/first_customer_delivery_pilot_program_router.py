# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 / FIX 347 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    AUTHORITY_EXPANSION_FIX_347,
    CUSTOMER_AUTHORITY_FIX_347,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_347,
    LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347,
    MUTATION_PERFORMED_FIX_347,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_347,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_intent import (
    handle_first_customer_delivery_pilot_intent,
    parse_first_customer_delivery_pilot_intent,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_renderer import (
    render_first_customer_delivery_pilot_program,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_service import (
    build_first_customer_delivery_pilot_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_347 is False else "true",
        "customer_authority": "false" if CUSTOMER_AUTHORITY_FIX_347 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_347 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_347 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_347 is False else "true",
        "local_customer_pilot_executable": "true"
        if LOCAL_CUSTOMER_PILOT_EXECUTABLE_FIX_347 is True
        else "false",
        "mutation_scope": "first_customer_delivery_pilot_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "customer_pilot_not_customer_authority",
        **extra,
    }


def route_first_customer_delivery_pilot_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_first_customer_delivery_pilot_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_first_customer_delivery_pilot_intent(intent, session_id=sid)

    if handled.get("action") == "run":
        result = handled.get("result") or {}
        if result.get("error") == "customer_delivery_request_required":
            body = (
                "Customer delivery request required before running the pilot. "
                "Use `customer delivery request: goal=..., scope=..., type=health_check_endpoint`. "
                "Customer delivery pilot ≠ customer authority."
            )
        else:
            body = (
                f"Customer delivery pilot — **{'PASSED' if result.get('passed') else 'FAILED'}** "
                f"({result.get('duration_ms', 0)}ms). "
                "Pilot executes within approved bounds — no customer authority granted."
            )
        return (
            body,
            "workstream_first_customer_delivery_pilot_program_run",
            _meta(
                sid,
                stage="run",
                pilot_passed="true" if result.get("passed") else "false",
            ),
        )

    if handled.get("action") == "intake":
        request = (handled.get("result") or {}).get("request") or {}
        body = (
            f"Customer delivery request recorded — **{request.get('request_label', request.get('request_type'))}**. "
            "Scope bounded; humans approve delivery, deployment, and acceptance."
        )
        return (
            body,
            "workstream_first_customer_delivery_pilot_program_intake",
            _meta(sid, stage="intake"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Customer pilot note recorded ({record.get('kind', 'note')}). "
            "Customer delivery pilot ≠ customer authority."
        )
        return (
            body,
            "workstream_first_customer_delivery_pilot_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_delivery_pilot_dashboard")
    result = build_first_customer_delivery_pilot_program(session_id=sid)
    markdown = render_first_customer_delivery_pilot_program(
        result.first_customer_delivery_pilot_program,
        focus=focus,
    )
    metrics = result.first_customer_delivery_pilot_program.get("metrics") or {}
    headline = (
        f"Verification **{metrics.get('verification_outcome', 'PENDING')}** · "
        f"Value realized **{metrics.get('value_realized', False)}** · "
        "Humans approve scope, delivery, deployment, and acceptance."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_first_customer_delivery_pilot_program",
        _meta(sid, stage="view", focus=focus),
    )
