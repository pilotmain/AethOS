# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — chat router for post-launch operations baseline."""

from __future__ import annotations

from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316,
    AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316,
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
    MUTATION_PERFORMED_FIX_316,
    POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
    POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_316,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_intent import (
    handle_post_launch_operations_baseline_intent,
    parse_post_launch_operations_baseline_intent,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_renderer import (
    render_post_launch_operations_baseline,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_service import (
    build_post_launch_operations_baseline,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID,
        "matched_module": (
            "mission_control.post_launch_operations_baseline.post_launch_operations_baseline_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_316 is False else "true",
        "post_launch_operations_authority": "false"
        if POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316 is False
        else "true",
        "automatic_operational_execution_enabled": "false"
        if AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316 is False
        else "true",
        "automatic_customer_contact_enabled": "false"
        if AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316 is False
        else "true",
        "automatic_incident_response_enabled": "false"
        if AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_316 is False else "true",
        "mutation_scope": "post_launch_operations_baseline",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "post_launch_operations_baseline_not_operational_authority",
        **extra,
    }


def route_post_launch_operations_baseline(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_post_launch_operations_baseline_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_post_launch_operations_baseline_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded operations baseline note ({record.get('kind', 'note')}). "
            "Post-launch operations baseline ≠ operational authority."
        )
        return (
            body,
            "mission_control_post_launch_operations_baseline_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "post_launch_operations_dashboard")
    result = build_post_launch_operations_baseline(session_id=sid)
    markdown = render_post_launch_operations_baseline(result.post_launch_operations_baseline, focus=focus)
    dashboard = result.post_launch_operations_baseline.get("sections", {}).get(
        "post_launch_operations_dashboard", [{}]
    )[0]
    platform_status = dashboard.get("platform_health_status", "—")
    customer_status = dashboard.get("customer_health_status", "—")
    headline = (
        f"Post-launch operations baseline — platform **{platform_status}**, "
        f"customers **{customer_status}**. Observation only, no operational execution."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_post_launch_operations_baseline",
        _meta(
            sid,
            stage="view",
            focus=focus,
            platform_health=str(platform_status),
            customer_health=str(customer_status),
        ),
    )
