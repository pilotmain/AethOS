# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — autonomous capability registry & self-awareness contract."""

from __future__ import annotations

from typing import Final

AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_capability_registry_v1"
)
AUTONOMOUS_CAPABILITY_REGISTRY_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_autonomous_capability_registry_record_v1"
)
AUTONOMOUS_CAPABILITY_REGISTRY_FIX: Final[str] = "FIX 295"

MUTATION_PERFORMED_FIX_295: Final[bool] = False
EXECUTION_PERFORMED_FIX_295: Final[bool] = False
CAPABILITY_AUTHORITY_FIX_295: Final[bool] = False
SELF_AUTHORITY_GRANTING_ENABLED_FIX_295: Final[bool] = False
AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295: Final[bool] = False
TRUST_MUTATION_AUTHORITY_FIX_295: Final[bool] = False
REPOSITORY_MUTATION_AUTHORITY_FIX_295: Final[bool] = False
PROVIDER_MUTATION_AUTHORITY_FIX_295: Final[bool] = False
DEPLOYMENT_AUTHORITY_FIX_295: Final[bool] = False
ROLLBACK_AUTHORITY_FIX_295: Final[bool] = False
MERGE_AUTHORITY_FIX_295: Final[bool] = False
GATE_BYPASS_ENABLED_FIX_295: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_295: Final[bool] = False
AUTONOMOUS_CAPABILITY_REGISTRY_COMPOSES_EVIDENCE_ONLY_FIX_295: Final[bool] = True

AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID: Final[str] = (
    "mission_control_autonomous_capability_registry"
)
AUTONOMOUS_CAPABILITY_REGISTRY_ORIGIN: Final[str] = (
    "mission_control_autonomous_capability_registry"
)

AUTONOMOUS_CAPABILITY_REGISTRY_INVARIANT: Final[str] = (
    "autonomous_capability_registry_understands_platform_capabilities_without_capability_authority"
)

CAPABILITY_DOMAINS: Final[tuple[str, ...]] = (
    "governance",
    "delivery",
    "operations",
    "intelligence",
    "provider",
)

CAPABILITY_STATUSES: Final[tuple[str, ...]] = (
    "PLANNED",
    "EXPERIMENTAL",
    "IMPLEMENTED",
    "PROVEN",
    "CONDITIONALLY_TRUSTED",
    "OPERATIONAL",
    "DEPRECATED",
    "BLOCKED",
)

PROVIDER_CAPABILITIES: Final[tuple[str, ...]] = (
    "railway",
    "github",
    "vercel",
    "aws",
    "gcp",
    "azure",
    "kubernetes",
)

HUMAN_CAPABILITY_REVIEW_KINDS: Final[tuple[str, ...]] = (
    "human_capability_review_approve",
    "human_capability_review_hold",
    "human_capability_review_reject",
    "human_capability_review_defer",
)

AUTONOMOUS_CAPABILITY_REGISTRY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "capability_note",
    "capability_evidence_note",
    *HUMAN_CAPABILITY_REVIEW_KINDS,
    "autonomous_capability_registry_record",
)

