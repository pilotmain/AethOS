# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E1 / FIX 343 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    AUTHORITY_EXPANSION_FIX_343,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_343,
    LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343,
    INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ROUTE_ID,
    MUTATION_PERFORMED_FIX_343,
    TRUST_MUTATION_AUTHORITY_FIX_343,
    TRUTH_REDUCTION_FIX_343,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_intent import (
    handle_intelligence_performance_evidence_scalability_intent,
    parse_intelligence_performance_evidence_scalability_intent,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_renderer import (
    render_intelligence_performance_evidence_scalability_program,
)
from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_service import (
    build_intelligence_performance_evidence_scalability_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INTELLIGENCE_PERFORMANCE_EVIDENCE_SCALABILITY_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.intelligence_performance_evidence_scalability_program."
            "intelligence_performance_evidence_scalability_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_343 is False else "true",
        "truth_reduction": "false" if TRUTH_REDUCTION_FIX_343 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_343 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_343 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_343 is False else "true",
        "local_performance_analysis_executable": "true"
        if LOCAL_PERFORMANCE_ANALYSIS_EXECUTABLE_FIX_343 is True
        else "false",
        "mutation_scope": "intelligence_performance_evidence_scalability_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "performance_optimization_not_truth_reduction",
        **extra,
    }


def route_intelligence_performance_evidence_scalability_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_intelligence_performance_evidence_scalability_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_intelligence_performance_evidence_scalability_intent(intent, session_id=sid)

    if handled.get("action") == "analyze":
        analysis = handled.get("analysis") or {}
        hotspots = analysis.get("compose_hotspot_registry") or {}
        body = (
            f"Intelligence performance analysis complete — **{hotspots.get('hotspot_count', 0)}** hotspots, "
            f"slowest **{hotspots.get('slowest_module', '—')}**. "
            "Performance optimization ≠ truth reduction."
        )
        return (
            body,
            "workstream_intelligence_performance_evidence_scalability_program_analyze",
            _meta(sid, stage="analyze"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded performance note ({record.get('kind', 'note')}). "
            "Optimization preserves evidence integrity — no truth reduction."
        )
        return (
            body,
            "workstream_intelligence_performance_evidence_scalability_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "intelligence_performance_dashboard")
    result = build_intelligence_performance_evidence_scalability_program(session_id=sid)
    markdown = render_intelligence_performance_evidence_scalability_program(
        result.intelligence_performance_evidence_scalability_program,
        focus=focus,
    )
    trends = result.intelligence_performance_evidence_scalability_program.get("latency_trends") or {}
    headline = (
        f"Total compose **{trends.get('total_compose_duration_sec', 0)}s** · "
        f"Slowest **{trends.get('slowest_module', '—')}** · "
        f"Scalability risk **{trends.get('scalability_risk')}**. "
        "Evidence integrity preserved."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_intelligence_performance_evidence_scalability_program",
        _meta(sid, stage="view", focus=focus),
    )
