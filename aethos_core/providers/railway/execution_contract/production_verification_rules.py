# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production verification rules (multi-signal, rollback, escalation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_policy import (
    load_railway_production_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_verification_contract import (
    REQUIRED_SIGNAL_FAMILIES,
    STRONG_SIGNAL_IDS,
    WEAK_ONLY_SIGNAL_IDS,
    IncidentEscalationLevel,
    RollbackRecommendation,
)
from aethos_core.providers.railway.execution_contract.production_verification_evidence import (
    ProductionVerificationEvidenceBundle,
)


@dataclass(frozen=True)
class ProductionVerificationRulesConfig:
    min_strong_signals: int
    min_signal_families: int
    reject_weak_only_pass: bool
    require_deployment_log_evidence: bool


@dataclass(frozen=True)
class ProductionVerificationAssessment:
    verification_passed: bool
    strong_signal_count: int
    medium_signal_count: int
    weak_signal_count: int
    families_present: tuple[str, ...]
    single_weak_signal_only: bool
    rollback_recommendation: RollbackRecommendation
    incident_escalation: IncidentEscalationLevel
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_passed": self.verification_passed,
            "strong_signal_count": self.strong_signal_count,
            "medium_signal_count": self.medium_signal_count,
            "weak_signal_count": self.weak_signal_count,
            "families_present": list(self.families_present),
            "single_weak_signal_only": self.single_weak_signal_only,
            "rollback_recommendation": self.rollback_recommendation,
            "incident_escalation": self.incident_escalation,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def load_production_verification_rules_config() -> ProductionVerificationRulesConfig:
    from aethos_core.config import get_settings

    settings = get_settings()
    return ProductionVerificationRulesConfig(
        min_strong_signals=int(
            getattr(settings, "railway_production_verification_min_strong_signals", 2) or 2
        ),
        min_signal_families=int(
            getattr(settings, "railway_production_verification_min_signal_families", 3) or 3
        ),
        reject_weak_only_pass=bool(
            getattr(settings, "railway_production_verification_reject_weak_only", True)
        ),
        require_deployment_log_evidence=bool(
            getattr(settings, "railway_production_verification_require_log_evidence", True)
        ),
    )


def assess_production_verification_evidence(
    bundle: ProductionVerificationEvidenceBundle,
    *,
    incident_mode_active: bool = False,
) -> ProductionVerificationAssessment:
    cfg = load_production_verification_rules_config()
    prod_cfg = load_railway_production_policy_config()

    strong = sum(1 for s in bundle.signals if s.strength == "strong" and s.passed)
    medium = sum(1 for s in bundle.signals if s.strength == "medium" and s.passed)
    weak = sum(1 for s in bundle.signals if s.strength == "weak")
    families = tuple(sorted({s.family for s in bundle.signals if s.passed}))
    passed_ids = {s.signal_id for s in bundle.signals if s.passed}

    weak_only = bool(passed_ids) and passed_ids.issubset(WEAK_ONLY_SIGNAL_IDS)
    single_weak = weak_only and len(passed_ids) == 1

    blockers: list[str] = []
    messages: list[str] = []

    if strong < cfg.min_strong_signals:
        blockers.append("insufficient_strong_signals")
        messages.append(
            f"Requires at least {cfg.min_strong_signals} strong passed signals; observed {strong}."
        )
    if len(families) < cfg.min_signal_families:
        blockers.append("insufficient_signal_families")
        messages.append(
            f"Requires evidence across {cfg.min_signal_families} families "
            f"({', '.join(REQUIRED_SIGNAL_FAMILIES)}); observed {', '.join(families) or 'none'}."
        )
    if cfg.reject_weak_only_pass and weak_only:
        blockers.append("weak_signal_only_rejected")
        messages.append("Verification cannot pass on a single weak signal.")
    if cfg.require_deployment_log_evidence and not bundle.deployment_logs.success_pattern_matched:
        blockers.append("deployment_log_evidence_missing")
        messages.append("Deployment log success pattern evidence is required.")
    if not bundle.health_check.multi_probe_agreement:
        blockers.append("health_check_confidence_insufficient")
        messages.append("Health check confidence requires multi-probe agreement.")

    verification_passed = not blockers

    rollback: RollbackRecommendation = "none"
    escalation: IncidentEscalationLevel = "none"

    if incident_mode_active or prod_cfg.incident_mode:
        rollback = "advise_incident_escalation"
        escalation = "incident_commander"
        verification_passed = False
        if "production_incident_mode_active" not in blockers:
            blockers.append("production_incident_mode_active")
    elif not verification_passed:
        if single_weak or weak_only:
            rollback = "advise_shadow_rollback_rehearsal"
            escalation = "operator_review"
        else:
            rollback = "advise_manual_review"
            escalation = "operator_review"
        messages.append(
            "No autonomous production rollback — use manual escalation or shadow rollback rehearsal."
        )
    elif strong >= cfg.min_strong_signals and not weak_only:
        messages.append("Multi-signal production verification policy satisfied (shadow/read-only).")

    _ = STRONG_SIGNAL_IDS  # contract reference for certification

    return ProductionVerificationAssessment(
        verification_passed=verification_passed,
        strong_signal_count=strong,
        medium_signal_count=medium,
        weak_signal_count=weak,
        families_present=families,
        single_weak_signal_only=single_weak,
        rollback_recommendation=rollback,
        incident_escalation=escalation,
        blockers=blockers,
        messages=messages,
    )
