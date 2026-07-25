# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 / FIX 342 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_342,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_342,
    LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342,
    MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ROUTE_ID,
    MUTATION_PERFORMED_FIX_342,
    PROVIDER_AUTHORITY_FIX_342,
    TRUST_MUTATION_AUTHORITY_FIX_342,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_intent import (
    handle_multi_cloud_operational_proof_intent,
    parse_multi_cloud_operational_proof_intent,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_renderer import (
    render_multi_cloud_operational_proof_program,
)
from aethos_core.workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_service import (
    build_multi_cloud_operational_proof_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MULTI_CLOUD_OPERATIONAL_PROOF_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.multi_cloud_operational_proof_program.multi_cloud_operational_proof_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_342 is False else "true",
        "provider_authority": "false" if PROVIDER_AUTHORITY_FIX_342 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_342 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_342 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_342 is False else "true",
        "local_multi_cloud_proof_executable": "true"
        if LOCAL_MULTI_CLOUD_PROOF_EXECUTABLE_FIX_342 is True
        else "false",
        "mutation_scope": "multi_cloud_operational_proof_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "multi_cloud_proof_not_provider_authority",
        **extra,
    }


def route_multi_cloud_operational_proof_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_multi_cloud_operational_proof_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_multi_cloud_operational_proof_intent(intent, session_id=sid)

    if handled.get("action") == "run":
        result = handled.get("result") or {}
        body = (
            f"Provider proof `{result.get('provider', '—')}` — "
            f"**{'PASSED' if result.get('passed') else 'FAILED'}**. "
            "Multi-cloud proof ≠ provider authority."
        )
        return (
            body,
            "workstream_multi_cloud_operational_proof_program_run",
            _meta(sid, stage="run", provider=str(result.get("provider") or "")),
        )

    if handled.get("action") == "run_wave":
        result = handled.get("result") or {}
        body = (
            f"Wave 1 provider proof — **{result.get('passed_count', 0)}/{result.get('total', 0)}** passed. "
            "Multi-cloud proof ≠ provider authority."
        )
        return (
            body,
            "workstream_multi_cloud_operational_proof_program_run_wave",
            _meta(sid, stage="run_wave"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded provider proof note ({record.get('kind', 'note')}). "
            "Evidence collection does not grant authority."
        )
        return (
            body,
            "workstream_multi_cloud_operational_proof_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "multi_cloud_dashboard")
    result = build_multi_cloud_operational_proof_program(session_id=sid)
    markdown = render_multi_cloud_operational_proof_program(
        result.multi_cloud_operational_proof_program,
        focus=focus,
    )
    scorecard = (
        (result.multi_cloud_operational_proof_program.get("sections") or {})
        .get("phase_7_comparative_analysis", [{}])[0]
        .get("provider_maturity_scorecard", {})
    )
    headline = (
        f"Wave 1 proven: **{scorecard.get('wave_1_multi_cloud_proven', False)}** · "
        f"Providers tracked: **{len(result.multi_cloud_operational_proof_program.get('all_proof_providers') or [])}**. "
        "Governance unchanged — proof does not grant authority."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_multi_cloud_operational_proof_program",
        _meta(sid, stage="view", focus=focus),
    )
