# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — chat router for multi-repository engineering intelligence."""

from __future__ import annotations

from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
    CROSS_REPO_AUTHORITY_FIX_260,
    DEPLOY_AUTHORITY_FIX_260,
    GATE_BYPASS_ENABLED_FIX_260,
    MERGE_AUTHORITY_FIX_260,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_260,
    PORTFOLIO_AUTHORITY_FIX_260,
    PROGRAM_DELIVERY_AUTHORITY_FIX_260,
    PROVIDER_MUTATION_AUTHORITY_FIX_260,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_intent import (
    handle_multi_repository_engineering_intelligence_intent,
    parse_multi_repository_engineering_intelligence_intent,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_renderer import (
    render_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.multi_repository_engineering_intelligence."
            "multi_repository_engineering_intelligence_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_260 is False else "true",
        "portfolio_authority": "false" if PORTFOLIO_AUTHORITY_FIX_260 is False else "true",
        "cross_repo_authority": "false" if CROSS_REPO_AUTHORITY_FIX_260 is False else "true",
        "program_delivery_authority": "false"
        if PROGRAM_DELIVERY_AUTHORITY_FIX_260 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_260 is False else "true",
        "deploy_authority": "false" if DEPLOY_AUTHORITY_FIX_260 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_260 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_260 is False else "true",
        "mutation_scope": "multi_repository_engineering_intelligence",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "portfolio_intelligence_not_authority",
        **extra,
    }


def route_multi_repository_engineering_intelligence(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_multi_repository_engineering_intelligence_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_multi_repository_engineering_intelligence_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = f"Recorded multi-repository engineering intelligence note ({record.get('kind', 'note')})."
        return (
            body,
            "mission_control_multi_repository_engineering_intelligence_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_multi_repository_engineering_intelligence(session_id=sid)
    markdown = render_multi_repository_engineering_intelligence(
        result.multi_repository_engineering_intelligence
    )
    summary = dict(
        (result.multi_repository_engineering_intelligence.get("sections") or {})
        .get("portfolio_engineering_dashboard", [{}])[0]
        .get("portfolio_summary", {})
    )
    headline = (
        f"Portfolio engineering health **{summary.get('portfolio_engineering_health_score', '—')}** "
        f"({summary.get('portfolio_health_tier', '—')}). "
        f"Cross-repo intelligence is advisory — trust remains independent per repository."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_multi_repository_engineering_intelligence",
        _meta(sid, stage="view"),
    )
