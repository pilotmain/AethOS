# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — chat router for tenant onboarding and activation."""

from __future__ import annotations

from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301,
    AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
    CROSS_TENANT_ACCESS_ENABLED_FIX_301,
    MUTATION_PERFORMED_FIX_301,
    ONBOARDING_AUTHORITY_FIX_301,
    PROVIDER_MUTATION_AUTHORITY_FIX_301,
    SECRET_COLLECTION_ENABLED_FIX_301,
    TENANT_ONBOARDING_ACTIVATION_ROUTE_ID,
    TRUST_MUTATION_AUTHORITY_FIX_301,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_intent import (
    handle_tenant_onboarding_activation_intent,
    parse_tenant_onboarding_activation_intent,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_renderer import (
    render_tenant_onboarding_activation,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": TENANT_ONBOARDING_ACTIVATION_ROUTE_ID,
        "matched_module": (
            "mission_control.tenant_onboarding_activation.tenant_onboarding_activation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_301 is False else "true",
        "onboarding_authority": "false" if ONBOARDING_AUTHORITY_FIX_301 is False else "true",
        "automatic_provisioning_enabled": "false"
        if AUTOMATIC_PROVISIONING_ENABLED_FIX_301 is False
        else "true",
        "automatic_permission_granting_enabled": "false"
        if AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301 is False
        else "true",
        "secret_collection_enabled": "false" if SECRET_COLLECTION_ENABLED_FIX_301 is False else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_301 is False
        else "true",
        "cross_tenant_access_enabled": "false"
        if CROSS_TENANT_ACCESS_ENABLED_FIX_301 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_301 is False else "true",
        "mutation_scope": "tenant_onboarding_activation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "onboarding_guidance_not_platform_authority",
        "runtime_answer_from_fix_295_296": "true",
        **extra,
    }


def route_tenant_onboarding_activation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_tenant_onboarding_activation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_tenant_onboarding_activation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded onboarding review note ({record.get('kind', 'note')}). "
            "Onboarding guidance ≠ platform authority."
        )
        return (
            body,
            "mission_control_tenant_onboarding_activation_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_tenant_onboarding_activation(session_id=sid)
    markdown = render_tenant_onboarding_activation(result.tenant_onboarding_activation)
    progress = (
        (result.tenant_onboarding_activation.get("sections") or {})
        .get("onboarding_progress_registry", [{}])[0]
    )
    headline = (
        f"Onboarding progress **{progress.get('completed_step_count', 0)}** / "
        f"**{progress.get('total_step_count', 0)}** steps. "
        "Guided setup from organization to first governed workflow — review only, no automatic provisioning."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_tenant_onboarding_activation",
        _meta(sid, stage="view"),
    )
