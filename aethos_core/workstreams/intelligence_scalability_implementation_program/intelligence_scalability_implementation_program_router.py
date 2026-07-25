# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 / FIX 345 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    AUTHORITY_EXPANSION_FIX_345,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_345,
    INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ROUTE_ID,
    LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345,
    MUTATION_PERFORMED_FIX_345,
    TRUST_MUTATION_AUTHORITY_FIX_345,
    TRUTH_MUTATION_FIX_345,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_intent import (
    handle_intelligence_scalability_implementation_intent,
    parse_intelligence_scalability_implementation_intent,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_renderer import (
    render_intelligence_scalability_implementation_program,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_service import (
    build_intelligence_scalability_implementation_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INTELLIGENCE_SCALABILITY_IMPLEMENTATION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.intelligence_scalability_implementation_program."
            "intelligence_scalability_implementation_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_345 is False else "true",
        "truth_mutation": "false" if TRUTH_MUTATION_FIX_345 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_345 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_345 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_345 is False else "true",
        "local_scalability_implementation_executable": "true"
        if LOCAL_SCALABILITY_IMPLEMENTATION_EXECUTABLE_FIX_345 is True
        else "false",
        "mutation_scope": "intelligence_scalability_implementation_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "optimization_execution_not_truth_mutation",
        **extra,
    }


def route_intelligence_scalability_implementation_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_intelligence_scalability_implementation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_intelligence_scalability_implementation_intent(intent, session_id=sid)

    if handled.get("action") == "execute":
        result = handled.get("result") or {}
        benchmark = result.get("runtime_benchmark_report") or {}
        body = (
            f"Scalability implementation executed — reduction **{benchmark.get('compose_duration_reduction_pct', 0)}**, "
            f"flattened **{result.get('dependency_flattening_execution_report', {}).get('flattened')}**. "
            "Optimization execution ≠ truth mutation."
        )
        return (
            body,
            "workstream_intelligence_scalability_implementation_program_execute",
            _meta(sid, stage="execute"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded scalability note ({record.get('kind', 'note')}). "
            "Runtime improvements preserve evidence integrity."
        )
        return (
            body,
            "workstream_intelligence_scalability_implementation_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "intelligence_scalability_dashboard")
    result = build_intelligence_scalability_implementation_program(session_id=sid)
    markdown = render_intelligence_scalability_implementation_program(
        result.intelligence_scalability_implementation_program,
        focus=focus,
    )
    benchmark = result.intelligence_scalability_implementation_program.get("runtime_benchmark") or {}
    headline = (
        f"Compose reduction **{benchmark.get('compose_duration_reduction_pct', 0)}** · "
        f"Truth mutation **{result.intelligence_scalability_implementation_program.get('truth_mutation')}**. "
        "Evidence integrity preserved."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_intelligence_scalability_implementation_program",
        _meta(sid, stage="view", focus=focus),
    )
