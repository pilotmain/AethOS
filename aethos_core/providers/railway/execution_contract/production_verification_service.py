# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production runtime verification orchestration (no live production mutations)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
    is_production_environment,
    load_railway_production_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_verification_contract import (
    PRODUCTION_VERIFICATION_RECEIPT_PHASE,
    PRODUCTION_VERIFICATION_SHADOW_PHASE,
)
from aethos_core.providers.railway.execution_contract.production_verification_evidence import (
    ProductionVerificationEvidenceBundle,
    collect_shadow_verification_evidence,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
    save_verification_receipt,
)
from aethos_core.providers.railway.execution_contract.production_verification_rules import (
    ProductionVerificationAssessment,
    assess_production_verification_evidence,
    load_production_verification_rules_config,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
    save_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    record_shadow_receipt,
)


@dataclass
class ProductionVerificationResult:
    evidence: ProductionVerificationEvidenceBundle
    assessment: ProductionVerificationAssessment
    receipt: dict[str, Any]
    journal: dict[str, Any] = field(default_factory=dict)
    detail: str = ""

    @property
    def verification_passed(self) -> bool:
        return self.assessment.verification_passed


def assess_production_verification_readiness(
    *,
    plan: dict[str, Any] | None,
    execution_id: str = "",
    shadow_journal: dict[str, Any] | None = None,
    orchestrating_forward: bool = False,
) -> dict[str, Any]:
    plan = plan or {}
    shadow_journal = shadow_journal or load_shadow_journal(execution_id=execution_id) or {}
    environment = str(plan.get("environment") or "")
    blockers: list[str] = []
    if not is_production_environment(environment):
        blockers.append("not_production_environment")
    if not execution_id:
        blockers.append("execution_id_missing")
    if not orchestrating_forward and not shadow_journal.get("forward_shadow_completed"):
        blockers.append("forward_shadow_incomplete")
    policy = assess_railway_production_policy(plan=plan, execution_id=execution_id, journal=shadow_journal)
    if policy.incident_mode_active:
        blockers.append("production_incident_mode_active")
    return {
        "ready": not blockers,
        "blockers": blockers,
        "slo_verification_required": policy.slo_verification_required,
    }


def run_production_shadow_runtime_verification(
    *,
    execution_id: str,
    plan: dict[str, Any],
    shadow_journal: dict[str, Any],
    user_text: str = "",
    orchestrating_forward: bool = False,
) -> ProductionVerificationResult:
    """
    Execute verify_runtime_shadow with multi-signal evidence assessment.

    Never imports live mutation executors or readonly production Railway adapters.
    """
    _ = user_text
    readiness = assess_production_verification_readiness(
        plan=plan,
        execution_id=execution_id,
        shadow_journal=shadow_journal,
        orchestrating_forward=orchestrating_forward,
    )
    policy_cfg = load_railway_production_policy_config()
    if not readiness["ready"]:
        bundle = collect_shadow_verification_evidence(
            execution_id=execution_id,
            plan=plan,
            shadow_journal=shadow_journal,
        )
        assessment = assess_production_verification_evidence(
            bundle,
            incident_mode_active=policy_cfg.incident_mode,
        )
        receipt = save_verification_receipt(
            {
                "execution_id": execution_id,
                "phase": PRODUCTION_VERIFICATION_RECEIPT_PHASE,
                "status": "verification_blocked",
                "evidence": bundle.to_dict(),
                "assessment": assessment.to_dict(),
                "mutation_performed": False,
            }
        )
        return ProductionVerificationResult(
            evidence=bundle,
            assessment=assessment,
            receipt=receipt,
            journal=shadow_journal,
            detail="Production verification blocked — readiness not satisfied.",
        )

    existing = load_verification_receipt(execution_id=execution_id)
    if existing and (existing.get("assessment") or {}).get("verification_passed"):
        bundle = collect_shadow_verification_evidence(
            execution_id=execution_id,
            plan=plan,
            shadow_journal=shadow_journal,
        )
        prior = existing.get("assessment") or {}
        assessment = assess_production_verification_evidence(
            bundle,
            incident_mode_active=policy_cfg.incident_mode,
        )
        if prior.get("verification_passed"):
            assessment = ProductionVerificationAssessment(
                verification_passed=True,
                strong_signal_count=int(prior.get("strong_signal_count") or 0),
                medium_signal_count=int(prior.get("medium_signal_count") or 0),
                weak_signal_count=int(prior.get("weak_signal_count") or 0),
                families_present=tuple(prior.get("families_present") or []),
                single_weak_signal_only=False,
                rollback_recommendation="none",
                incident_escalation="none",
                messages=["Idempotent replay of production verification receipt."],
            )
        return ProductionVerificationResult(
            evidence=bundle,
            assessment=assessment,
            receipt=existing,
            journal=shadow_journal,
            detail="Production verification idempotent replay.",
        )

    bundle = collect_shadow_verification_evidence(
        execution_id=execution_id,
        plan=plan,
        shadow_journal=shadow_journal,
    )
    assessment = assess_production_verification_evidence(
        bundle,
        incident_mode_active=policy_cfg.incident_mode,
    )

    receipt = save_verification_receipt(
        {
            "execution_id": execution_id,
            "phase": PRODUCTION_VERIFICATION_RECEIPT_PHASE,
            "status": "verification_passed" if assessment.verification_passed else "verification_failed",
            "evidence": bundle.to_dict(),
            "assessment": assessment.to_dict(),
            "rollback_recommendation": assessment.rollback_recommendation,
            "incident_escalation": assessment.incident_escalation,
            "rules": load_production_verification_rules_config().__dict__,
        }
    )

    if not assessment.verification_passed:
        from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
            create_or_refresh_escalation_from_verification,
        )

        create_or_refresh_escalation_from_verification(
            execution_id=execution_id,
            plan=plan,
            session_id=str(shadow_journal.get("session_id") or ""),
        )
        from aethos_core.providers.railway.execution_contract.production_incident_command import (
            sync_incident_from_verification_failure,
        )

        sync_incident_from_verification_failure(
            execution_id=execution_id,
            plan=plan,
            session_id=str(shadow_journal.get("session_id") or ""),
        )

    record_shadow_receipt(
        execution_id=execution_id,
        phase=PRODUCTION_VERIFICATION_SHADOW_PHASE,
        status="shadow_verification_success" if assessment.verification_passed else "shadow_verification_failed",
        detail=receipt.get("status", ""),
        policy_checks_passed=assessment.verification_passed,
        policy_blockers=assessment.blockers,
    )

    shadow_journal["production_verification"] = {
        "passed": assessment.verification_passed,
        "evidence": bundle.to_dict(),
        "assessment": assessment.to_dict(),
        "receipt_id": receipt.get("receipt_id"),
    }
    shadow_journal["production_slo_verification_passed"] = assessment.verification_passed
    shadow_journal = save_shadow_journal(shadow_journal)

    detail = (
        "Production shadow verification passed (multi-signal)."
        if assessment.verification_passed
        else "Production shadow verification failed — see evidence report."
    )
    return ProductionVerificationResult(
        evidence=bundle,
        assessment=assessment,
        receipt=receipt,
        journal=shadow_journal,
        detail=detail,
    )
