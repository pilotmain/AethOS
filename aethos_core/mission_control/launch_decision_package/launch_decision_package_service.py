# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_315_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315,
    AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315,
    AUTOMATIC_LAUNCH_ENABLED_FIX_315,
    EXECUTION_PERFORMED_FIX_315,
    FORBIDDEN_LAUNCH_DECISION_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_315,
    HUMAN_LAUNCH_DECISION_KINDS,
    LAUNCH_DECISION_AUTHORITY_FIX_315,
    LAUNCH_DECISION_PACKAGE_COMPOSES_EVIDENCE_ONLY_FIX_315,
    LAUNCH_DECISION_PACKAGE_DOMAINS,
    LAUNCH_DECISION_PACKAGE_FIX,
    LAUNCH_DECISION_PACKAGE_INVARIANT,
    LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION,
    LAUNCH_RECOMMENDATION_PACKAGE_VALUES,
    MUTATION_PERFORMED_FIX_315,
    PILOT_EXECUTION_PERFORMED_FIX_315,
    TRUST_MUTATION_AUTHORITY_FIX_315,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_evaluator import (
    bucket_risks_by_level,
    categorize_blockers,
    categorize_capabilities,
    derive_launch_recommendation_package,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_store import (
    has_launch_decision_approve,
    list_launch_decision_package_records,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
    build_public_launch_readiness_freeze,
)


@dataclass(frozen=True)
class LaunchDecisionPackageResult:
    ok: bool
    session_id: str
    launch_decision_package: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _section(freeze: dict[str, Any], key: str) -> dict[str, Any]:
    sections = freeze.get("sections") or {}
    rows = sections.get(key) or [{}]
    return rows[0] if rows else {}


def build_launch_decision_package(*, session_id: str) -> LaunchDecisionPackageResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_launch_decision_package_records()
    packaged_at = _exported_at()

    freeze_result = build_public_launch_readiness_freeze(session_id=sid)
    freeze = freeze_result.public_launch_readiness_freeze
    freeze_sections = freeze.get("sections") or {}

    dashboard_freeze = _section(freeze, "launch_readiness_freeze_dashboard")
    capability_freeze = _section(freeze, "launch_capability_baseline")
    trust_freeze = _section(freeze, "launch_trust_baseline_summary")
    operational_freeze = _section(freeze, "launch_operational_baseline")
    customer_freeze = _section(freeze, "launch_customer_baseline")
    product_freeze = _section(freeze, "launch_product_baseline")
    risk_freeze = _section(freeze, "launch_risk_freeze")
    blocker_freeze = _section(freeze, "launch_blocker_freeze")
    recommendation_freeze = _section(freeze, "launch_recommendation_freeze")

    freeze_recommendation = str(freeze.get("launch_recommendation_freeze") or "NOT_READY")
    overall_launch_status = str(
        recommendation_freeze.get("overall_launch_status")
        or product_freeze.get("overall_launch_status")
        or "UNKNOWN"
    )
    ops_recommendation = str(recommendation_freeze.get("operations_recommendation") or "BLOCK_LAUNCH")
    beta_recommendation = str(recommendation_freeze.get("beta_recommendation") or "DO_NOT_LAUNCH")

    ops_risks = list(risk_freeze.get("risks") or [])
    risk_buckets = bucket_risks_by_level(ops_risks)
    critical_risk_count = len(risk_buckets["critical"])

    frozen_blockers = list(blocker_freeze.get("blockers") or [])
    blocker_categories = categorize_blockers(
        blockers=frozen_blockers,
        overall_launch_status=overall_launch_status,
    )
    all_blockers = [str(row.get("detail") or "") for row in frozen_blockers if row.get("detail")]

    platform_healthy = bool(operational_freeze.get("platform_healthy"))
    recommendation = derive_launch_recommendation_package(
        freeze_recommendation=freeze_recommendation,
        ops_recommendation=ops_recommendation,
        beta_recommendation=beta_recommendation,
        blocker_count=len(frozen_blockers),
        critical_risk_count=critical_risk_count,
        platform_healthy=platform_healthy,
    )

    proven_items = list(dashboard_freeze.get("proven_items") or [])
    unproven_items = list(dashboard_freeze.get("unproven_items") or [])

    proven_caps = list(capability_freeze.get("proven_capabilities") or [])
    cap_categories = categorize_capabilities(proven_caps)
    if not cap_categories["proven"] and not cap_categories["operational"]:
        cap_categories = categorize_capabilities(
            [
                {"name": item, "status": "PROVEN"}
                for item in proven_items
                if "capabilities proven" in item.lower()
            ]
        )

    trust_rows = list(trust_freeze.get("baselines") or [])
    trust_baseline_count = int(trust_freeze.get("baseline_count") or 0)

    launch_executive_summary = [
        {
            "summary_id": "launch-executive-summary",
            "platform_summary": (
                f"Platform {'healthy' if platform_healthy else 'needs attention'} — "
                f"delivery/deploy/monitoring/recovery from FIX 200–230"
            ),
            "readiness_summary": (
                f"Overall launch status: {overall_launch_status}. "
                f"Open blockers: {len(blocker_categories['open'])}."
            ),
            "trust_summary": (
                f"{trust_baseline_count} trust baselines frozen from FIX 186–196 via FIX 314."
            ),
            "recommendation_summary": (
                f"Evidence supports **{recommendation}** — humans must approve any launch path."
            ),
            "evidence_sources": ["FIX 314"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_capability_summary = [
        {
            "summary_id": "launch-capability-summary",
            "proven": cap_categories["proven"][:12],
            "operational": cap_categories["operational"][:12],
            "experimental": cap_categories["experimental"][:12],
            "planned": cap_categories["planned"][:12],
            "proven_count": len(cap_categories["proven"]) or capability_freeze.get("proven_count", 0),
            "operational_count": len(cap_categories["operational"]),
            "experimental_count": len(cap_categories["experimental"]),
            "planned_count": len(cap_categories["planned"]) or capability_freeze.get("unproven_count", 0),
            "runtime_integration_ready": capability_freeze.get("runtime_integration_ready", False),
            "evidence_sources": ["FIX 295", "FIX 296", "FIX 314"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_trust_evidence_summary = [
        {
            "summary_id": "launch-trust-evidence-summary",
            "trust_baselines": trust_rows,
            "baseline_count": trust_baseline_count,
            "pilot_evidence": [
                row for row in trust_rows if row.get("available") and row.get("fix") in {"FIX 186", "FIX 192"}
            ],
            "operational_evidence": [
                row for row in trust_rows if row.get("available") and row.get("fix") in {"FIX 194", "FIX 196"}
            ],
            "evidence_sources": ["FIX 186", "FIX 192", "FIX 194", "FIX 196", "FIX 314"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_operational_summary = [
        {
            "summary_id": "launch-operational-summary",
            "delivery_readiness": operational_freeze.get("delivery_health", False),
            "deploy_readiness": operational_freeze.get("deploy_health", False),
            "monitoring_readiness": operational_freeze.get("monitoring_health", False),
            "recovery_readiness": operational_freeze.get("recovery_health", False),
            "platform_healthy": platform_healthy,
            "operations_recommendation": ops_recommendation,
            "evidence_sources": ["FIX 200-230", "FIX 313", "FIX 314"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_customer_summary = [
        {
            "summary_id": "launch-customer-summary",
            "customer_readiness": customer_freeze.get("customer_support_ready", False),
            "onboarding_readiness": product_freeze.get("public_experience_ready", False),
            "beta_readiness": customer_freeze.get("beta_program_ready", False),
            "healthy_count": customer_freeze.get("healthy_count", 0),
            "at_risk_count": customer_freeze.get("at_risk_count", 0),
            "beta_participants": customer_freeze.get("beta_participants", 0),
            "evidence_sources": ["FIX 310", "FIX 311", "FIX 312"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_risk_summary = [
        {
            "summary_id": "launch-risk-summary",
            "critical": risk_buckets["critical"],
            "high": risk_buckets["high"],
            "medium": risk_buckets["medium"],
            "low": risk_buckets["low"],
            "critical_count": len(risk_buckets["critical"]),
            "high_count": len(risk_buckets["high"]),
            "medium_count": len(risk_buckets["medium"]),
            "low_count": len(risk_buckets["low"]),
            "evidence_sources": ["FIX 309", "FIX 313", "FIX 314"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_blocker_summary = [
        {
            "summary_id": "launch-blocker-summary",
            "open": blocker_categories["open"],
            "resolved": blocker_categories["resolved"],
            "conditional": blocker_categories["conditional"],
            "open_count": len(blocker_categories["open"]),
            "resolved_count": len(blocker_categories["resolved"]),
            "conditional_count": len(blocker_categories["conditional"]),
            "evidence_sources": ["FIX 309", "FIX 313", "FIX 314"],
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    launch_recommendation_package = [
        {
            "package_id": "launch-recommendation-package",
            "recommendation": recommendation,
            "freeze_recommendation": freeze_recommendation,
            "rationale": (
                "Derived from FIX 314 frozen baseline, FIX 313 operations, and FIX 312 beta — "
                "not launch approval or execution."
            ),
            "decision_options": list(LAUNCH_RECOMMENDATION_PACKAGE_VALUES),
            "launch_approval_performed": False,
            "read_only": True,
        }
    ]

    session_records = [
        row for row in records if not sid or str(row.get("session_id") or sid) == sid
    ]
    launch_decision_registry = [
        {
            "registry_id": "launch-decision-registry",
            "records": session_records[-20:],
            "record_count": len(session_records),
            "decisions_supported": list(HUMAN_LAUNCH_DECISION_KINDS),
            "launch_decision_approve": has_launch_decision_approve(session_id=sid),
            "launch_decision_authority": False,
            "read_only": True,
        }
    ]

    launch_decision_dashboard = [
        {
            "dashboard_id": "launch-decision-dashboard",
            "launch_recommendation_package": recommendation,
            "overall_launch_status": overall_launch_status,
            "open_blocker_count": len(blocker_categories["open"]),
            "critical_risk_count": critical_risk_count,
            "trust_baseline_count": trust_baseline_count,
            "platform_healthy": platform_healthy,
            "proven_items": proven_items,
            "unproven_items": unproven_items,
            "decision_options": list(LAUNCH_RECOMMENDATION_PACKAGE_VALUES),
            "launch_approval_performed": False,
            "packaged_at": packaged_at,
            "read_only": True,
        }
    ]

    sections = {
        "launch_executive_summary": launch_executive_summary,
        "launch_capability_summary": launch_capability_summary,
        "launch_trust_evidence_summary": launch_trust_evidence_summary,
        "launch_operational_summary": launch_operational_summary,
        "launch_customer_summary": launch_customer_summary,
        "launch_risk_summary": launch_risk_summary,
        "launch_blocker_summary": launch_blocker_summary,
        "launch_recommendation_package": launch_recommendation_package,
        "launch_decision_registry": launch_decision_registry,
        "launch_decision_dashboard": launch_decision_dashboard,
        "forbidden_launch_decision_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_LAUNCH_DECISION_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION,
        "fix": LAUNCH_DECISION_PACKAGE_FIX,
        "exported_at": packaged_at,
        "packaged_at": packaged_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_315,
        "execution_performed": EXECUTION_PERFORMED_FIX_315,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_315,
        "launch_decision_package_compose_artifacts_only": LAUNCH_DECISION_PACKAGE_COMPOSES_EVIDENCE_ONLY_FIX_315,
        "launch_decision_authority": LAUNCH_DECISION_AUTHORITY_FIX_315,
        "automatic_launch_approval_enabled": AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_315,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_315,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_315,
        "invariant": LAUNCH_DECISION_PACKAGE_INVARIANT,
        "session_id": sid,
        "launch_decision_package_domains": list(LAUNCH_DECISION_PACKAGE_DOMAINS),
        "launch_recommendation_package": recommendation,
        "sections": sections,
        "operator_record_count": len(records),
        "launch_decision_approve": has_launch_decision_approve(session_id=sid),
        "fix_315_certification_requirements": list(FIX_315_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_186_through_314": True,
            "pilot_execution_performed": False,
            "launch_approval_performed": False,
            "launch_execution_performed": False,
            "trust_mutation_performed": False,
            "customer_provisioning_performed": False,
            "beta_expansion_performed": False,
        },
    }

    return LaunchDecisionPackageResult(
        ok=True,
        session_id=sid,
        launch_decision_package=payload,
        blockers=all_blockers,
        detail="Launch decision package composed from FIX 314 evidence (package ≠ launch decision).",
    )
