# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection experience contract."""

from __future__ import annotations

from typing import Final

PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION: Final[str] = (
    "mission_control_provider_connection_experience_v1"
)
PROVIDER_CONNECTION_EXPERIENCE_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_provider_connection_experience_record_v1"
)
PROVIDER_CONNECTION_EXPERIENCE_FIX: Final[str] = "FIX 303"

MUTATION_PERFORMED_FIX_303: Final[bool] = False
EXECUTION_PERFORMED_FIX_303: Final[bool] = False
PROVIDER_CONNECTION_AUTHORITY_FIX_303: Final[bool] = False
AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_303: Final[bool] = False
SECRET_COLLECTION_ENABLED_FIX_303: Final[bool] = False
PERMISSION_ESCALATION_ENABLED_FIX_303: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_303: Final[bool] = False
PROVIDER_CONNECTION_COMPOSES_EVIDENCE_ONLY_FIX_303: Final[bool] = True

PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID: Final[str] = (
    "mission_control_provider_connection_experience"
)

PROVIDER_CONNECTION_EXPERIENCE_INVARIANT: Final[str] = (
    "provider_connection_experience_guidance_without_provider_mutation_authority"
)

PHASE_1_PROVIDERS: Final[tuple[str, ...]] = (
    "GitHub",
    "Railway",
    "Vercel",
)

PHASE_2_PROVIDERS: Final[tuple[str, ...]] = (
    "AWS",
    "Azure",
    "GCP",
    "Kubernetes",
)

PROVIDER_CAPABILITY_UNLOCKS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "GitHub",
        (
            "Repository intelligence",
            "Delivery lifecycle",
            "Pull request workflows",
        ),
    ),
    (
        "Railway",
        (
            "Deployment visibility",
            "Monitoring visibility",
            "Rollback assessments",
        ),
    ),
    (
        "Vercel",
        (
            "Project visibility",
            "Deployment visibility",
            "Environment visibility",
        ),
    ),
)

PROVIDER_PERMISSION_REQUIREMENTS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("GitHub", ("repo:read", "workflow:read", "actions:read")),
    ("Railway", ("project:read", "service:read", "deployment:read")),
    ("Vercel", ("project:read", "deployment:read", "env:read")),
)

PROVIDER_SETUP_GUIDANCE: Final[tuple[tuple[str, str], ...]] = (
    ("GitHub", "Mission Control → Advanced settings → Credentials → GitHub token or OAuth app with repo and workflow read scopes."),
    ("Railway", "Mission Control → Advanced settings → Credentials → Railway API token with project and deployment read access."),
    ("Vercel", "Mission Control → Advanced settings → Credentials → Vercel API token or `vercel` CLI login for project visibility."),
)

HUMAN_PROVIDER_CONNECTION_DECISION_KINDS: Final[tuple[str, ...]] = (
    "provider_connection_decision_approve",
    "provider_connection_decision_hold",
    "provider_connection_decision_reject",
    "provider_connection_decision_defer",
)

PROVIDER_CONNECTION_EXPERIENCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "provider_connection_note",
    *HUMAN_PROVIDER_CONNECTION_DECISION_KINDS,
    "provider_connection_experience_record",
)

PROVIDER_CONNECTION_EXPERIENCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("guidance_not_mutation", "Provider connection guidance ≠ provider mutation authority."),
    ("compose_only", "Composes FIX 295 provider matrix and credential readiness without connecting providers."),
    ("manual_connection", "Providers are connected manually in Settings — never automatically."),
    ("no_secret_collection", "Never collect secrets in chat."),
    ("capability_unlocks", "Capability unlocks explain what becomes available after connection."),
    ("trust_explanation", "Trust explanation clarifies access scope and human approval boundaries."),
    ("phase_separation", "Phase 1 providers have connection flows; Phase 2 are PLANNED only."),
    ("human_review", "Provider connection review records decisions without provisioning."),
    ("readiness_evaluation", "Readiness evaluates credentials, permissions, scopes, and reachability state."),
    ("no_escalation", "Permission escalation and hidden provider access remain forbidden."),
)

FORBIDDEN_PROVIDER_CONNECTION_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("automatic_provider_provisioning", "Never auto-provisions provider connections."),
    ("automatic_credential_creation", "Never auto-creates credentials."),
    ("secret_collection_in_chat", "Never collects secrets in chat."),
    ("provider_mutation", "Never mutates providers during connection guidance."),
    ("permission_escalation", "Never escalates permissions automatically."),
    ("hidden_provider_access", "Never grants hidden provider access."),
)

PROVIDER_CONNECTION_EXPERIENCE_EXECUTABLE: Final[bool] = False

MAX_PROVIDER_CONNECTION_EXPERIENCE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_PROVIDER_CONNECTION_EXPERIENCE_RECORDS: Final[int] = 500
