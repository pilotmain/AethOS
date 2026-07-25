# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — chat router for work package readiness + lane admission."""

from __future__ import annotations

from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_169,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169,
    MUTATION_PERFORMED_FIX_169,
    WORK_PACKAGE_READINESS_LANE_ADMISSION_ROUTE_ID,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_intent import (
    is_work_package_readiness_lane_admission_intent,
    parse_lane_admission_record_intent,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_renderer import (
    render_work_package_readiness_lane_admission,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_service import (
    build_work_package_readiness_lane_admission,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
    append_work_package_readiness_lane_admission_record,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": WORK_PACKAGE_READINESS_LANE_ADMISSION_ROUTE_ID,
        "matched_module": (
            "mission_control.work_package_readiness_lane_admission."
            "work_package_readiness_lane_admission_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_169 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_169 is False else "true",
        "autonomous_lane_entry_enabled": "false"
        if AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169 is False
        else "true",
        "mutation_scope": "work_package_readiness_lane_admission_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "readiness_not_execution_authority",
        **extra,
    }


def route_work_package_readiness_lane_admission(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_lane_admission_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        wp = build_bounded_delivery_work_packages(session_id=session_id)
        wp_payload = wp.bounded_delivery_work_packages if wp.ok else {}
        record, blockers = append_work_package_readiness_lane_admission_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(wp_payload.get("plan_id") or "") or None,
            correlation_id=str(wp_payload.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Lane admission record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_work_package_readiness_lane_admission_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Lane admission record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Readiness evaluation only — no execution authority."
        )
        return (
            body,
            "mission_control_work_package_readiness_lane_admission_record",
            _meta(
                session_id,
                stage="work_package_readiness_lane_admission_record",
                record_id=str(record.get("record_id") or ""),
                work_package_readiness_lane_admission_memory_only="true",
            ),
        )

    if not is_work_package_readiness_lane_admission_intent(text):
        return None

    result = build_work_package_readiness_lane_admission(session_id=session_id)
    if not result.ok:
        body = f"Work package readiness unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_work_package_readiness_lane_admission_blocked", _meta(session_id, stage="blocked")

    body = render_work_package_readiness_lane_admission(result.work_package_readiness_lane_admission)
    return (
        body,
        "mission_control_work_package_readiness_lane_admission",
        _meta(
            session_id,
            stage="work_package_readiness_lane_admission",
            lane_admission_record_count=str(
                result.work_package_readiness_lane_admission.get("lane_admission_record_count", 0)
            ),
        ),
    )
