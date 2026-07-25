# SPDX-License-Identifier: Apache-2.0
"""FIX 336 / EXECUTION_TRACK_3 — chat router."""

from __future__ import annotations

from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_contract import (
    DEPLOYMENT_AUTHORITY_FIX_336,
    GIT_DELIVERY_AUTHORITY_FIX_336,
    GOVERNED_GIT_DELIVERY_ROUTE_ID,
    LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336,
    MERGE_AUTHORITY_FIX_336,
    MUTATION_PERFORMED_FIX_336,
    ROLLBACK_AUTHORITY_FIX_336,
    TRUST_MUTATION_AUTHORITY_FIX_336,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_intent import (
    handle_governed_git_delivery_intent,
    parse_governed_git_delivery_intent,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_renderer import (
    render_governed_git_delivery,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_service import (
    build_governed_git_delivery,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_GIT_DELIVERY_ROUTE_ID,
        "matched_module": "execution_tracks.governed_git_delivery.governed_git_delivery_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_336 is False else "true",
        "git_delivery_authority": "false" if GIT_DELIVERY_AUTHORITY_FIX_336 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_336 is False else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_336 is False else "true",
        "rollback_authority": "false" if ROLLBACK_AUTHORITY_FIX_336 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_336 is False else "true",
        "local_git_delivery_executable": "true"
        if LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336 is True
        else "false",
        "mutation_scope": "governed_git_delivery",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "git_delivery_not_merge_authority",
        **extra,
    }


def route_governed_git_delivery(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_governed_git_delivery_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_governed_git_delivery_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        delivery = handled.get("delivery") or {}
        body = f"Recorded Git delivery review ({record.get('kind', 'note')}). "
        if delivery.get("executed"):
            body += (
                f"Git delivery executed on branch `{delivery.get('receipt', {}).get('branch_name', '—')}`. "
            )
        body += "Git delivery ≠ merge authority."
        return (
            body,
            "execution_track_governed_git_delivery_record",
            _meta(
                sid,
                stage="record",
                record_kind=str(record.get("kind") or ""),
                delivery_executed="true" if delivery.get("executed") else "false",
            ),
        )

    focus = str(handled.get("focus") or "git_delivery_dashboard")
    result = build_governed_git_delivery(session_id=sid)
    markdown = render_governed_git_delivery(result.governed_git_delivery, focus=focus)
    dashboard = (
        (result.governed_git_delivery.get("sections") or {})
        .get("phase_9_delivery_dashboard", [{}])[0]
        .get("git_delivery_dashboard", {})
    )
    headline = (
        f"Branch **{dashboard.get('branch_status', '—')}** · "
        f"Commit **{dashboard.get('commit_status', '—')}** · "
        f"PR **{dashboard.get('pull_request_status', '—')}** · "
        f"Verification **{dashboard.get('verification_status', '—')}**. "
        "Governed Git delivery under human review — no merge authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "execution_track_governed_git_delivery",
        _meta(sid, stage="view", focus=focus),
    )
