# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 / FIX 344 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    AUTHORITY_EXPANSION_FIX_344,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_344,
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ROUTE_ID,
    LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344,
    MUTATION_PERFORMED_FIX_344,
    TRUST_MUTATION_AUTHORITY_FIX_344,
    TRUTH_REDUCTION_FIX_344,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_intent import (
    handle_intelligence_runtime_optimization_intent,
    parse_intelligence_runtime_optimization_intent,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_renderer import (
    render_intelligence_runtime_optimization_program,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_service import (
    build_intelligence_runtime_optimization_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ROUTE_ID,
        "matched_module": (
            "workstreams.intelligence_runtime_optimization_program."
            "intelligence_runtime_optimization_program_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_344 is False else "true",
        "truth_reduction": "false" if TRUTH_REDUCTION_FIX_344 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_344 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_344 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_344 is False else "true",
        "local_runtime_optimization_executable": "true"
        if LOCAL_RUNTIME_OPTIMIZATION_EXECUTABLE_FIX_344 is True
        else "false",
        "mutation_scope": "intelligence_runtime_optimization_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "runtime_optimization_not_truth_reduction",
        **extra,
    }


def route_intelligence_runtime_optimization_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_intelligence_runtime_optimization_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_intelligence_runtime_optimization_intent(intent, session_id=sid)

    if handled.get("action") == "analyze":
        analysis = handled.get("analysis") or {}
        metrics = analysis.get("runtime_metrics") or {}
        body = (
            f"Runtime optimization analysis complete — projected reduction **{metrics.get('compose_duration_reduction', 0)}**, "
            f"cache hit ratio **{metrics.get('cache_hit_ratio', 0)}**. "
            "Runtime optimization ≠ truth reduction."
        )
        return (
            body,
            "workstream_intelligence_runtime_optimization_program_analyze",
            _meta(sid, stage="analyze"),
        )

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded runtime optimization note ({record.get('kind', 'note')}). "
            "Evidence integrity preserved — no truth reduction."
        )
        return (
            body,
            "workstream_intelligence_runtime_optimization_program_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "runtime_optimization_dashboard")
    result = build_intelligence_runtime_optimization_program(session_id=sid)
    markdown = render_intelligence_runtime_optimization_program(
        result.intelligence_runtime_optimization_program,
        focus=focus,
    )
    metrics = result.intelligence_runtime_optimization_program.get("runtime_metrics") or {}
    headline = (
        f"Projected compose reduction **{metrics.get('compose_duration_reduction', 0)}** · "
        f"Depth reduction **{metrics.get('dependency_depth_reduction', 0)}** · "
        "Evidence integrity preserved."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_intelligence_runtime_optimization_program",
        _meta(sid, stage="view", focus=focus),
    )
