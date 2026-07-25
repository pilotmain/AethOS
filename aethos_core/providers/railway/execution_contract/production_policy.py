# SPDX-License-Identifier: Apache-2.0
"""
FIX 117 — Production policy hardening layer (policy only; no live production mutations).

Centralizes production execution constraints: incident mode, deployment freeze,
blast-radius classification, operator quorum, shadow rollout, rollback escalation,
audit retention, and SLO verification requirements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import (
    classify_plan_risk,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
    ExecutionMode,
    extract_final_phrase_from_text,
    is_production_environment,
    is_rollback_blocked_environment,
    load_railway_execution_enablement_config,
    validate_final_phrase,
)
from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    list_confirmations,
    quorum_counts,
    record_confirmation,
)
from aethos_core.operations.mutations.risk import MutationRiskTier

EnvironmentTier = Literal["staging", "development", "production", "unknown"]
BlastRadiusClass = Literal["local", "service", "environment", "platform"]
RolloutMode = Literal["disabled", "shadow", "dry_run", "live"]
RollbackEscalationMode = Literal["manual_only", "blocked"]

PRODUCTION_QUORUM_CONFIRMATION_PHRASE = (
    "I confirm operator quorum for production Railway deployment."
)

_PRODUCTION_POLICY_RX = re.compile(r"\bshow\s+railway\s+production\s+policy\b", re.I)


@dataclass(frozen=True)
class RailwayProductionPolicyConfig:
    incident_mode: bool
    deployment_freeze: bool
    freeze_start_utc: str
    freeze_end_utc: str
    shadow_mode_required_for_production: bool
    forward_live_unlocked: bool
    operator_quorum_required: int
    require_second_confirmation: bool
    audit_retention_days: int
    slo_verification_required: bool
    autonomous_rollback_blocked: bool


@dataclass(frozen=True)
class RailwayProductionPolicyAssessment:
    environment_tier: EnvironmentTier
    blast_radius: BlastRadiusClass
    mutation_risk_tier: str
    incident_mode_active: bool
    deployment_freeze_active: bool
    shadow_mode_required: bool
    rollout_mode: RolloutMode
    forward_live_permitted: bool
    rollback_permitted: bool
    rollback_escalation: RollbackEscalationMode
    production_phrase_valid: bool
    quorum_confirmation_valid: bool
    quorum_required: int
    quorum_confirmations_recorded: int
    operator_quorum_satisfied: bool
    slo_verification_required: bool
    slo_verification_satisfied: bool
    audit_retention_days: int
    autonomous_rollback_blocked: bool
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment_tier": self.environment_tier,
            "blast_radius": self.blast_radius,
            "mutation_risk_tier": self.mutation_risk_tier,
            "incident_mode_active": self.incident_mode_active,
            "deployment_freeze_active": self.deployment_freeze_active,
            "shadow_mode_required": self.shadow_mode_required,
            "rollout_mode": self.rollout_mode,
            "forward_live_permitted": self.forward_live_permitted,
            "rollback_permitted": self.rollback_permitted,
            "rollback_escalation": self.rollback_escalation,
            "production_phrase_valid": self.production_phrase_valid,
            "quorum_confirmation_valid": self.quorum_confirmation_valid,
            "quorum_required": self.quorum_required,
            "quorum_confirmations_recorded": self.quorum_confirmations_recorded,
            "operator_quorum_satisfied": self.operator_quorum_satisfied,
            "slo_verification_required": self.slo_verification_required,
            "slo_verification_satisfied": self.slo_verification_satisfied,
            "audit_retention_days": self.audit_retention_days,
            "autonomous_rollback_blocked": self.autonomous_rollback_blocked,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def is_railway_production_policy_intent(text: str) -> bool:
    return bool(_PRODUCTION_POLICY_RX.search((text or "").strip()))


def is_production_shadow_execution_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "railway_production_shadow_execution", False))


def load_railway_production_policy_config() -> RailwayProductionPolicyConfig:
    from aethos_core.config import get_settings

    settings = get_settings()
    quorum = int(getattr(settings, "railway_production_operator_quorum", 2) or 2)
    return RailwayProductionPolicyConfig(
        incident_mode=bool(getattr(settings, "railway_production_incident_mode", False)),
        deployment_freeze=bool(getattr(settings, "railway_production_deployment_freeze", False)),
        freeze_start_utc=str(getattr(settings, "railway_production_freeze_start_utc", "") or ""),
        freeze_end_utc=str(getattr(settings, "railway_production_freeze_end_utc", "") or ""),
        shadow_mode_required_for_production=bool(
            getattr(settings, "railway_production_shadow_mode_required", True)
        ),
        forward_live_unlocked=bool(
            getattr(settings, "railway_production_forward_live_unlocked", False)
        ),
        operator_quorum_required=max(1, quorum),
        require_second_confirmation=bool(
            getattr(settings, "railway_production_require_second_confirmation", True)
        ),
        audit_retention_days=int(
            getattr(settings, "railway_production_audit_retention_days", 90) or 90
        ),
        slo_verification_required=bool(
            getattr(settings, "railway_production_slo_verification_required", True)
        ),
        autonomous_rollback_blocked=True,
    )


def resolve_environment_tier(environment: str) -> EnvironmentTier:
    env = (environment or "").strip().lower()
    if env in {"production", "prod", "live"}:
        return "production"
    if env in {"staging", "stage", "preview"}:
        return "staging"
    if env in {"development", "dev"}:
        return "development"
    return "unknown"


def classify_blast_radius(*, environment: str, phase: str = "") -> BlastRadiusClass:
    tier = resolve_environment_tier(environment)
    _ = phase
    if tier == "production":
        return "platform"
    if tier in {"staging", "development"}:
        return "environment"
    return "service"


def _parse_utc(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def is_deployment_freeze_active(*, now: datetime | None = None) -> bool:
    cfg = load_railway_production_policy_config()
    if cfg.incident_mode:
        return True
    if cfg.deployment_freeze:
        return True
    start = _parse_utc(cfg.freeze_start_utc)
    end = _parse_utc(cfg.freeze_end_utc)
    if start is None and end is None:
        return False
    current = now or datetime.now(timezone.utc)
    if start and current < start:
        return False
    if end and current > end:
        return False
    if start or end:
        return True
    return False


def extract_production_quorum_phrase_from_text(text: str) -> str:
    raw = (text or "").strip()
    if PRODUCTION_QUORUM_CONFIRMATION_PHRASE in raw:
        return PRODUCTION_QUORUM_CONFIRMATION_PHRASE
    return ""


def validate_production_quorum_phrase(*, phrase: str) -> bool:
    return bool(phrase) and phrase == PRODUCTION_QUORUM_CONFIRMATION_PHRASE


def record_production_confirmations_from_text(
    *,
    execution_id: str,
    user_text: str,
    session_id: str = "",
) -> list[dict[str, Any]]:
    """Record operator confirmations when exact phrases appear (idempotent)."""
    results: list[dict[str, Any]] = []
    if not execution_id.strip():
        return results
    phrase = extract_final_phrase_from_text(user_text)
    if phrase == PRODUCTION_FINAL_PHRASE:
        results.append(
            record_confirmation(
                execution_id=execution_id,
                kind="production_final_phrase",
                session_id=session_id,
            )
        )
    quorum = extract_production_quorum_phrase_from_text(user_text)
    if quorum:
        results.append(
            record_confirmation(
                execution_id=execution_id,
                kind="production_quorum_confirmation",
                session_id=session_id,
            )
        )
    return results


def _resolve_rollout_mode(*, tier: EnvironmentTier, execution_mode: ExecutionMode) -> RolloutMode:
    if tier != "production":
        if execution_mode == "enabled":
            return "live"
        if execution_mode == "dry_run":
            return "dry_run"
        return "disabled"
    cfg = load_railway_production_policy_config()
    if cfg.shadow_mode_required_for_production or not cfg.forward_live_unlocked:
        if execution_mode == "dry_run":
            return "shadow"
        return "shadow" if execution_mode == "enabled" else "disabled"
    if execution_mode == "enabled":
        return "live"
    if execution_mode == "dry_run":
        return "dry_run"
    return "disabled"


def _slo_verification_satisfied(*, execution_id: str, journal: dict[str, Any] | None) -> bool:
    journal = journal or {}
    if journal.get("production_slo_verification_passed") is True:
        return True
    from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
        load_shadow_journal,
    )
    from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
        load_verification_receipt,
    )

    shadow = load_shadow_journal(execution_id=execution_id) if execution_id else None
    if shadow and shadow.get("production_slo_verification_passed") is True:
        return True
    pv_receipt = load_verification_receipt(execution_id=execution_id) if execution_id else None
    if pv_receipt and (pv_receipt.get("assessment") or {}).get("verification_passed"):
        return True
    if not execution_id:
        return False
    from aethos_core.providers.railway.execution_contract.execution_contract_models import (
        VERIFY_RUNTIME_PHASE,
    )
    from aethos_core.providers.railway.execution_contract.execution_receipts import (
        find_phase_receipt,
    )
    from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
        verification_readonly_recorded,
    )

    receipt = find_phase_receipt(execution_id=execution_id, phase=VERIFY_RUNTIME_PHASE)
    return verification_readonly_recorded(receipt)


def assess_railway_production_policy(
    *,
    plan: dict[str, Any] | None,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
) -> RailwayProductionPolicyAssessment:
    plan = plan or {}
    journal = journal or {}
    cfg = load_railway_production_policy_config()
    enablement_cfg = load_railway_execution_enablement_config()
    environment = str(plan.get("environment") or "").strip().lower()
    tier = resolve_environment_tier(environment)
    is_production = tier == "production"
    blast = classify_blast_radius(environment=environment)
    risk = classify_plan_risk(environment=environment)
    risk_label = risk.value if isinstance(risk, MutationRiskTier) else str(risk)

    phrase = extract_final_phrase_from_text(user_text)
    production_phrase_valid = (
        validate_final_phrase(phrase=phrase, is_production=True) if phrase else False
    )
    quorum_phrase = extract_production_quorum_phrase_from_text(user_text)
    quorum_confirmation_valid = validate_production_quorum_phrase(phrase=quorum_phrase)

    if execution_id and user_text.strip():
        record_production_confirmations_from_text(
            execution_id=execution_id,
            user_text=user_text,
            session_id=str(journal.get("session_id") or ""),
        )

    counts = quorum_counts(execution_id=execution_id) if execution_id else {}
    quorum_recorded = int(counts.get("total_distinct") or 0)
    quorum_required = cfg.operator_quorum_required if is_production else 0

    operator_quorum_satisfied = True
    if is_production and cfg.require_second_confirmation:
        operator_quorum_satisfied = (
            counts.get("production_final_phrase", 0) >= 1
            and counts.get("production_quorum_confirmation", 0) >= 1
            and quorum_recorded >= quorum_required
        )
    elif is_production and quorum_required > 1:
        operator_quorum_satisfied = quorum_recorded >= quorum_required

    freeze_active = is_deployment_freeze_active()
    shadow_required = is_production and cfg.shadow_mode_required_for_production
    rollout = _resolve_rollout_mode(tier=tier, execution_mode=enablement_cfg.mode)

    slo_required = is_production and cfg.slo_verification_required
    slo_satisfied = (not slo_required) or _slo_verification_satisfied(
        execution_id=execution_id,
        journal=journal,
    )

    rollback_permitted = False
    if is_production or is_rollback_blocked_environment(environment):
        rollback_permitted = False
    rollback_escalation: RollbackEscalationMode = "manual_only"

    blockers: list[str] = []
    messages: list[str] = []

    if is_production:
        if cfg.incident_mode:
            blockers.append("production_incident_mode_active")
            messages.append(
                "Production incident mode is active — all production execution is frozen."
            )
        if freeze_active and "production_incident_mode_active" not in blockers:
            blockers.append("production_deployment_freeze_active")
            messages.append("Production deployment freeze window is active.")
        if not enablement_cfg.allow_production:
            blockers.append("production_not_allowlisted")
            messages.append("Production is not enabled in greenfield allowlists.")
        if not cfg.forward_live_unlocked:
            blockers.append("production_forward_live_locked")
            messages.append(
                "Production forward live execution remains locked (FIX 117). "
                "Use shadow/dry-run rehearsal only."
            )
        if shadow_required and enablement_cfg.mode == "enabled":
            blockers.append("production_shadow_mode_required")
            messages.append(
                "Production targets require shadow mode — live enabled execution is not permitted."
            )
        if cfg.require_second_confirmation and not operator_quorum_satisfied:
            blockers.append("production_operator_quorum_unsatisfied")
            messages.append(
                "Production requires operator quorum: production final phrase plus "
                "quorum confirmation phrase, recorded on the execution journal."
            )
        elif quorum_required > 1 and not operator_quorum_satisfied:
            blockers.append("production_operator_quorum_unsatisfied")
            messages.append(
                f"Production requires {quorum_required} distinct operator confirmations."
            )
        if slo_required and not slo_satisfied:
            blockers.append("production_slo_verification_required")
            messages.append(
                "Production runtime SLO verification must pass before live execution."
            )
        if cfg.autonomous_rollback_blocked:
            blockers.append("production_autonomous_rollback_blocked")
            messages.append(
                "Autonomous production rollback is prohibited — escalation is manual-only."
            )

    forward_live_permitted = is_production and not blockers
    if is_production and enablement_cfg.mode != "enabled":
        forward_live_permitted = False
    if not is_production:
        forward_live_permitted = True

    return RailwayProductionPolicyAssessment(
        environment_tier=tier,
        blast_radius=blast,
        mutation_risk_tier=risk_label,
        incident_mode_active=cfg.incident_mode,
        deployment_freeze_active=freeze_active,
        shadow_mode_required=shadow_required,
        rollout_mode=rollout,
        forward_live_permitted=forward_live_permitted,
        rollback_permitted=rollback_permitted,
        rollback_escalation=rollback_escalation,
        production_phrase_valid=production_phrase_valid,
        quorum_confirmation_valid=quorum_confirmation_valid,
        quorum_required=quorum_required,
        quorum_confirmations_recorded=quorum_recorded,
        operator_quorum_satisfied=operator_quorum_satisfied,
        slo_verification_required=slo_required,
        slo_verification_satisfied=slo_satisfied,
        audit_retention_days=cfg.audit_retention_days,
        autonomous_rollback_blocked=cfg.autonomous_rollback_blocked,
        blockers=blockers,
        messages=messages,
    )


def production_policy_forward_block_errors(
    *,
    environment: str,
    phase: str,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> list[str]:
    code = forward_live_mutation_blocked_reason(
        environment=environment,
        phase=phase,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
        plan=plan,
    )
    if not code:
        return []
    return [code, f"Production policy blocks forward live phase `{phase}` (FIX 117)."]


def forward_live_mutation_blocked_reason(
    *,
    environment: str,
    phase: str,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> str | None:
    """Return a stable blocker code when forward live mutation must not run."""
    if not is_production_environment(environment):
        return None
    assessment = assess_railway_production_policy(
        plan=plan or {"environment": environment},
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
    )
    if assessment.forward_live_permitted:
        return None
    return assessment.blockers[0] if assessment.blockers else "production_forward_live_locked"

