# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D1 / FIX 341 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_contract import (
    AUTHORITY_EXPANSION_FIX_341,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_341,
    LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341,
    MUTATION_PERFORMED_FIX_341,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_341,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_intent import (
    handle_phase2_provider_execution_expansion_intent,
    parse_phase2_provider_execution_expansion_intent,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_renderer import (
    render_phase2_provider_execution_expansion_program,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_service import (
    build_phase2_provider_execution_expansion_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.phase2_provider_execution_expansion_program."
            "phase2_provider_execution_expansion_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_341 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_341 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_341 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_341 is False else "true",
        "local_phase2_execution_executable": "true"
        if LOCAL_PHASE2_EXECUTION_EXECUTABLE_FIX_341 is True
        else "false",
        "mutation_scope": "phase2_provider_execution_expansion_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "provider_expansion_not_authority_expansion",
        **extra,
    }


def route_phase2_provider_execution_expansion_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_phase2_provider_execution_expansion_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_phase2_provider_execution_expansion_intent(intent, session_id=sid)

    if handled.get("action") == "deploy":
        result = handled.get("result") or {}
        body = (
            f"Phase 2 `{result.get('provider', '—')}` deployment — "
            f"**{'EXECUTED' if result.get('executed') else 'BLOCKED'}**. "
            "Provider expansion ≠ authority expansion."
        )
        return (
            body,
            "workstream_phase2_provider_execution_expansion_program_deploy",
            _meta(
                sid,
                stage="deploy",
                provider=str(result.get("provider") or ""),
                executed="true" if result.get("executed") else "false",
            ),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded Phase 2 provider review ({record.get('kind', 'note')}). "
            "Provider expansion ≠ authority expansion."
        )
        return (
            body,
            "workstream_phase2_provider_execution_expansion_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "expansion_dashboard")
    result = build_phase2_provider_execution_expansion_program(session_id=sid)
    markdown = render_phase2_provider_execution_expansion_program(
        result.phase2_provider_execution_expansion_program,
        focus=focus,
    )
    dashboard = (
        (result.phase2_provider_execution_expansion_program.get("sections") or {})
        .get("phase_8_expansion_dashboard", [{}])[0]
        .get("expansion_dashboard", {})
    )
    headline = (
        f"Phase 2 expansion **{'APPROVED' if dashboard.get('expansion_approved') else 'PENDING'}** · "
        f"Executions **{dashboard.get('execution_count', 0)}**. "
        "New providers inherit governance — no authority expansion."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_phase2_provider_execution_expansion_program",
        _meta(sid, stage="view", focus=focus),
    )
