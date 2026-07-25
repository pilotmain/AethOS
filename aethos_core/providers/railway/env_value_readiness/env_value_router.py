# SPDX-License-Identifier: Apache-2.0
"""Route Railway env value readiness commands."""

from __future__ import annotations

from typing import Any

_BLOCKED_HANDLERS = (
    "generic_devops,explicit_mutation,railway_restart,github_workflow_lane,"
    "browser_observation,railway_mutation_preflight"
)


def route_railway_env_value_readiness(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        compose_no_plan_after_lifecycle_ensure,
        ensure_railway_deployment_lifecycle_for_lane,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import (
        classify_deployment_plan_lifecycle_state,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_context import (
        record_user_marked_configured,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_intent import (
        is_railway_env_value_configure_intent,
        is_railway_env_value_intent,
        is_railway_env_value_mark_intent,
        is_railway_env_value_minimum_secrets_intent,
        is_railway_env_value_refresh_intent,
        is_railway_env_value_secure_summary_intent,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        get_or_assess_env_value_readiness,
    )
    from aethos_core.providers.railway.env_value_readiness.env_readiness_summary_renderer import (
        render_compact_env_readiness_report,
        render_minimum_required_secrets,
        render_secure_env_readiness_summary,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_renderer import (
        render_configure_securely_guide,
        render_mark_configured_reply,
        render_refresh_reply,
    )

    raw = (text or "").strip()
    if not is_railway_env_value_intent(raw):
        return None

    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=True,
    )
    plan = lane.plan
    if classify_deployment_plan_lifecycle_state(plan) == "no_plan":
        return (
            compose_no_plan_after_lifecycle_ensure(
                ensure_result=lane.ensure_result,
                session_id=session_id,
                materialization_failure=lane.materialization_failure,
            ),
            "railway_env_value_readiness_not_ready",
            _meta(session_id, stage="no_plan", ready="false"),
        )

    if is_railway_env_value_mark_intent(raw):
        record_user_marked_configured(session_id=session_id)
        return (
            render_mark_configured_reply(),
            "railway_env_value_readiness_mark_recorded",
            _meta(session_id, stage="mark_recorded", ready="false"),
        )

    force_refresh = is_railway_env_value_refresh_intent(raw)
    state = get_or_assess_env_value_readiness(
        plan=plan or {},
        session_id=session_id,
        force_refresh=force_refresh,
    )

    if is_railway_env_value_secure_summary_intent(raw):
        body = render_secure_env_readiness_summary(state)
        intent = "railway_env_value_readiness_secure_summary"
        stage = "secure_summary"
    elif is_railway_env_value_minimum_secrets_intent(raw):
        body = render_minimum_required_secrets(state)
        intent = "railway_env_value_readiness_minimum_secrets"
        stage = "minimum_secrets"
    elif is_railway_env_value_configure_intent(raw):
        body = render_configure_securely_guide(state=state)
        intent = "railway_env_value_readiness_configure_guide"
        stage = "configure_guide"
    elif is_railway_env_value_refresh_intent(raw):
        body = render_refresh_reply(state)
        intent = "railway_env_value_readiness_refresh"
        stage = "refresh"
    else:
        body = render_compact_env_readiness_report(state)
        intent = "railway_env_value_readiness_check"
        stage = "check"

    return body, intent, _meta(
        session_id,
        stage=stage,
        ready="true" if state.get("ready") else "false",
        missing=",".join(state.get("critical_missing") or state.get("missing") or []),
        state=state,
    )


def _meta(
    session_id: str,
    *,
    stage: str,
    ready: str,
    missing: str = "",
    state: dict[str, Any] | None = None,
) -> dict[str, str]:
    meta = {
        "route_id": "railway_env_value_readiness",
        "matched_module": "providers.railway.env_value_readiness.env_value_router",
        "railway_env_value_readiness_stage": stage,
        "blocked_handlers": _BLOCKED_HANDLERS,
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "env_value_ready": ready,
    }
    if missing:
        meta["env_value_missing"] = missing
    if state:
        meta["env_profile"] = str(state.get("env_profile") or state.get("deployment_profile") or "")
        meta["env_value_ready_mode"] = str(state.get("ready_mode") or "")
        meta["critical_missing_count"] = str(state.get("critical_missing_count", 0))
        meta["optional_missing_count"] = str(state.get("optional_missing_count", 0))
        meta["defaulted_count"] = str(state.get("defaulted_count", 0))
        meta["ignored_dev_only_count"] = str(state.get("ignored_dev_only_count", 0))
        meta["configured_securely_count"] = str(state.get("configured_securely_count", 0))
        meta["minimum_secret_set_complete"] = str(state.get("minimum_secret_set_complete", False)).lower()
        meta["env_readiness_confidence"] = str(state.get("env_readiness_confidence") or "")
        if state.get("env_readiness_score") is not None:
            meta["env_readiness_score"] = str(state.get("env_readiness_score"))
    return meta
