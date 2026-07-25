# SPDX-License-Identifier: Apache-2.0
"""FIX 334 / EXECUTION_TRACK_1 — chat router."""

from __future__ import annotations

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_contract import (
    CLOUD_PROVISIONING_AUTHORITY_FIX_334,
    CODE_GENERATION_AUTHORITY_FIX_334,
    DEPLOYMENT_AUTHORITY_FIX_334,
    GIT_PUSH_AUTHORITY_FIX_334,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_ROUTE_ID,
    LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334,
    MUTATION_PERFORMED_FIX_334,
    PR_CREATION_AUTHORITY_FIX_334,
    PROVIDER_MUTATION_AUTHORITY_FIX_334,
    TRUST_MUTATION_AUTHORITY_FIX_334,
    WORKSPACE_CREATION_AUTHORITY_FIX_334,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_intent import (
    handle_governed_workspace_creation_intent,
    parse_governed_workspace_creation_intent,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_renderer import (
    render_governed_workspace_creation_repository_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_service import (
    build_governed_workspace_creation_repository_bootstrap,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_ROUTE_ID,
        "matched_module": (
            "execution_tracks.governed_workspace_creation_repository_bootstrap."
            "governed_workspace_creation_repository_bootstrap_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_334 is False else "true",
        "workspace_creation_authority": "false"
        if WORKSPACE_CREATION_AUTHORITY_FIX_334 is False
        else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_334 is False else "true",
        "git_push_authority": "false" if GIT_PUSH_AUTHORITY_FIX_334 is False else "true",
        "pr_creation_authority": "false" if PR_CREATION_AUTHORITY_FIX_334 is False else "true",
        "cloud_provisioning_authority": "false"
        if CLOUD_PROVISIONING_AUTHORITY_FIX_334 is False
        else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_334 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_334 is False else "true",
        "code_generation_authority": "false"
        if CODE_GENERATION_AUTHORITY_FIX_334 is False
        else "true",
        "local_bootstrap_executable": "true"
        if LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334 is True
        else "false",
        "mutation_scope": "governed_workspace_creation_repository_bootstrap",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "workspace_creation_not_deployment_authority",
        **extra,
    }


def route_governed_workspace_creation_repository_bootstrap(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_governed_workspace_creation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_governed_workspace_creation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        bootstrap = handled.get("bootstrap") or {}
        body = f"Recorded workspace review ({record.get('kind', 'note')}). "
        if bootstrap.get("executed"):
            body += (
                f"Repository bootstrap executed at `{bootstrap.get('receipt', {}).get('workspace_path', '—')}`. "
            )
        body += "Workspace creation ≠ deployment authority."
        return (
            body,
            "execution_track_governed_workspace_creation_record",
            _meta(
                sid,
                stage="record",
                record_kind=str(record.get("kind") or ""),
                bootstrap_executed="true" if bootstrap.get("executed") else "false",
            ),
        )

    focus = str(handled.get("focus") or "workspace_creation_dashboard")
    result = build_governed_workspace_creation_repository_bootstrap(session_id=sid)
    markdown = render_governed_workspace_creation_repository_bootstrap(
        result.governed_workspace_creation_repository_bootstrap,
        focus=focus,
    )
    dashboard = (
        (result.governed_workspace_creation_repository_bootstrap.get("sections") or {})
        .get("phase_6_workspace_dashboard", [{}])[0]
        .get("workspace_creation_dashboard", {})
    )
    headline = (
        f"Workspace status **{dashboard.get('workspace_status', '—')}** · "
        f"Repository **{dashboard.get('repository_status', '—')}** · "
        f"Verification **{dashboard.get('verification_status', '—')}**. "
        "Governed repository preparation under human review — no deployment authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "execution_track_governed_workspace_creation_repository_bootstrap",
        _meta(sid, stage="view", focus=focus),
    )
