# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_311_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
    build_atlas_trader_trust_report_freeze,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
    build_nexora_trust_report_freeze,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
    build_payment_integration_readiness,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
    build_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
    AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
    EXECUTION_PERFORMED_FIX_311,
    FORBIDDEN_PUBLIC_EXPERIENCE_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_311,
    HUMAN_PUBLIC_EXPERIENCE_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_311,
    PROVIDER_MUTATION_AUTHORITY_FIX_311,
    PUBLIC_EXPERIENCE_DOMAINS,
    PUBLIC_PRODUCT_AUTHORITY_FIX_311,
    PUBLIC_PRODUCT_COMPOSES_EVIDENCE_ONLY_FIX_311,
    PUBLIC_PRODUCT_EXPERIENCE_FIX,
    PUBLIC_PRODUCT_EXPERIENCE_INVARIANT,
    PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION,
    TENANT_MUTATION_AUTHORITY_FIX_311,
    TRUST_MUTATION_AUTHORITY_FIX_311,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_evaluator import (
    classify_capabilities,
    summarize_trust_baseline,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_store import (
    has_public_experience_review_decision_approve,
    list_public_product_experience_records,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
    build_tenant_onboarding_activation,
)


@dataclass(frozen=True)
class PublicProductExperienceResult:
    ok: bool
    session_id: str
    public_product_experience: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _safe_build(name: str, builder, *, session_id: str) -> tuple[Any, bool]:
    try:
        result = builder(session_id=session_id)
        return result, bool(getattr(result, "ok", True))
    except Exception:
        return None, False


def _payload(result: Any, attr: str) -> dict[str, Any]:
    if not result:
        return {}
    value = getattr(result, attr, None)
    return value if isinstance(value, dict) else {}


def build_public_product_experience(*, session_id: str) -> PublicProductExperienceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_public_product_experience_records()

    capability, capability_ok = _safe_build("fix_295", build_autonomous_capability_registry, session_id=sid)
    runtime, runtime_ok = _safe_build(
        "fix_296", build_capability_registry_runtime_integration, session_id=sid
    )
    trust_186, trust_186_ok = _safe_build(
        "fix_186", build_dogfood_pilot_trust_report_freeze, session_id=sid
    )
    trust_192, trust_192_ok = _safe_build(
        "fix_192", build_pilotos_ui_trust_report_freeze, session_id=sid
    )
    trust_194, trust_194_ok = _safe_build(
        "fix_194", build_atlas_trader_trust_report_freeze, session_id=sid
    )
    trust_196, trust_196_ok = _safe_build("fix_196", build_nexora_trust_report_freeze, session_id=sid)
    onboarding, onboarding_ok = _safe_build("fix_301", build_tenant_onboarding_activation, session_id=sid)
    provider, provider_ok = _safe_build("fix_303", build_provider_connection_experience, session_id=sid)
    billing, billing_ok = _safe_build("fix_305", build_billing_entitlements_foundation, session_id=sid)
    payment, payment_ok = _safe_build("fix_308", build_payment_integration_readiness, session_id=sid)
    launch, launch_ok = _safe_build("fix_309", build_saas_launch_readiness_assessment, session_id=sid)

    capability_board = _payload(capability, "autonomous_capability_registry")
    capability_registry = (capability_board.get("sections") or {}).get("capability_registry", [{}])[0]
    capabilities = list(capability_registry.get("capabilities") or [])
    capability_buckets = classify_capabilities(capabilities)

    runtime_board = _payload(runtime, "capability_registry_runtime_integration")
    runtime_sections = runtime_board.get("sections") or {}

    trust_baselines = [
        summarize_trust_baseline(
            fix="FIX 186",
            label="Dogfood pilot trust baseline",
            payload=_payload(trust_186, "dogfood_pilot_trust_report_freeze"),
            ok=trust_186_ok,
        ),
        summarize_trust_baseline(
            fix="FIX 192",
            label="PilotOS UI trust baseline",
            payload=_payload(trust_192, "pilotos_ui_trust_report_freeze"),
            ok=trust_192_ok,
        ),
        summarize_trust_baseline(
            fix="FIX 194",
            label="Atlas Trader trust baseline",
            payload=_payload(trust_194, "atlas_trader_trust_report_freeze"),
            ok=trust_194_ok,
        ),
        summarize_trust_baseline(
            fix="FIX 196",
            label="Nexora trust baseline",
            payload=_payload(trust_196, "nexora_trust_report_freeze"),
            ok=trust_196_ok,
        ),
    ]

    launch_board = _payload(launch, "saas_launch_readiness_assessment")
    overall_launch_status = str(launch_board.get("overall_launch_status") or "UNKNOWN")
    launch_dashboard = (launch_board.get("sections") or {}).get("launch_readiness_dashboard", [{}])[0]
    launch_scores = launch_dashboard.get("domain_scores") or {}

    billing_sections = (_payload(billing, "billing_entitlements_foundation").get("sections") or {})
    plan_registry = (billing_sections.get("plan_registry") or [{}])[0]
    plans = list(plan_registry.get("plans") or [])
    entitlement_registry = (billing_sections.get("entitlement_registry") or [{}])[0]

    payment_sections = (_payload(payment, "payment_integration_readiness").get("sections") or {})
    upgrade_paths = (payment_sections.get("upgrade_path_registry") or [{}])[0]

    onboarding_sections = (_payload(onboarding, "tenant_onboarding_activation").get("sections") or {})
    provider_sections = (_payload(provider, "provider_connection_experience").get("sections") or {})

    public_landing_experience = [
        {
            "experience_id": "public-landing-experience",
            "headline": "AethOS is a governed platform for autonomous software delivery and operations.",
            "what_aethos_is": [
                "Multi-tenant platform with human-in-the-loop governance.",
                "Evidence-backed delivery, deployment, and operational intelligence.",
                "Self-aware capability registry with explicit authority boundaries.",
            ],
            "what_aethos_does": [
                "Plans, coordinates, and validates governed engineering workflows.",
                "Connects providers and channels with readiness-first onboarding.",
                "Explains trust, readiness, and operational proof transparently.",
            ],
            "governance_points": [
                "Humans approve high-impact actions — AethOS assesses and recommends.",
                "Trust is earned through pilot evidence, not self-declaration.",
                "Public experiences explain boundaries; they do not bypass governance.",
            ],
            "trust_boundaries": [
                "No automatic provider mutation from public surfaces.",
                "No trust mutation or hidden launch authority.",
                "No customer provisioning without human review.",
            ],
            "read_only": True,
        }
    ]

    capability_explorer = [
        {
            "explorer_id": "capability-explorer",
            "capability_count": len(capabilities),
            **capability_buckets,
            "authority_boundaries": [
                "Capability registry describes platform abilities — not execution authority.",
                "Runtime integration answers from evidence without capability authority.",
            ],
            "runtime_integration_ready": runtime_ok,
            "runtime_sections": list(runtime_sections.keys())[:8],
            "evidence_sources": ["FIX 295", "FIX 296"],
            "read_only": True,
        }
    ]

    trust_explorer = [
        {
            "explorer_id": "trust-explorer",
            "baselines": trust_baselines,
            "baseline_count": sum(1 for row in trust_baselines if row.get("available")),
            "operational_proof": [
                "Pilot trust report freezes compose audit evidence without re-execution.",
                "Trust recommendations are advisory — humans decide trust expansion.",
            ],
            "evidence_sources": ["FIX 186", "FIX 192", "FIX 194", "FIX 196"],
            "read_only": True,
        }
    ]

    guided_product_tour = [
        {
            "tour_id": "guided-product-tour",
            "steps": [
                {
                    "step_id": "platform",
                    "title": "Platform walkthrough",
                    "detail": "Multi-tenant foundation, onboarding, and administration visibility.",
                },
                {
                    "step_id": "governance",
                    "title": "Governance walkthrough",
                    "detail": "Approvals, trust boundaries, and human decision records.",
                },
                {
                    "step_id": "delivery",
                    "title": "Delivery lifecycle walkthrough",
                    "detail": "Merge, deploy, monitoring, and rollback lifecycles with evidence.",
                },
                {
                    "step_id": "intelligence",
                    "title": "Intelligence walkthrough",
                    "detail": "Capability registry, operational intelligence, and audit visibility.",
                },
            ],
            "read_only": True,
        }
    ]

    use_case_explorer = [
        {
            "explorer_id": "use-case-explorer",
            "use_cases": [
                {
                    "use_case_id": "software_delivery",
                    "title": "Software delivery",
                    "detail": "Governed engineering workflows from planning through merge.",
                },
                {
                    "use_case_id": "repository_intelligence",
                    "title": "Repository intelligence",
                    "detail": "Knowledge graph, diagnostics, and cross-repo intelligence.",
                },
                {
                    "use_case_id": "product_planning",
                    "title": "Product planning",
                    "detail": "Mission planning with human decision boards.",
                },
                {
                    "use_case_id": "operations",
                    "title": "Operations",
                    "detail": "Deploy, monitor, rollback, and operational truth surfaces.",
                },
                {
                    "use_case_id": "governance",
                    "title": "Governance",
                    "detail": "Approval coverage, trust baselines, and auditability.",
                },
            ],
            "read_only": True,
        }
    ]

    customer_journey_explorer = [
        {
            "explorer_id": "customer-journey-explorer",
            "paths": [
                {
                    "path_id": "new_customer",
                    "title": "New customer path",
                    "detail": "Discover product → review plans → start guided onboarding.",
                    "composed_from": ["FIX 301", "FIX 305"],
                },
                {
                    "path_id": "provider_connection",
                    "title": "Provider connection path",
                    "detail": "Review provider readiness → connect Phase 1 providers with guidance.",
                    "composed_from": ["FIX 303"],
                },
                {
                    "path_id": "first_governed_workflow",
                    "title": "First governed workflow",
                    "detail": "Complete onboarding → run first approval-gated workflow.",
                    "composed_from": ["FIX 301", "FIX 302"],
                },
                {
                    "path_id": "expansion",
                    "title": "Expansion path",
                    "detail": "Review entitlements → evaluate upgrade paths and launch readiness.",
                    "composed_from": ["FIX 305", "FIX 308", "FIX 309"],
                },
            ],
            "onboarding_ready": onboarding_ok,
            "provider_guidance_ready": provider_ok,
            "read_only": True,
        }
    ]

    plan_entitlement_explorer = [
        {
            "explorer_id": "plan-entitlement-explorer",
            "plans": plans,
            "plan_count": len(plans),
            "entitlements": entitlement_registry.get("entitlements") or [],
            "upgrade_paths": upgrade_paths.get("paths") or upgrade_paths.get("upgrade_paths") or [],
            "limits_visible": bool(entitlement_registry),
            "evidence_sources": ["FIX 305", "FIX 308"],
            "read_only": True,
        }
    ]

    public_readiness_explorer = [
        {
            "explorer_id": "public-readiness-explorer",
            "overall_launch_status": overall_launch_status,
            "readiness_categories": launch_scores,
            "public_limitations": [
                "Payment processing is modeled as readiness — not enabled publicly.",
                "Launch assessment does not declare launch — humans decide readiness.",
                "Limited beta may be justified before public launch.",
                "Some capabilities remain experimental or planned.",
            ],
            "launch_readiness_ready": launch_ok,
            "evidence_sources": ["FIX 309"],
            "read_only": True,
        }
    ]

    public_education_center = [
        {
            "center_id": "public-education-center",
            "faqs": [
                {
                    "question": "What can AethOS do?",
                    "answer": (
                        "Plan and coordinate governed engineering workflows, explain platform "
                        "capabilities from evidence, and guide onboarding, providers, and billing."
                    ),
                },
                {
                    "question": "What can't AethOS do?",
                    "answer": (
                        "Bypass governance, mutate trust, auto-provision customers, or execute "
                        "providers without human approval."
                    ),
                },
                {
                    "question": "How does governance work?",
                    "answer": (
                        "High-impact actions require human approval. AethOS assesses and recommends; "
                        "humans remain accountable."
                    ),
                },
                {
                    "question": "How do approvals work?",
                    "answer": (
                        "Approval inboxes and decision records track human approve/hold/reject/defer "
                        "without automatic execution."
                    ),
                },
            ],
            "onboarding_guidance_ready": onboarding_ok,
            "provider_guidance_ready": provider_ok,
            "capability_registry_ready": capability_ok,
            "evidence_sources": ["FIX 295", "FIX 301", "FIX 303"],
            "read_only": True,
        }
    ]

    domains_composed = sum(
        1
        for ok in (
            capability_ok,
            runtime_ok,
            trust_186_ok or trust_192_ok or trust_194_ok or trust_196_ok,
            onboarding_ok,
            provider_ok,
            billing_ok,
            payment_ok,
            launch_ok,
        )
        if ok
    )

    public_product_dashboard = [
        {
            "dashboard_id": "public-product-dashboard",
            "proven_capability_count": len(capability_buckets.get("proven") or []),
            "trust_baseline_count": sum(1 for row in trust_baselines if row.get("available")),
            "plan_count": len(plans),
            "overall_launch_status": overall_launch_status,
            "evidence_coverage": {
                "domains_composed": 10,
                "domains_total": 10,
                "fix_295_310_sources_composed": domains_composed,
            },
            "getting_started": [
                "Explore proven capabilities in the capability explorer.",
                "Review trust baselines and operational proof in the trust explorer.",
                "Follow the customer journey from onboarding to first governed workflow.",
                "Compare plans and entitlements before selecting a tier.",
            ],
            "automatic_onboarding_performed": False,
            "customer_provisioning_performed": False,
            "read_only": True,
        }
    ]

    sections = {
        "public_landing_experience": public_landing_experience,
        "capability_explorer": capability_explorer,
        "trust_explorer": trust_explorer,
        "guided_product_tour": guided_product_tour,
        "use_case_explorer": use_case_explorer,
        "customer_journey_explorer": customer_journey_explorer,
        "plan_entitlement_explorer": plan_entitlement_explorer,
        "public_readiness_explorer": public_readiness_explorer,
        "public_education_center": public_education_center,
        "public_product_dashboard": public_product_dashboard,
        "human_public_experience_review": [
            {
                "review_id": "human-public-experience-review",
                "decisions_supported": list(HUMAN_PUBLIC_EXPERIENCE_DECISION_KINDS),
                "public_experience_review_decision_approve": has_public_experience_review_decision_approve(
                    session_id=sid
                ),
                "public_product_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_public_experience_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PUBLIC_EXPERIENCE_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION,
        "fix": PUBLIC_PRODUCT_EXPERIENCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_311,
        "execution_performed": EXECUTION_PERFORMED_FIX_311,
        "public_product_compose_artifacts_only": PUBLIC_PRODUCT_COMPOSES_EVIDENCE_ONLY_FIX_311,
        "public_product_authority": PUBLIC_PRODUCT_AUTHORITY_FIX_311,
        "automatic_customer_onboarding_enabled": AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_311,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_311,
        "tenant_mutation_authority": TENANT_MUTATION_AUTHORITY_FIX_311,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_311,
        "invariant": PUBLIC_PRODUCT_EXPERIENCE_INVARIANT,
        "session_id": sid,
        "public_experience_domains": list(PUBLIC_EXPERIENCE_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "public_experience_review_decision_approve": has_public_experience_review_decision_approve(
            session_id=sid
        ),
        "fix_311_certification_requirements": list(FIX_311_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_295_through_310": True,
            "provider_execution_performed": False,
            "governance_bypass_performed": False,
            "tenant_mutation_performed": False,
            "customer_provisioning_performed": False,
            "automatic_onboarding_performed": False,
        },
    }

    return PublicProductExperienceResult(
        ok=True,
        session_id=sid,
        public_product_experience=payload,
        blockers=[],
        detail="Public product experience composed from evidence (experience ≠ platform authority).",
    )
