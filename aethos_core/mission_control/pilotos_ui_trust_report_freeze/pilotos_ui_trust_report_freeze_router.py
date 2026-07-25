# SPDX-License-Identifier: Apache-2.0
"""FIX 192 — chat router for PilotOS UI trust report freeze."""

from __future__ import annotations

from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_contract import (
    AUTOMATIC_EXPANSION_ENABLED_FIX_192,
    CROSS_REPO_AUTHORITY_FIX_192,
    EXECUTION_PERFORMED_FIX_192,
    GATE_BYPASS_ENABLED_FIX_192,
    MUTATION_PERFORMED_FIX_192,
    PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID,
    PILOT_EXECUTION_AUTHORITY_FIX_192,
    PILOT_REEXECUTION_PERFORMED_FIX_192,
    TRUST_GRANTING_AUTHORITY_FIX_192,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_intent import (
    is_pilotos_ui_trust_report_freeze_intent,
    parse_pilotos_ui_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_renderer import (
    render_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
    build_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    append_pilotos_ui_trust_report_freeze_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID,
        "matched_module": (
            "mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_192 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_192 is False else "true",
        "pilot_reexecution_performed": "false" if PILOT_REEXECUTION_PERFORMED_FIX_192 is False else "true",
        "trust_granting_authority": "false" if TRUST_GRANTING_AUTHORITY_FIX_192 is False else "true",
        "pilot_execution_authority": "false" if PILOT_EXECUTION_AUTHORITY_FIX_192 is False else "true",
        "cross_repo_authority": "false" if CROSS_REPO_AUTHORITY_FIX_192 is False else "true",
        "automatic_expansion_enabled": "false"
        if AUTOMATIC_EXPANSION_ENABLED_FIX_192 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_192 is False else "true",
        "mutation_scope": "pilotos_ui_trust_report_freeze_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "trust_freeze_not_trust_granting",
        **extra,
    }


def route_pilotos_ui_trust_report_freeze(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_pilotos_ui_trust_report_freeze_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        record, blockers = append_pilotos_ui_trust_report_freeze_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"PilotOS UI trust freeze record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_pilotos_ui_trust_report_freeze_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"PilotOS UI trust freeze record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show pilotos trust report freeze` to review the frozen baseline."
        )
        return (
            body,
            "mission_control_pilotos_ui_trust_report_freeze_record",
            _meta(
                session_id,
                stage="pilotos_ui_trust_report_freeze_record",
                record_id=str(record.get("record_id") or ""),
            ),
        )

    if not is_pilotos_ui_trust_report_freeze_intent(text):
        return None

    result = build_pilotos_ui_trust_report_freeze(session_id=session_id)
    if not result.ok:
        body = f"PilotOS UI trust report freeze unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_pilotos_ui_trust_report_freeze_blocked",
            _meta(session_id, stage="blocked"),
        )

    report = result.pilotos_ui_trust_report_freeze
    body = render_pilotos_ui_trust_report_freeze(report)
    return (
        body,
        "mission_control_pilotos_ui_trust_report_freeze",
        _meta(
            session_id,
            stage="pilotos_ui_trust_report_freeze",
            trust_status=str(report.get("trust_status") or "none"),
            atlas_expansion_blocked=str(report.get("atlas_expansion_blocked", True)),
        ),
    )
