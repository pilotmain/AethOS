# SPDX-License-Identifier: Apache-2.0
"""FIX 337 / EXECUTION_TRACK_4 — chat router."""

from __future__ import annotations

from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_contract import (
    AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337,
    DEPLOYMENT_AUTHORITY_FIX_337,
    GOVERNED_DEPLOYMENT_EXECUTION_ROUTE_ID,
    LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337,
    MUTATION_PERFORMED_FIX_337,
    PRODUCTION_PROMOTION_AUTHORITY_FIX_337,
    ROLLBACK_AUTHORITY_FIX_337,
    TRUST_MUTATION_AUTHORITY_FIX_337,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_intent import (
    handle_governed_deployment_execution_intent,
    parse_governed_deployment_execution_intent,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_renderer import (
    render_governed_deployment_execution,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_service import (
    build_governed_deployment_execution,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_DEPLOYMENT_EXECUTION_ROUTE_ID,
        "matched_module": "execution_tracks.governed_deployment_execution.governed_deployment_execution_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_337 is False else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_337 is False else "true",
        "autonomous_deployment_enabled": "false"
        if AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337 is False
        else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_337 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_337 is False else "true",
        "production_promotion_authority": "false"
        if PRODUCTION_PROMOTION_AUTHORITY_FIX_337 is False
        else "true",
        "local_deployment_execution_executable": "true"
        if LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337 is True
        else "false",
        "mutation_scope": "governed_deployment_execution",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "deployment_execution_not_deployment_authority",
        **extra,
    }


def route_governed_deployment_execution(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_governed_deployment_execution_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_governed_deployment_execution_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        deployment = handled.get("deployment") or {}
        body = f"Recorded deployment review ({record.get('kind', 'note')}). "
        if deployment.get("executed"):
            body += (
                f"Deployment executed — `{deployment.get('receipt', {}).get('deployment_url', '—')}`. "
            )
        body += "Deployment execution ≠ deployment authority."
        return (
            body,
            "execution_track_governed_deployment_execution_record",
            _meta(
                sid,
                stage="record",
                record_kind=str(record.get("kind") or ""),
                deployment_executed="true" if deployment.get("executed") else "false",
            ),
        )

    focus = str(handled.get("focus") or "deployment_execution_dashboard")
    result = build_governed_deployment_execution(session_id=sid)
    markdown = render_governed_deployment_execution(result.governed_deployment_execution, focus=focus)
    dashboard = (
        (result.governed_deployment_execution.get("sections") or {})
        .get("phase_8_deployment_dashboard", [{}])[0]
        .get("deployment_execution_dashboard", {})
    )
    headline = (
        f"Deployment **{dashboard.get('deployment_status', '—')}** · "
        f"Verification **{dashboard.get('verification_status', '—')}** · "
        f"Provider **{dashboard.get('provider', '—')}**. "
        "Governed deployment under human review — no rollback authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "execution_track_governed_deployment_execution",
        _meta(sid, stage="view", focus=focus),
    )
