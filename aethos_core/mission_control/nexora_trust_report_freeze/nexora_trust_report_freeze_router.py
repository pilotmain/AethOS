# SPDX-License-Identifier: Apache-2.0
"""FIX 196 — chat router for Nexora trust report freeze."""

from __future__ import annotations

from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_contract import (
    AUTOMATIC_EXPANSION_ENABLED_FIX_196,
    CROSS_REPO_AUTHORITY_FIX_196,
    EXECUTION_PERFORMED_FIX_196,
    GATE_BYPASS_ENABLED_FIX_196,
    MUTATION_PERFORMED_FIX_196,
    NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID,
    PILOT_EXECUTION_AUTHORITY_FIX_196,
    PILOT_REEXECUTION_PERFORMED_FIX_196,
    TRUST_GRANTING_AUTHORITY_FIX_196,
    TRUST_INHERITANCE_ENABLED_FIX_196,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_intent import (
    is_nexora_trust_report_freeze_intent,
    parse_nexora_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_renderer import (
    render_nexora_trust_report_freeze,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
    build_nexora_trust_report_freeze,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
    append_nexora_trust_report_freeze_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID,
        "matched_module": (
            "mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_196 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_196 is False else "true",
        "pilot_reexecution_performed": "false" if PILOT_REEXECUTION_PERFORMED_FIX_196 is False else "true",
        "trust_granting_authority": "false" if TRUST_GRANTING_AUTHORITY_FIX_196 is False else "true",
        "trust_inheritance_enabled": "false" if TRUST_INHERITANCE_ENABLED_FIX_196 is False else "true",
        "pilot_execution_authority": "false" if PILOT_EXECUTION_AUTHORITY_FIX_196 is False else "true",
        "cross_repo_authority": "false" if CROSS_REPO_AUTHORITY_FIX_196 is False else "true",
        "automatic_expansion_enabled": "false"
        if AUTOMATIC_EXPANSION_ENABLED_FIX_196 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_196 is False else "true",
        "mutation_scope": "nexora_trust_report_freeze_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "trust_freeze_not_trust_granting",
        **extra,
    }


def route_nexora_trust_report_freeze(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_nexora_trust_report_freeze_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        record, blockers = append_nexora_trust_report_freeze_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"Nexora trust freeze record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_nexora_trust_report_freeze_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Nexora trust freeze record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show nexora trust report freeze` to review the frozen baseline."
        )
        return (
            body,
            "mission_control_nexora_trust_report_freeze_record",
            _meta(
                session_id,
                stage="nexora_trust_report_freeze_record",
                record_id=str(record.get("record_id") or ""),
            ),
        )

    if not is_nexora_trust_report_freeze_intent(text):
        return None

    result = build_nexora_trust_report_freeze(session_id=session_id)
    if not result.ok:
        body = f"Nexora trust report freeze unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_nexora_trust_report_freeze_blocked",
            _meta(session_id, stage="blocked"),
        )

    report = result.nexora_trust_report_freeze
    body = render_nexora_trust_report_freeze(report)
    return (
        body,
        "mission_control_nexora_trust_report_freeze",
        _meta(
            session_id,
            stage="nexora_trust_report_freeze",
            trust_status=str(report.get("trust_status") or "none"),
            multi_repo_trust_baseline_complete=str(
                report.get("multi_repo_trust_baseline_complete", False)
            ),
        ),
    )
