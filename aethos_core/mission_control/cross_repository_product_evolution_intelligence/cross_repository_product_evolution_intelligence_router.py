# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — chat router for cross-repository product evolution intelligence."""

from __future__ import annotations

from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
    CROSS_REPO_EXECUTION_ENABLED_FIX_261,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID,
    DEPLOY_AUTHORITY_FIX_261,
    GATE_BYPASS_ENABLED_FIX_261,
    MERGE_AUTHORITY_FIX_261,
    MUTATION_PERFORMED_FIX_261,
    PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
    PROVIDER_MUTATION_AUTHORITY_FIX_261,
    REPOSITORY_MUTATION_AUTHORITY_FIX_261,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_intent import (
    handle_cross_repository_product_evolution_intelligence_intent,
    parse_cross_repository_product_evolution_intelligence_intent,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_renderer import (
    render_cross_repository_product_evolution_intelligence,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
    build_cross_repository_product_evolution_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.cross_repository_product_evolution_intelligence."
            "cross_repository_product_evolution_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_261 is False else "true",
        "product_evolution_authority": "false"
        if PRODUCT_EVOLUTION_AUTHORITY_FIX_261 is False
        else "true",
        "automatic_improvement_enabled": "false"
        if AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261 is False
        else "true",
        "cross_repo_execution_enabled": "false"
        if CROSS_REPO_EXECUTION_ENABLED_FIX_261 is False
        else "true",
        "repository_mutation_authority": "false"
        if REPOSITORY_MUTATION_AUTHORITY_FIX_261 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_261 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_261 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_261 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_261 is False else "true",
        "mutation_scope": "cross_repository_product_evolution_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "product_evolution_not_execution",
        **extra,
    }


def route_cross_repository_product_evolution_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_cross_repository_product_evolution_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_cross_repository_product_evolution_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded cross-repository product evolution note ({record.get('kind', 'note')}). "
            "Evolution intelligence identifies opportunities — humans decide."
        )
        return (
            body,
            "mission_control_cross_repository_product_evolution_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_cross_repository_product_evolution_intelligence(session_id=sid)
    markdown = render_cross_repository_product_evolution_intelligence(
        result.cross_repository_product_evolution_intelligence
    )
    dashboard = (
        (result.cross_repository_product_evolution_intelligence.get("sections") or {})
        .get("product_evolution_dashboard", [{}])[0]
    )
    headline = (
        f"Portfolio evolution intelligence identified **{result.cross_repository_product_evolution_intelligence.get('opportunity_count', 0)}** "
        f"opportunities. Top priority: "
        f"**{(dashboard.get('top_opportunities') or [{}])[0].get('title', 'review backlog')}**. "
        "Evolution intelligence ≠ execution authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_cross_repository_product_evolution_intelligence",
        _meta(sid, stage="view"),
    )
