# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 / FIX 339 — chat router."""

from __future__ import annotations

from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_contract import (
    AUTHORITY_EXPANSION_FIX_339,
    DELIVERY_AUTHORITY_FIX_339,
    GOVERNANCE_BYPASS_AUTHORITY_FIX_339,
    LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339,
    MUTATION_PERFORMED_FIX_339,
    REAL_WORLD_DELIVERY_PROOF_PROGRAM_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_339,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_intent import (
    handle_real_world_delivery_proof_intent,
    parse_real_world_delivery_proof_intent,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_renderer import (
    render_real_world_delivery_proof_program,
)
from aethos_core.workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_service import (
    build_real_world_delivery_proof_program,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": REAL_WORLD_DELIVERY_PROOF_PROGRAM_ROUTE_ID,
        "matched_module": "workstreams.real_world_delivery_proof_program.real_world_delivery_proof_program_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_339 is False else "true",
        "delivery_authority": "false" if DELIVERY_AUTHORITY_FIX_339 is False else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_339 is False else "true",
        "authority_expansion": "false" if AUTHORITY_EXPANSION_FIX_339 is False else "true",
        "governance_bypass_authority": "false" if GOVERNANCE_BYPASS_AUTHORITY_FIX_339 is False else "true",
        "local_delivery_proof_executable": "true"
        if LOCAL_DELIVERY_PROOF_EXECUTABLE_FIX_339 is True
        else "false",
        "mutation_scope": "real_world_delivery_proof_program",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "operational_proof_not_authority_expansion",
        **extra,
    }


def route_real_world_delivery_proof_program(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_real_world_delivery_proof_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_real_world_delivery_proof_intent(intent, session_id=sid)

    if handled.get("action") == "run":
        result = handled.get("result") or {}
        body = (
            f"Real-world delivery proof — **{'PASSED' if result.get('passed') else 'FAILED'}** "
            f"({result.get('duration_ms', 0)}ms). "
            "Operational proof ≠ authority expansion."
        )
        return (
            body,
            "workstream_real_world_delivery_proof_program_run",
            _meta(
                sid,
                stage="run",
                proof_passed="true" if result.get("passed") else "false",
            ),
        )

    if handled.get("action") in {"record", "candidate"}:
        label = "candidate" if handled.get("action") == "candidate" else handled.get("record", {}).get("kind", "note")
        body = (
            f"Recorded delivery proof {label}. "
            "Operational proof ≠ authority expansion."
        )
        return (
            body,
            "workstream_real_world_delivery_proof_program_record",
            _meta(sid, stage="record"),
        )

    focus = str(handled.get("focus") or "delivery_proof_dashboard")
    result = build_real_world_delivery_proof_program(session_id=sid)
    markdown = render_real_world_delivery_proof_program(
        result.real_world_delivery_proof_program,
        focus=focus,
    )
    metrics = result.real_world_delivery_proof_program.get("metrics") or {}
    headline = (
        f"Deliveries **{metrics.get('successful_deliveries', 0)}** successful · "
        f"**{metrics.get('failed_deliveries', 0)}** failed · "
        f"**{metrics.get('deployments_verified', 0)}** verified. "
        "Proof measures execution — no authority expansion."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "workstream_real_world_delivery_proof_program",
        _meta(sid, stage="view", focus=focus),
    )
