# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — software delivery issue plan router."""

from __future__ import annotations

from aethos_core.software_delivery.issue_plan_contract import SOFTWARE_DELIVERY_LANE_ID
from aethos_core.software_delivery.issue_plan_renderer import (
    render_implementation_scope,
    render_issue_plan_summary,
    render_risk_assessment,
)
from aethos_core.software_delivery.issue_plan_service import (
    analyze_github_issue,
    approve_implementation_planning,
    create_implementation_plan,
    extract_planning_approval,
    is_software_delivery_issue_plan_intent,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": SOFTWARE_DELIVERY_LANE_ID,
        "matched_module": "software_delivery.issue_plan_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "software_delivery_stage": stage,
        "lane_separation": "software_delivery_not_infra",
        **extra,
    }


def route_software_delivery_issue_plan(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_software_delivery_issue_plan_intent(raw):
        return None

    if "analyze" in raw.lower() and "github issue" in raw.lower():
        result = analyze_github_issue(session_id=session_id, user_text=raw)
        body = render_issue_plan_summary(result.plan) if result.plan else result.detail
        intent = (
            "software_delivery_issue_analyzed"
            if result.ok
            else "software_delivery_issue_plan_blocked"
        )
        return body, intent, _meta(
            session_id,
            stage="analyze",
            plan_id=str((result.plan or {}).get("plan_id") or ""),
        )

    if extract_planning_approval(raw) or (
        "approve" in raw.lower() and "planning" in raw.lower()
    ):
        result = approve_implementation_planning(session_id=session_id, user_text=raw)
        body = render_issue_plan_summary(result.plan) if result.plan else result.detail
        intent = (
            "software_delivery_planning_approved"
            if result.ok
            else "software_delivery_issue_plan_blocked"
        )
        return body, intent, _meta(session_id, stage="approve")

    if "create" in raw.lower() and "implementation plan" in raw.lower():
        result = create_implementation_plan(session_id=session_id)
        body = render_issue_plan_summary(result.plan) if result.plan else result.detail
        intent = (
            "software_delivery_plan_created"
            if result.ok
            else "software_delivery_issue_plan_blocked"
        )
        return body, intent, _meta(session_id, stage="create_plan")

    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        body = (
            "No software delivery issue plan for this session. "
            "Run `analyze github issue owner/repo#N` first."
        )
        return body, "software_delivery_issue_plan_blocked", _meta(session_id, stage="blocked")

    if "scope" in raw.lower():
        body = render_implementation_scope(plan)
        return body, "software_delivery_implementation_scope", _meta(session_id, stage="scope")

    if "risk" in raw.lower():
        body = render_risk_assessment(plan)
        return body, "software_delivery_risk_assessment", _meta(session_id, stage="risk")

    body = render_issue_plan_summary(plan)
    return body, "software_delivery_issue_plan", _meta(session_id, stage="summary")