PLATFORM_CAPABILITIES: Final[tuple[tuple[str, str, str, str, str], ...]] = (
    ("mission_control", "Mission Control", "governance", "FIX 170", "Governed operator console and routing"),
    ("mission_authorization", "Mission Authorization", "governance", "FIX 175", "Human-gated mission authorization"),
    ("human_decision_board", "Human Decision Board", "governance", "FIX 174", "Record-only human decision layer"),
    ("trust_systems", "Trust Systems", "governance", "FIX 186", "Repository trust baselines and freeze reports"),
    ("approval_systems", "Approval Systems", "governance", "FIX 134", "Governed approval inbox and lane admission"),
    ("lane_systems", "Lane Systems", "governance", "FIX 128", "Cross-lane operations and lane separation"),
    ("delivery_planning", "Delivery Planning", "delivery", "FIX 200", "Governed planning without auto-execution"),
    ("patch_generation", "Patch Generation", "delivery", "FIX 210", "Governed patch artifact generation"),
    ("delivery_verification", "Delivery Verification", "delivery", "FIX 220", "Verification receipts and evidence"),
    ("pr_creation", "PR Creation", "delivery", "FIX 125I", "Human-gated GitHub PR opening"),
    ("merge_lifecycle", "Merge Lifecycle", "delivery", "FIX 230", "Governed merge lifecycle coordination"),
    ("deploy_lifecycle", "Deploy Lifecycle", "delivery", "FIX 230", "Governed deploy lifecycle coordination"),
    ("monitoring_lifecycle", "Monitoring Lifecycle", "operations", "FIX 230", "Governed monitoring lifecycle"),
    ("rollback_lifecycle", "Rollback Lifecycle", "operations", "FIX 230", "Governed rollback lifecycle"),
    ("incident_investigation", "Incident Investigation", "operations", "FIX 230", "Operational investigation receipts"),
    ("repository_intelligence", "Repository Intelligence", "intelligence", "FIX 240", "Repository knowledge graph"),
    ("portfolio_intelligence", "Portfolio Intelligence", "intelligence", "FIX 260", "Multi-repository engineering intelligence"),
    ("product_evolution", "Product Evolution Intelligence", "intelligence", "FIX 261", "Cross-repository evolution intelligence"),
    ("product_stewardship", "Product Stewardship", "intelligence", "FIX 270", "Autonomous product stewardship"),
    ("lifecycle_management", "Application Lifecycle Management", "intelligence", "FIX 280", "Unified lifecycle model"),
    ("business_operating_system", "Business Operating System", "intelligence", "FIX 290", "Unified business operating model"),
    ("capability_registry", "Capability Registry & Self-Awareness", "intelligence", "FIX 295", "Live platform capability graph"),
    ("enterprise_operating_system", "Enterprise Operating System", "intelligence", "FIX 300", "Planned enterprise intelligence layer"),
    ("provider_railway", "Railway Provider", "provider", "FIX 102", "Railway readonly and governed mutation paths"),
    ("provider_github", "GitHub Provider", "provider", "FIX 125", "GitHub readonly and governed delivery paths"),
    ("provider_vercel", "Vercel Provider", "provider", "FIX 125", "Vercel readonly operational checks"),
    ("provider_aws", "AWS Provider", "provider", "PLANNED", "AWS integration planned"),
    ("provider_gcp", "GCP Provider", "provider", "PLANNED", "GCP integration planned"),
    ("provider_azure", "Azure Provider", "provider", "PLANNED", "Azure integration planned"),
    ("provider_kubernetes", "Kubernetes Provider", "provider", "PLANNED", "Kubernetes integration planned"),
)

AUTONOMOUS_CAPABILITY_REGISTRY_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("awareness_not_authority", "Capability awareness ≠ capability authority."),
    ("compose_only", "Composes FIX certifications, trust baselines, and provider readiness without re-execution."),
    ("evidence_derived", "Capability status derives from certifications, pilots, and operational receipts."),
    ("no_self_modification", "Capability registry never self-modifies platform capabilities."),
    ("no_authority_escalation", "Capability registry never grants itself authority."),
    ("no_automatic_promotion", "Capability promotion requires human review — never automatic."),
    ("no_trust_mutation", "Trust baselines are read-only capability inputs."),
    ("live_self_awareness", "Self-awareness answers derive from live evidence, not static provider text."),
    ("drift_detection", "Capability drift detection compares certified, surfaced, and documented capabilities."),
    ("human_review", "Human capability review records decisions without execution."),
)

FORBIDDEN_CAPABILITY_REGISTRY_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("self_modifying_capabilities", "Capability registry never self-modifies capabilities."),
    ("authority_escalation", "Capability registry never escalates authority."),
    ("automatic_trust_changes", "Capability registry never changes trust automatically."),
    ("automatic_capability_promotion", "Capability registry never auto-promotes capabilities."),
    ("execution", "Capability registry never executes operational changes."),
    ("repository_mutation", "Capability registry never mutates repositories."),
    ("provider_mutation", "Capability registry never mutates providers."),
    ("gate_bypass", "Capability registry never bypasses frozen governance gates."),
)

AUTONOMOUS_CAPABILITY_REGISTRY_EXECUTABLE: Final[bool] = False

MAX_AUTONOMOUS_CAPABILITY_REGISTRY_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_AUTONOMOUS_CAPABILITY_REGISTRY_RECORDS: Final[int] = 500
