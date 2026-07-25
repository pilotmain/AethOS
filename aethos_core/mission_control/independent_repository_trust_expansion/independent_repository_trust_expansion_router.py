# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — chat router for independent repository trust expansion."""

from __future__ import annotations

from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187,
    DIRECT_EXECUTION_PERFORMED_FIX_187,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187,
    EXECUTION_PERFORMED_FIX_187,
    GATE_BYPASS_ENABLED_FIX_187,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_187,
    PILOT_EXECUTION_PERFORMED_FIX_187,
    TRUST_TRANSFER_ENABLED_FIX_187,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_intent import (
    is_independent_repository_trust_expansion_intent,
    parse_independent_repository_trust_expansion_record_intent,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_renderer import (
    render_independent_repository_trust_expansion,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_service import (
    build_independent_repository_trust_expansion,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    append_independent_repository_trust_expansion_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID,
        "matched_module": "mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_187 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_187 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_187 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187 is False
        else "true",
        "pilot_execution_performed": "false" if PILOT_EXECUTION_PERFORMED_FIX_187 is False else "true",
        "autonomous_trust_expansion_enabled": "false"
        if AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_187 is False else "true",
        "trust_transfer_enabled": "false" if TRUST_TRANSFER_ENABLED_FIX_187 is False else "true",
        "mutation_scope": "independent_repository_trust_expansion_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "trust_expansion_not_pilot_execution",
        **extra,
    }


def route_independent_repository_trust_expansion(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_independent_repository_trust_expansion_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        record, blockers = append_independent_repository_trust_expansion_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"Repository trust expansion record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_independent_repository_trust_expansion_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Repository trust expansion record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show repository trust expansion` to review the registry."
        )
        return (
            body,
            "mission_control_independent_repository_trust_expansion_record",
            _meta(
                session_id,
                stage="independent_repository_trust_expansion_record",
                record_id=str(record.get("record_id") or ""),
                independent_repository_trust_expansion_memory_only="true",
            ),
        )

    if not is_independent_repository_trust_expansion_intent(text):
        return None

    result = build_independent_repository_trust_expansion(session_id=session_id)
    if not result.ok:
        body = f"Repository trust expansion unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_independent_repository_trust_expansion_blocked",
            _meta(session_id, stage="blocked"),
        )

    report = result.independent_repository_trust_expansion
    body = render_independent_repository_trust_expansion(report)
    return (
        body,
        "mission_control_independent_repository_trust_expansion",
        _meta(
            session_id,
            stage="independent_repository_trust_expansion",
            phase_1_complete=str(report.get("phase_1_complete", False)),
            next_phase_2_repository=str(report.get("next_phase_2_repository") or ""),
        ),
    )
