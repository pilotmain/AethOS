# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — channel integration foundation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.governance.governance_friction_approval_contract import FIX_304_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
    AUTHORIZATION_BYPASS_ENABLED_FIX_304,
    AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
    CHANNEL_AUTHORITY_FIX_304,
    CHANNEL_CAPABILITY_SUPPORT,
    CHANNEL_DOMAINS,
    CHANNEL_INGRESS_MODEL,
    CHANNEL_INTEGRATION_COMPOSES_EVIDENCE_ONLY_FIX_304,
    CHANNEL_INTEGRATION_FOUNDATION_FIX,
    CHANNEL_INTEGRATION_FOUNDATION_INVARIANT,
    CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION,
    CHANNELS,
    CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
    CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
    EXECUTION_PERFORMED_FIX_304,
    FORBIDDEN_CHANNEL_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_304,
    HUMAN_CHANNEL_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_304,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
    has_channel_decision_approve,
    list_channel_integration_foundation_records,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_evaluator import (
    evaluate_access_request,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)
from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
    build_multi_tenant_platform_foundation,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.orgs.members import get_member_role, list_members
from aethos_core.orgs.organizations import get_current_organization


@dataclass(frozen=True)
class ChannelIntegrationFoundationResult:
    ok: bool
    session_id: str
    channel_integration_foundation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_user(*, session_id: str) -> str:
    sid = (session_id or "default").strip()[:64] or "default"
    if sid.startswith("tg-"):
        return "telegram-channel-user"
    return sid if sid != "default" else "default"


def _channel_status(*, channel: str) -> dict[str, Any]:
    settings = get_settings()
    if channel == "web":
        return {"status": "OPERATIONAL", "configured": True, "readiness": "ready"}
    if channel == "telegram":
        from aethos_core.channels.telegram.telegram_runtime import telegram_configured

        configured = telegram_configured()
        return {
            "status": "OPERATIONAL" if configured else "EXPERIMENTAL",
            "configured": configured,
            "readiness": "ready" if configured else "not_configured",
        }
    return {"status": "PLANNED", "configured": False, "readiness": "planned"}


def _capability_matrix_rows() -> list[dict[str, Any]]:
    rows = []
    for channel, supported, unsupported in CHANNEL_CAPABILITY_SUPPORT:
        rows.append(
            {
                "channel": channel,
                "supported_actions": list(supported),
                "unsupported_actions": list(unsupported),
                "governance_limitations": [
                    "Same Mission Control governance for all channels.",
                    "No channel-specific authorization bypass.",
                ],
                "read_only": True,
            }
        )
    return rows


def _supported_actions(channel: str) -> list[str]:
    for name, supported, _unsupported in CHANNEL_CAPABILITY_SUPPORT:
        if name == channel:
            return list(supported)
    return []


