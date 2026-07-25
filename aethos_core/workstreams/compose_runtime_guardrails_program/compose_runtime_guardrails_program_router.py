# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 / FIX 346 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_contract import (
    AUTHORITY_EXPANSION_FIX_346,
    COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ROUTE_ID,
    EVIDENCE_REDUCTION_FIX_346,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_346,
    LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346,
    MUTATION_PERFORMED_FIX_346,
    TRUST_MUTATION_AUTHORITY_FIX_346,
    TRUTH_MUTATION_FIX_346,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_intent import (
    handle_compose_runtime_guardrails_intent,
    parse_compose_runtime_guardrails_intent,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_renderer import (
    render_compose_runtime_guardrails_program,
)
from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_service import (
    build_compose_runtime_guardrails_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": COMPOSE_RUNTIME_GUARDRAILS_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_346 is False else "true",
        "evidence_reduction": "false" if EVIDENCE_REDUCTION_FIX_346 is False else "true",
        "truth_mutation": "false" if TRUTH_MUTATION_FIX_346 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_346 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_346 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_346 is False else "true",
        "local_runtime_guardrail_executable": "true"
        if LOCAL_RUNTIME_GUARDRAIL_EXECUTABLE_FIX_346 is True
        else "false",
        "mutation_scope": "compose_runtime_guardrails_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "runtime_guardrails_not_evidence_reduction",
        **extra,
    }


def route_compose_runtime_guardrails_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_compose_runtime_guardrails_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_compose_runtime_guardrails_intent(intent, session_id=sid)

    if handled.get("action") == "benchmark":
        result = handled.get("result") or {}
        body = (
            f"Benchmark command `{intent.get('command_text')}` — mode **{result.get('mode', 'benchmark')}**. "
            "Heavy compose requires explicit benchmark mode. Runtime guardrails ≠ evidence reduction."
        )
        return (
            body,
            "workstream_compose_runtime_guardrails_program_benchmark",
            _meta(sid, stage="benchmark", command=str(intent.get("command_text") or "")),
        )

    if handled.get("action") in {"enforce", "record"}:
        record = handled.get("record") or {}
        body = (
            f"Runtime guardrail note recorded ({record.get('kind', 'note')}). "
            "Guardrails prevent accidental expensive execution without reducing evidence."
        )
        return (
            body,
            "workstream_compose_runtime_guardrails_program_record",
            _meta(sid, stage=str(handled.get("action")), record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "runtime_safety_dashboard")
    result = build_compose_runtime_guardrails_program(session_id=sid)
    markdown = render_compose_runtime_guardrails_program(result.compose_runtime_guardrails_program, focus=focus)
    headline = (
        f"Active mode **{result.compose_runtime_guardrails_program.get('active_runtime_mode')}** · "
        "Critical compose requires explicit benchmark mode."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_compose_runtime_guardrails_program",
        _meta(sid, stage="view", focus=focus),
    )
