# SPDX-License-Identifier: Apache-2.0
"""FIX 335 / EXECUTION_TRACK_2 — chat router."""

from __future__ import annotations

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    DEPLOYMENT_AUTHORITY_FIX_335,
    GIT_COMMIT_AUTHORITY_FIX_335,
    GIT_PUSH_AUTHORITY_FIX_335,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_ROUTE_ID,
    LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335,
    MERGE_AUTHORITY_FIX_335,
    MUTATION_PERFORMED_FIX_335,
    PR_CREATION_AUTHORITY_FIX_335,
    PROVIDER_MUTATION_AUTHORITY_FIX_335,
    REPOSITORY_AUTHORITY_FIX_335,
    TRUST_MUTATION_AUTHORITY_FIX_335,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_intent import (
    handle_governed_code_generation_intent,
    parse_governed_code_generation_intent,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_renderer import (
    render_governed_code_generation_changeset_creation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_service import (
    build_governed_code_generation_changeset_creation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": GOVERNED_CODE_GENERATION_CHANGESET_CREATION_ROUTE_ID,
        "matched_module": (
            "execution_tracks.governed_code_generation_changeset_creation."
            "governed_code_generation_changeset_creation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_335 is False else "true",
        "repository_authority": "false" if REPOSITORY_AUTHORITY_FIX_335 is False else "true",
        "git_commit_authority": "false" if GIT_COMMIT_AUTHORITY_FIX_335 is False else "true",
        "git_push_authority": "false" if GIT_PUSH_AUTHORITY_FIX_335 is False else "true",
        "pr_creation_authority": "false" if PR_CREATION_AUTHORITY_FIX_335 is False else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_335 is False else "true",
        "deployment_authority": "false" if DEPLOYMENT_AUTHORITY_FIX_335 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_335 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_335 is False else "true",
        "local_code_generation_executable": "true"
        if LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335 is True
        else "false",
        "mutation_scope": "governed_code_generation_changeset_creation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "code_generation_not_repository_authority",
        **extra,
    }


def route_governed_code_generation_changeset_creation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_governed_code_generation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_governed_code_generation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        generation = handled.get("generation") or {}
        body = f"Recorded generation review ({record.get('kind', 'note')}). "
        if generation.get("executed"):
            body += (
                f"Code generation executed — changeset `{generation.get('receipt', {}).get('changeset_id', '—')}`. "
            )
        body += "Code generation ≠ repository authority."
        return (
            body,
            "execution_track_governed_code_generation_record",
            _meta(
                sid,
                stage="record",
                record_kind=str(record.get("kind") or ""),
                generation_executed="true" if generation.get("executed") else "false",
            ),
        )

    focus = str(handled.get("focus") or "code_generation_dashboard")
    result = build_governed_code_generation_changeset_creation(session_id=sid)
    markdown = render_governed_code_generation_changeset_creation(
        result.governed_code_generation_changeset_creation,
        focus=focus,
    )
    dashboard = (
        (result.governed_code_generation_changeset_creation.get("sections") or {})
        .get("phase_9_dashboard", [{}])[0]
        .get("code_generation_dashboard", {})
    )
    headline = (
        f"Request **{dashboard.get('request_status', '—')}** · "
        f"Generated **{dashboard.get('generated_file_status', '—')}** · "
        f"Verification **{dashboard.get('verification_status', '—')}**. "
        "Governed implementation changes under human review — no git mutation."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "execution_track_governed_code_generation_changeset_creation",
        _meta(sid, stage="view", focus=focus),
    )
