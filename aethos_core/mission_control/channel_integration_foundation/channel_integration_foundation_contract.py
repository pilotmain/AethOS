# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — channel integration foundation contract."""

from __future__ import annotations

from typing import Final

CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_channel_integration_foundation_v1"
)
CHANNEL_INTEGRATION_FOUNDATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_channel_integration_foundation_record_v1"
)
CHANNEL_INTEGRATION_FOUNDATION_FIX: Final[str] = "FIX 304"

MUTATION_PERFORMED_FIX_304: Final[bool] = False
EXECUTION_PERFORMED_FIX_304: Final[bool] = False
CHANNEL_AUTHORITY_FIX_304: Final[bool] = False
AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304: Final[bool] = False
CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304: Final[bool] = False
CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304: Final[bool] = False
AUTHORIZATION_BYPASS_ENABLED_FIX_304: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_304: Final[bool] = False
CHANNEL_INTEGRATION_COMPOSES_EVIDENCE_ONLY_FIX_304: Final[bool] = True

CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID: Final[str] = (
    "mission_control_channel_integration_foundation"
)

CHANNEL_INTEGRATION_FOUNDATION_INVARIANT: Final[str] = (
    "channel_integration_foundation_unified_ingress_without_channel_specific_governance"
)

CHANNELS: Final[tuple[str, ...]] = (
    "web",
    "telegram",
    "slack",
    "email",
    "voice",
)

CHANNEL_DOMAINS: Final[tuple[str, ...]] = (
    "channel_registry",
    "channel_identity_mapping",
    "channel_authorization",
    "channel_capability_matrix",
    "web_channel",
    "telegram_channel",
    "slack_channel",
    "email_channel",
    "voice_channel",
    "channel_health_dashboard",
)

CHANNEL_INGRESS_MODEL: Final[str] = "all_channels_route_to_mission_control_core"

CHANNEL_CAPABILITY_SUPPORT: Final[tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...]] = (
    (
        "web",
        ("mission_control_queries", "onboarding", "authorization", "provider_connection", "governed_workflows"),
        ("channel_specific_governance", "identity_bypass", "hidden_execution"),
    ),
    (
        "telegram",
        ("operational_queries", "investigation_followups", "readonly_provider_checks"),
        ("channel_specific_governance", "identity_bypass", "hidden_execution", "secret_collection"),
    ),
    (
        "slack",
        ("planned_operational_queries",),
        ("all_actions_until_configured", "channel_specific_governance"),
    ),
    (
        "email",
        ("planned_inbound_notifications", "planned_outbound_summaries"),
        ("all_actions_until_configured", "channel_specific_governance"),
    ),
    (
        "voice",
        ("planned_voice_ingress",),
        ("all_actions_until_configured", "channel_specific_governance", "call_orchestration"),
    ),
)

HUMAN_CHANNEL_DECISION_KINDS: Final[tuple[str, ...]] = (
    "channel_decision_approve",
    "channel_decision_hold",
    "channel_decision_reject",
    "channel_decision_defer",
)

CHANNEL_INTEGRATION_FOUNDATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "channel_note",
    *HUMAN_CHANNEL_DECISION_KINDS,
    "channel_integration_foundation_record",
)

CHANNEL_INTEGRATION_FOUNDATION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("integration_not_duplication", "Channel integration ≠ channel-specific logic."),
    ("unified_ingress", "All channels route into the same Mission Control orchestration layer."),
    ("identical_governance", "Governance remains identical regardless of entry channel."),
    ("identity_mapping", "Channel users map to platform identity, tenant membership, and role."),
    ("authorization_parity", "FIX 302 authorization applies consistently across channels."),
    ("tenant_isolation", "Cross-tenant channel access remains blocked."),
    ("no_bypass", "No channel may bypass governance, identity, or trust boundaries."),
    ("web_reference", "Web channel is the reference implementation for channel parity."),
    ("human_review", "Channel review records decisions without automatic provisioning."),
    ("compose_only", "Composes FIX 300 channel registry and FIX 302 authorization without re-execution."),
)

FORBIDDEN_CHANNEL_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("channel_specific_governance", "Channels never introduce channel-specific governance rules."),
    ("channel_specific_authorization", "Channels never introduce channel-specific authorization bypass."),
    ("cross_tenant_routing", "Channels never route across tenant boundaries."),
    ("identity_bypass", "Channels never bypass identity resolution."),
    ("trust_bypass", "Channels never bypass trust boundaries."),
    ("hidden_execution_paths", "Channels never introduce hidden execution paths."),
)

CHANNEL_INTEGRATION_FOUNDATION_EXECUTABLE: Final[bool] = False

MAX_CHANNEL_INTEGRATION_FOUNDATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_CHANNEL_INTEGRATION_FOUNDATION_RECORDS: Final[int] = 500
