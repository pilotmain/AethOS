# SPDX-License-Identifier: Apache-2.0
"""FIX 338 / EXECUTION_TRACK_5 — chat router."""

from __future__ import annotations

from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    APPROVAL_BYPASS_AUTHORITY_FIX_338,
    AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338,
    DELIVERY_AUTHORITY_FIX_338,
    DEPLOYMENT_BYPASS_AUTHORITY_FIX_338,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_ROUTE_ID,
    LOCAL_CERTIFICATION_EXECUTABLE_FIX_338,
    MUTATION_PERFORMED_FIX_338,
    TRUST_MUTATION_AUTHORITY_FIX_338,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_intent import (
    handle_governed_end_to_end_delivery_certification_intent,
    parse_governed_end_to_end_delivery_certification_intent,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_renderer import (
    render_governed_end_to_end_delivery_certification,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_service import (
    build_governed_end_to_end_delivery_certification,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_ROUTE_ID,
        "matched_module": (
            "execution_tracks.governed_end_to_end_delivery_certification."
            "governed_end_to_end_delivery_certification_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_338 is False else "true",
        "delivery_authority": "false" if DELIVERY_AUTHORITY_FIX_338 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_338 is False else "true",
        "automatic_certification_promotion": "false"
        if AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338 is False
        else "true",
        "approval_bypass_authority": "false" if APPROVAL_BYPASS_AUTHORITY_FIX_338 is False else "true",
        "deployment_bypass_authority": "false" if DEPLOYMENT_BYPASS_AUTHORITY_FIX_338 is False else "true",
        "local_certification_executable": "true"
        if LOCAL_CERTIFICATION_EXECUTABLE_FIX_338 is True
        else "false",
        "mutation_scope": "governed_end_to_end_delivery_certification",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "delivery_certification_not_delivery_authority",
        **extra,
    }


def route_governed_end_to_end_delivery_certification(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_governed_end_to_end_delivery_certification_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_governed_end_to_end_delivery_certification_intent(intent, session_id=sid)

    if handled.get("action") == "run":
        run = handled.get("run") or {}
        body = (
            f"Certification run `{handled.get('scenario_id', '—')}` — "
            f"**{'PASSED' if run.get('passed') else 'FAILED'}** "
            f"({run.get('duration_ms', 0)}ms). "
            "Delivery certification ≠ delivery authority."
        )
        return (
            body,
            "execution_track_governed_end_to_end_delivery_certification_run",
            _meta(
                sid,
                stage="run",
                scenario_id=str(handled.get("scenario_id") or ""),
                run_passed="true" if run.get("passed") else "false",
            ),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded certification review ({record.get('kind', 'note')}). "
            "Delivery certification ≠ delivery authority."
        )
        return (
            body,
            "execution_track_governed_end_to_end_delivery_certification_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "delivery_certification_dashboard")
    result = build_governed_end_to_end_delivery_certification(session_id=sid)
    markdown = render_governed_end_to_end_delivery_certification(
        result.governed_end_to_end_delivery_certification,
        focus=focus,
    )
    dashboard = (
        (result.governed_end_to_end_delivery_certification.get("sections") or {})
        .get("phase_8_certification_dashboard", [{}])[0]
        .get("delivery_certification_dashboard", {})
    )
    headline = (
        f"Certification **{dashboard.get('certification_status', '—')}** · "
        f"Runs **{dashboard.get('run_count', 0)}** · "
        f"Pass rate **{dashboard.get('pass_rate', 0.0)}**. "
        "Certification measures quality — no delivery authority granted."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "execution_track_governed_end_to_end_delivery_certification",
        _meta(sid, stage="view", focus=focus),
    )
