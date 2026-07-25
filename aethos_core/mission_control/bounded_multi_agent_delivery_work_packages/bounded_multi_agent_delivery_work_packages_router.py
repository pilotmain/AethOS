# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — chat router for bounded delivery work packages."""

from __future__ import annotations

from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_contract import (
    AUTONOMOUS_EXECUTION_ENABLED_FIX_168,
    BOUNDED_DELIVERY_WORK_PACKAGES_ROUTE_ID,
    CODE_WRITE_ENABLED_FIX_168,
    MUTATION_PERFORMED_FIX_168,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_intent import (
    is_bounded_delivery_work_packages_intent,
    parse_work_packages_record_intent,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_renderer import (
    render_bounded_delivery_work_packages,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
    append_bounded_delivery_work_packages_record,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
    build_execution_handoff_coordination,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": BOUNDED_DELIVERY_WORK_PACKAGES_ROUTE_ID,
        "matched_module": (
            "mission_control.bounded_multi_agent_delivery_work_packages."
            "bounded_multi_agent_delivery_work_packages_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_168 is False else "true",
        "autonomous_execution_enabled": "false" if AUTONOMOUS_EXECUTION_ENABLED_FIX_168 is False else "true",
        "code_write_enabled": "false" if CODE_WRITE_ENABLED_FIX_168 is False else "true",
        "mutation_scope": "bounded_delivery_work_packages_memory_only",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "work_packages_not_execution_authority",
        **extra,
    }


def route_bounded_delivery_work_packages(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    record_intent = parse_work_packages_record_intent(text)
    if record_intent is not None:
        kind, content = record_intent
        handoff = build_execution_handoff_coordination(session_id=session_id)
        handoff_payload = handoff.execution_handoff_coordination if handoff.ok else {}
        record, blockers = append_bounded_delivery_work_packages_record(
            session_id=session_id,
            kind=kind,
            content=content,
            plan_id=str(handoff_payload.get("plan_id") or "") or None,
            correlation_id=str(handoff_payload.get("correlation_id") or "") or None,
        )
        if blockers or not record:
            body = f"Work package record blocked: {', '.join(blockers)}"
            return (
                body,
                "mission_control_bounded_delivery_work_packages_record_blocked",
                _meta(session_id, stage="blocked"),
            )
        body = (
            f"Work package record persisted (`{record.get('record_id')}`, kind `{kind}`). "
            "Package scoping only — no execution authority."
        )
        return (
            body,
            "mission_control_bounded_delivery_work_packages_record",
            _meta(
                session_id,
                stage="bounded_delivery_work_packages_record",
                record_id=str(record.get("record_id") or ""),
                bounded_delivery_work_packages_memory_only="true",
            ),
        )

    if not is_bounded_delivery_work_packages_intent(text):
        return None

    result = build_bounded_delivery_work_packages(session_id=session_id)
    if not result.ok:
        body = f"Bounded delivery work packages unavailable: {', '.join(result.blockers)}"
        return body, "mission_control_bounded_delivery_work_packages_blocked", _meta(session_id, stage="blocked")

    body = render_bounded_delivery_work_packages(result.bounded_delivery_work_packages)
    return (
        body,
        "mission_control_bounded_delivery_work_packages",
        _meta(
            session_id,
            stage="bounded_delivery_work_packages",
            work_package_record_count=str(result.bounded_delivery_work_packages.get("work_package_record_count", 0)),
        ),
    )