def build_channel_integration_foundation(*, session_id: str) -> ChannelIntegrationFoundationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    user_id = _resolve_user(session_id=sid)
    records = list_channel_integration_foundation_records()

    tenant = build_multi_tenant_platform_foundation(session_id=sid)
    tenant_sections = (tenant.multi_tenant_platform_foundation.get("sections") or {})
    fix_300_registry = (tenant_sections.get("channel_registry") or [{}])[0]

    identity = build_identity_access_hardening(session_id=sid)
    identity_sections = (identity.identity_access_hardening.get("sections") or {})
    fix_302_channel_auth = (identity_sections.get("channel_authorization_report") or [{}])[0]

    build_provider_connection_experience(session_id=sid)

    current_org = get_current_organization()
    org_id = str(current_org.get("org_id") or "")
    role = get_member_role(user_id=user_id, org_id=org_id)
    members = list_members(org_id=org_id)

    registry_channels = []
    connected_count = 0
    for channel in CHANNELS:
        status = _channel_status(channel=channel)
        if status["configured"]:
            connected_count += 1
        registry_channels.append(
            {
                "channel": channel,
                "status": status["status"],
                "readiness": status["readiness"],
                "configured": status["configured"],
                "ingress": CHANNEL_INGRESS_MODEL,
                "cross_tenant_channel_access_enabled": False,
                "read_only": True,
            }
        )

    channel_registry = [
        {
            "registry_id": "channel-registry",
            "channels": registry_channels,
            "channel_count": len(registry_channels),
            "connected_channel_count": connected_count,
            "common_ingress_model": CHANNEL_INGRESS_MODEL,
            "fix_300_registry_composed": bool(fix_300_registry),
            "read_only": True,
        }
    ]

    channel_identity = [
        {
            "report_id": "channel-identity-report",
            "session_id": sid,
            "platform_user_id": user_id,
            "organization_id": org_id,
            "role": role,
            "membership_count": len(members),
            "identity_resolution_path": [
                "channel_user",
                "platform_identity",
                "tenant_membership",
                "role",
            ],
            "telegram_session_prefix": "tg-" if sid.startswith("tg-") else None,
            "cross_channel_identity_bypass_enabled": False,
            "read_only": True,
        }
    ]

    channel_authorization = [
        {
            "report_id": "channel-authorization-report",
            "composed_from_fix_302": True,
            "authorization_model": "same_as_mission_control_core",
            "channels": fix_302_channel_auth.get("channels") or [],
            "tenant_isolation_enforced": True,
            "authorization_bypass_enabled": False,
            "read_only": True,
        }
    ]

    capability_matrix = [
        {
            "matrix_id": "channel-capability-matrix",
            "channels": _capability_matrix_rows(),
            "channel_specific_logic_forbidden": True,
            "read_only": True,
        }
    ]

    auth_eval = evaluate_access_request(role=role, permission="view", requester_org_id=org_id)

    web_report = [
        {
            "report_id": "web-channel-report",
            "reference_implementation": True,
            "status": "OPERATIONAL",
            "ingress": "mission_control_core",
            "mission_control_ui": True,
            "authorization_allowed": auth_eval["allowed"],
            "read_only": True,
        }
    ]

    telegram_status = _channel_status(channel="telegram")
    telegram_report = [
        {
            "report_id": "telegram-channel-report",
            "bot_readiness": telegram_status["readiness"],
            "configured": telegram_status["configured"],
            "identity_mapping": "telegram chat/user maps to tg-* session_id",
            "capability_support": _supported_actions("telegram"),
            "ingress": CHANNEL_INGRESS_MODEL,
            "read_only": True,
        }
    ]

    slack_report = [
        {
            "report_id": "slack-channel-report",
            "workspace_readiness": "planned",
            "configured": False,
            "identity_mapping": "planned_slack_user_to_platform_identity",
            "capability_support": _supported_actions("slack"),
            "status": "PLANNED",
            "read_only": True,
        }
    ]

    email_report = [
        {
            "report_id": "email-channel-report",
            "inbound_readiness": "planned",
            "outbound_readiness": "planned",
            "identity_mapping": "planned_email_sender_to_platform_identity",
            "capability_support": _supported_actions("email"),
            "status": "PLANNED",
            "read_only": True,
        }
    ]

    voice_report = [
        {
            "report_id": "voice-channel-report",
            "voice_readiness": "planned",
            "call_orchestration_readiness": "planned",
            "capability_roadmap": _supported_actions("voice"),
            "status": "PLANNED",
            "read_only": True,
        }
    ]

    channel_dashboard = [
        {
            "dashboard_id": "channel-dashboard",
            "connected_channels": connected_count,
            "total_channels": len(CHANNELS),
            "readiness_summary": [
                {"channel": row["channel"], "readiness": row["readiness"], "status": row["status"]}
                for row in registry_channels
            ],
            "authorization_health": "fix_302_composed",
            "identity_mapping_health": "session_scoped_with_org_context",
            "ingress_model": CHANNEL_INGRESS_MODEL,
            "automatic_channel_provisioning_enabled": False,
            "read_only": True,
        }
    ]

    sections = {
        "channel_registry": channel_registry,
        "channel_identity_report": channel_identity,
        "channel_authorization_report": channel_authorization,
        "channel_capability_matrix": capability_matrix,
        "web_channel_report": web_report,
        "telegram_channel_report": telegram_report,
        "slack_channel_report": slack_report,
        "email_channel_report": email_report,
        "voice_channel_report": voice_report,
        "channel_dashboard": channel_dashboard,
        "human_channel_review": [
            {
                "review_id": "human-channel-review",
                "decisions_supported": list(HUMAN_CHANNEL_DECISION_KINDS),
                "channel_decision_approve": has_channel_decision_approve(session_id=sid),
                "automatic_channel_provisioning_enabled": False,
                "read_only": True,
            }
        ],
        "forbidden_channel_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_CHANNEL_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION,
        "fix": CHANNEL_INTEGRATION_FOUNDATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_304,
        "execution_performed": EXECUTION_PERFORMED_FIX_304,
        "channel_integration_compose_artifacts_only": CHANNEL_INTEGRATION_COMPOSES_EVIDENCE_ONLY_FIX_304,
        "channel_authority": CHANNEL_AUTHORITY_FIX_304,
        "automatic_channel_provisioning_enabled": AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
        "cross_channel_identity_bypass_enabled": CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
        "cross_tenant_channel_access_enabled": CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
        "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_304,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_304,
        "invariant": CHANNEL_INTEGRATION_FOUNDATION_INVARIANT,
        "session_id": sid,
        "channel_domains": list(CHANNEL_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "channel_decision_approve": has_channel_decision_approve(session_id=sid),
        "fix_304_certification_requirements": list(FIX_304_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_300_channel_registry": True,
            "composes_fix_302_channel_authorization": True,
            "composes_fix_303_provider_connection_context": True,
            "automatic_channel_provisioning_performed": False,
            "cross_tenant_channel_routing_performed": False,
            "channel_specific_governance_performed": False,
        },
    }

    return ChannelIntegrationFoundationResult(
        ok=True,
        session_id=sid,
        channel_integration_foundation=payload,
        detail="Channel integration foundation composed with unified Mission Control ingress (integration ≠ duplication).",
    )
