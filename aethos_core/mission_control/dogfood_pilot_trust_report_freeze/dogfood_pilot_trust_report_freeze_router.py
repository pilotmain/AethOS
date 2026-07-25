# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — chat router for dogfood pilot trust report freeze."""

from __future__ import annotations

from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
    AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186,
    DIRECT_EXECUTION_PERFORMED_FIX_186,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID,
    EXECUTION_PERFORMED_FIX_186,
    GATE_BYPASS_ENABLED_FIX_186,
    MUTATION_PERFORMED_FIX_186,
    PILOT_REEXECUTION_PERFORMED_FIX_186,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_intent import (
    is_dogfood_pilot_trust_report_freeze_intent,
    parse_dogfood_pilot_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_renderer import (
    render_dogfood_pilot_trust_report_freeze,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    append_dogfood_pilot_trust_report_freeze_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID,
        "matched_module": "mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_186 is False else "true",
        "execution_performed": "false" if EXECUTION_PERFORMED_FIX_186 is False else "true",
        "direct_execution_performed": "false" if DIRECT_EXECUTION_PERFORMED_FIX_186 is False else "true",
        "direct_provider_mutation_performed": "false"
        if DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186 is False
        else "true",
        "pilot_reexecution_performed": "false" if PILOT_REEXECUTION_PERFORMED_FIX_186 is False else "true",
        "autonomous_trust_report_execution_enabled": "false"
        if AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186 is False
        else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_186 is False else "true",
        "mutation_scope": "dogfood_pilot_trust_report_freeze_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "trust_report_freeze_not_pilot_reexecution",
        **extra,
    }


def route_dogfood_pilot_trust_report_freeze(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_dogfood_pilot_trust_report_freeze_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        record, blockers = append_dogfood_pilot_trust_report_freeze_record(
            session_id=session_id,
            kind=kind,
            content=content,
        )
        if blockers or not record:
            body = f"Trust report freeze record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_dogfood_pilot_trust_report_freeze_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Trust report freeze record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Use `show dogfood trust report freeze` to review the frozen baseline."
        )
        return (
            body,
            "mission_control_dogfood_pilot_trust_report_freeze_record",
            _meta(
                session_id,
                stage="dogfood_pilot_trust_report_freeze_record",
                record_id=str(record.get("record_id") or ""),
                dogfood_pilot_trust_report_freeze_memory_only="true",
            ),
        )

    if not is_dogfood_pilot_trust_report_freeze_intent(text):
        return None

    result = build_dogfood_pilot_trust_report_freeze(session_id=session_id)
    if not result.ok:
        body = f"Dogfood pilot trust report freeze unavailable: {', '.join(result.blockers)}"
        return (
            body,
            "mission_control_dogfood_pilot_trust_report_freeze_blocked",
            _meta(session_id, stage="blocked"),
        )

    report = result.dogfood_pilot_trust_report_freeze
    body = render_dogfood_pilot_trust_report_freeze(report)
    return (
        body,
        "mission_control_dogfood_pilot_trust_report_freeze",
        _meta(
            session_id,
            stage="dogfood_pilot_trust_report_freeze",
            trust_status=str(report.get("trust_status") or "none"),
            multi_repo_expansion_blocked=str(report.get("multi_repo_expansion_blocked", True)),
        ),
    )
