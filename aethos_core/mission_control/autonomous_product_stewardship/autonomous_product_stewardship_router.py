# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — chat router for autonomous product stewardship."""

from __future__ import annotations

from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID,
    CROSS_REPO_EXECUTION_ENABLED_FIX_270,
    DEPLOYMENT_AUTHORITY_FIX_270,
    GATE_BYPASS_ENABLED_FIX_270,
    MERGE_AUTHORITY_FIX_270,
    MUTATION_PERFORMED_FIX_270,
    PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
    PROVIDER_MUTATION_AUTHORITY_FIX_270,
    REPOSITORY_MUTATION_AUTHORITY_FIX_270,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_intent import (
    handle_autonomous_product_stewardship_intent,
    parse_autonomous_product_stewardship_intent,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_renderer import (
    render_autonomous_product_stewardship,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_service import (
    build_autonomous_product_stewardship,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": AUTONOMOUS_PRODUCT_STEWARDSHIP_ROUTE_ID,
        "matched_module": (
            "mission_control.autonomous_product_stewardship.autonomous_product_stewardship_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_270 is False else "true",
        "product_stewardship_authority": "false"
        if PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270 is False
        else "true",
        "automatic_improvement_enabled": "false"
        if AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270 is False
        else "true",
        "cross_repo_execution_enabled": "false"
        if CROSS_REPO_EXECUTION_ENABLED_FIX_270 is False
        else "true",
        "repository_mutation_authority": "false"
        if REPOSITORY_MUTATION_AUTHORITY_FIX_270 is False
        else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_270 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_270 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_270 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_270 is False else "true",
        "mutation_scope": "autonomous_product_stewardship",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "product_stewardship_not_execution",
        **extra,
    }


def route_autonomous_product_stewardship(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_autonomous_product_stewardship_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_autonomous_product_stewardship_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded product stewardship note ({record.get('kind', 'note')}). "
            "Stewardship observes and recommends — humans approve."
        )
        return (
            body,
            "mission_control_autonomous_product_stewardship_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_autonomous_product_stewardship(session_id=sid)
    markdown = render_autonomous_product_stewardship(result.autonomous_product_stewardship)
    dashboard = (
        (result.autonomous_product_stewardship.get("sections") or {})
        .get("product_stewardship_dashboard", [{}])[0]
    )
    headline = (
        f"Product stewardship observed **{result.autonomous_product_stewardship.get('candidate_count', 0)}** "
        f"candidates. Next action: "
        f"**{(dashboard.get('recommended_next_actions') or [{}])[0].get('title', 'review stewardship backlog')}**. "
        "Stewardship ≠ execution authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_autonomous_product_stewardship",
        _meta(sid, stage="view"),
    )
