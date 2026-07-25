# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — chat router for multi-tenant platform foundation."""

from __future__ import annotations

from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
    AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
    CROSS_TENANT_ACCESS_ENABLED_FIX_300,
    CROSS_TENANT_TRUST_ENABLED_FIX_300,
    GATE_BYPASS_ENABLED_FIX_300,
    MERGE_AUTHORITY_FIX_300,
    MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_300,
    PERMISSION_ESCALATION_ENABLED_FIX_300,
    PROVIDER_MUTATION_AUTHORITY_FIX_300,
    REPOSITORY_MUTATION_AUTHORITY_FIX_300,
    TENANT_AUTHORITY_FIX_300,
    TRUST_MUTATION_AUTHORITY_FIX_300,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_intent import (
    handle_multi_tenant_platform_foundation_intent,
    parse_multi_tenant_platform_foundation_intent,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_renderer import (
    render_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": MULTI_TENANT_PLATFORM_FOUNDATION_ROUTE_ID,
        "matched_module": (
            "mission_control.multi_tenant_platform_foundation."
            "multi_tenant_platform_foundation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_300 is False else "true",
        "tenant_authority": "false" if TENANT_AUTHORITY_FIX_300 is False else "true",
        "automatic_tenant_creation_enabled": "false"
        if AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300 is False
        else "true",
        "cross_tenant_access_enabled": "false"
        if CROSS_TENANT_ACCESS_ENABLED_FIX_300 is False
        else "true",
        "cross_tenant_trust_enabled": "false"
        if CROSS_TENANT_TRUST_ENABLED_FIX_300 is False
        else "true",
        "permission_escalation_enabled": "false"
        if PERMISSION_ESCALATION_ENABLED_FIX_300 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_300 is False else "true",
        "repository_mutation_authority": "false"
        if REPOSITORY_MUTATION_AUTHORITY_FIX_300 is False
        else "true",
        "provider_mutation_authority": "false"
        if PROVIDER_MUTATION_AUTHORITY_FIX_300 is False
        else "true",
        "merge_authority": "false" if MERGE_AUTHORITY_FIX_300 is False else "true",
        "gate_bypass_enabled": "false" if GATE_BYPASS_ENABLED_FIX_300 is False else "true",
        "mutation_scope": "multi_tenant_platform_foundation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "multi_tenant_not_governance_bypass",
        **extra,
    }


def route_multi_tenant_platform_foundation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_multi_tenant_platform_foundation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_multi_tenant_platform_foundation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded tenant platform note ({record.get('kind', 'note')}). "
            "Multi-tenant platform ≠ governance bypass."
        )
        return (
            body,
            "mission_control_multi_tenant_platform_foundation_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    result = build_multi_tenant_platform_foundation(session_id=sid)
    markdown = render_multi_tenant_platform_foundation(result.multi_tenant_platform_foundation)
    dashboard = (
        (result.multi_tenant_platform_foundation.get("sections") or {})
        .get("tenant_dashboard", [{}])[0]
    )
    headline = (
        f"Organizations **{dashboard.get('organization_count', 0)}**, "
        f"workspaces **{dashboard.get('workspace_count', 0)}**, "
        f"projects **{dashboard.get('project_count', 0)}**. "
        "Multi-tenant platform ≠ governance bypass."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_multi_tenant_platform_foundation",
        _meta(sid, stage="view"),
    )
