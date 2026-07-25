# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — production rollout orchestration router."""

from __future__ import annotations

from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    get_or_create_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration import (
    advance_rollout_stage,
    assess_current_rollout_gate,
    build_rollout_status,
    is_production_rollout_orchestration_intent,
    pause_rollout,
    resume_rollout,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    ROLLOUT_STAGES,
)
from aethos_core.providers.railway.execution_contract.production_policy_operator_views import (
    is_readonly_rollout_query,
    render_unenrolled_policy_view,
)
from aethos_core.providers.railway.execution_contract.production_rollout_renderer import (
    render_rollout_gate,
    render_rollout_health_checkpoints,
    render_rollout_orchestration_result,
    render_rollout_status,
    render_rollout_timeline,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": "railway_production_rollout",
        "matched_module": "providers.railway.execution_contract.production_rollout_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "production_rollout_stage": stage,
        **extra,
    }


def route_railway_production_rollout(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_production_rollout_orchestration_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    readonly = is_readonly_rollout_query(raw)
    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=not readonly,
    )
    plan = lane.plan or {}
    execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""

    if not execution_id:
        if not readonly:
            body = render_unenrolled_policy_view("rollout_status")
            body += (
                "\n\n**Action blocked:** rollout pause/resume/advance requires "
                "a enrolled production execution."
            )
            return body, "railway_production_rollout_blocked", _meta(
                session_id, stage="blocked", enrollment="missing"
            )
        if "health checkpoint" in raw.lower():
            body = render_unenrolled_policy_view("rollout_health_checkpoint")
            return body, "railway_production_rollout_health_checkpoint", _meta(
                session_id, stage="health_checkpoint", enrollment="missing"
            )
        if "timeline" in raw.lower():
            body = render_unenrolled_policy_view("rollout_timeline")
            return body, "railway_production_rollout_timeline", _meta(
                session_id, stage="timeline", enrollment="missing"
            )
        body = render_unenrolled_policy_view("rollout_status")
        return body, "railway_production_rollout_status", _meta(
            session_id, stage="status", enrollment="missing"
        )

    if "pause" in raw.lower() and "rollout" in raw.lower():
        result = pause_rollout(
            execution_id=execution_id,
            user_text=raw,
            plan=plan,
            session_id=session_id,
        )
        body = render_rollout_orchestration_result(result)
        intent = "railway_production_rollout_pause" if result.success else "railway_production_rollout_blocked"
        return body, intent, _meta(session_id, stage="pause", success=str(result.success).lower())

    if "resume" in raw.lower() and "rollout" in raw.lower():
        result = resume_rollout(
            execution_id=execution_id,
            user_text=raw,
            plan=plan,
            session_id=session_id,
        )
        body = render_rollout_orchestration_result(result)
        intent = "railway_production_rollout_resume" if result.success else "railway_production_rollout_blocked"
        return body, intent, _meta(session_id, stage="resume", success=str(result.success).lower())

    if "advance" in raw.lower() and "rollout" in raw.lower():
        result = advance_rollout_stage(
            execution_id=execution_id,
            user_text=raw,
            plan=plan,
            session_id=session_id,
        )
        body = render_rollout_orchestration_result(result)
        intent = (
            "railway_production_rollout_advance"
            if result.success
            else "railway_production_rollout_blocked"
        )
        return body, intent, _meta(
            session_id,
            stage="advance",
            success=str(result.success).lower(),
            current_stage=str(result.journal.get("current_stage") or ""),
        )

    if "health checkpoint" in raw.lower():
        journal, _ = get_or_create_rollout_journal(
            execution_id=execution_id,
            session_id=session_id,
            plan=plan,
        )
        stage = str(journal.get("current_stage") or ROLLOUT_STAGES[0])
        body = render_rollout_health_checkpoints(
            execution_id=execution_id,
            stage=stage,
            plan=plan,
        )
        gate = assess_current_rollout_gate(execution_id=execution_id, plan=plan)
        body = body + "\n\n" + render_rollout_gate(gate)
        return body, "railway_production_rollout_health_checkpoint", _meta(
            session_id,
            stage="health_checkpoint",
            current_stage=stage,
        )

    if "timeline" in raw.lower():
        journal, _ = get_or_create_rollout_journal(
            execution_id=execution_id,
            session_id=session_id,
            plan=plan,
        )
        body = render_rollout_timeline(execution_id=execution_id, journal=journal)
        return body, "railway_production_rollout_timeline", _meta(session_id, stage="timeline")

    status = build_rollout_status(
        execution_id=execution_id,
        plan=plan,
        session_id=session_id,
    )
    body = render_rollout_status(status)
    return body, "railway_production_rollout_status", _meta(
        session_id,
        stage="status",
        current_stage=str(status.get("current_stage") or ""),
        rollout_paused=str(status.get("rollout_paused", False)).lower(),
    )
