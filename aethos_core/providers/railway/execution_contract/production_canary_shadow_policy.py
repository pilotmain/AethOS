# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — canary + shadow deployment policy framework (governed, no live traffic mutation)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    AUTOMATIC_PROMOTION_PERMITTED,
    AUTOMATIC_TRAFFIC_MUTATION_PERMITTED,
    AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED,
    CANARY_TRAFFIC_POLICY,
    DEFAULT_MAX_CANARY_PERCENT,
    SHADOW_TRAFFIC_POLICY,
    SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
    DeploymentStrategy,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_store import (
    append_policy_event,
    load_policy_record,
    save_policy_record,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    load_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    load_verification_receipt,
)

_POLICY_RX = re.compile(r"\bshow\s+railway\s+production\s+canary\s+shadow\s+policy\b", re.I)
_SHADOW_TRAFFIC_RX = re.compile(r"\bshow\s+railway\s+production\s+shadow\s+traffic\s+policy\b", re.I)
_CANARY_HEALTH_RX = re.compile(r"\bshow\s+railway\s+production\s+canary\s+health\s+evidence\b", re.I)
_PERCENT_RX = re.compile(
    r"\bshow\s+railway\s+production\s+rollout\s+percentage\s+governance\b",
    re.I,
)
_SYNTHETIC_RX = re.compile(
    r"\brecord\s+railway\s+production\s+synthetic\s+verification\s+traffic\b",
    re.I,
)
_ROLLBACK_REC_RX = re.compile(
    r"\bshow\s+railway\s+production\s+canary\s+rollback\s+recommendation\b",
    re.I,
)
_SEGMENTATION_RX = re.compile(
    r"\bshow\s+railway\s+production\s+traffic\s+segmentation\b",
    re.I,
)


@dataclass(frozen=True)
class CanaryHealthEvidence:
    error_rate: float
    synthetic_requests_recorded: int
    health_passed: bool
    promotion_pause_triggered: bool
    detail: str


@dataclass(frozen=True)
class DeploymentStrategyPolicyAssessment:
    execution_id: str
    deployment_strategy: DeploymentStrategy
    current_rollout_stage: str
    shadow_traffic_policy: dict[str, str]
    canary_traffic_policy: dict[str, str]
    max_canary_percent: int
    governed_canary_percent: int
    traffic_mutation_boundary: str
    autonomous_deployment_permitted: bool
    automatic_promotion_permitted: bool
    synthetic_verification_recorded: bool
    canary_health: CanaryHealthEvidence
    blast_radius_rollback_recommendation: str
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "deployment_strategy": self.deployment_strategy,
            "current_rollout_stage": self.current_rollout_stage,
            "shadow_traffic_policy": dict(self.shadow_traffic_policy),
            "canary_traffic_policy": dict(self.canary_traffic_policy),
            "max_canary_percent": self.max_canary_percent,
            "governed_canary_percent": self.governed_canary_percent,
            "traffic_mutation_boundary": self.traffic_mutation_boundary,
            "autonomous_deployment_permitted": self.autonomous_deployment_permitted,
            "automatic_promotion_permitted": self.automatic_promotion_permitted,
            "synthetic_verification_recorded": self.synthetic_verification_recorded,
            "canary_health": {
                "error_rate": self.canary_health.error_rate,
                "synthetic_requests_recorded": self.canary_health.synthetic_requests_recorded,
                "health_passed": self.canary_health.health_passed,
                "promotion_pause_triggered": self.canary_health.promotion_pause_triggered,
                "detail": self.canary_health.detail,
            },
            "blast_radius_rollback_recommendation": self.blast_radius_rollback_recommendation,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def is_production_canary_shadow_policy_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _POLICY_RX.search(raw)
        or _SHADOW_TRAFFIC_RX.search(raw)
        or _CANARY_HEALTH_RX.search(raw)
        or _PERCENT_RX.search(raw)
        or _SYNTHETIC_RX.search(raw)
        or _ROLLBACK_REC_RX.search(raw)
        or _SEGMENTATION_RX.search(raw)
    )


def extract_synthetic_verification_phrase(text: str) -> bool:
    return SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE in (text or "")


def load_canary_shadow_policy_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "railway_production_canary_shadow_policy_enabled", True)),
        "max_canary_percent": int(
            getattr(settings, "railway_production_max_canary_percent", DEFAULT_MAX_CANARY_PERCENT) or 5
        ),
        "promotion_pause_error_rate_threshold": float(
            getattr(settings, "railway_production_canary_promotion_pause_error_rate", 0.05) or 0.05
        ),
        "require_synthetic_verification_traffic": bool(
            getattr(settings, "railway_production_require_synthetic_verification_traffic", True)
        ),
        "shadow_traffic_mirror_simulation": bool(
            getattr(settings, "railway_production_shadow_traffic_mirror_simulation", True)
        ),
    }


def _resolve_deployment_strategy(*, rollout_stage: str) -> DeploymentStrategy:
    if rollout_stage in ("", "shadow"):
        return "shadow_only"
    if rollout_stage == "canary":
        return "shadow_then_canary"
    return "canary_governed"


def _governed_canary_percent(*, stage: str, max_percent: int) -> int:
    if stage in ("", "shadow"):
        return 0
    if stage == "canary":
        return min(max_percent, 5)
    if stage == "staged_rollout":
        return min(max_percent, 10)
    if stage == "full_rollout":
        return min(max_percent, 25)
    return 0


def _evaluate_canary_health(record: dict[str, Any], *, cfg: dict[str, Any]) -> CanaryHealthEvidence:
    synthetic = list(record.get("synthetic_verification_runs") or [])
    error_rate = float(record.get("simulated_error_rate") or 0.0)
    threshold = float(cfg["promotion_pause_error_rate_threshold"])
    pause = error_rate >= threshold
    passed = len(synthetic) > 0 and not pause
    return CanaryHealthEvidence(
        error_rate=error_rate,
        synthetic_requests_recorded=len(synthetic),
        health_passed=passed,
        promotion_pause_triggered=pause,
        detail=(
            "Canary health evaluated from synthetic verification traffic only (no real prod mutation)."
        ),
    )


def _blast_radius_rollback_recommendation(
    *,
    stage: str,
    health: CanaryHealthEvidence,
) -> str:
    if health.promotion_pause_triggered:
        if stage in ("canary", "staged_rollout"):
            return "advise_blast_radius_service_rollback_rehearsal"
        return "advise_blast_radius_platform_escalation"
    if not health.health_passed:
        return "advise_manual_review"
    return "none"


def get_or_create_policy_record(
    *,
    execution_id: str,
    session_id: str = "",
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = load_policy_record(execution_id=execution_id)
    if existing:
        return existing
    rollout = load_rollout_journal(execution_id=execution_id) or {}
    stage = str(rollout.get("current_stage") or "shadow")
    cfg = load_canary_shadow_policy_config()
    record = {
        "execution_id": execution_id,
        "session_id": session_id,
        "deployment_strategy": _resolve_deployment_strategy(rollout_stage=stage),
        "traffic_mutation_boundary": "synthetic_only",
        "max_canary_percent": cfg["max_canary_percent"],
        "governed_canary_percent": _governed_canary_percent(stage=stage, max_percent=cfg["max_canary_percent"]),
        "traffic_segments": _build_traffic_segments(stage=stage, cfg=cfg),
        "synthetic_verification_runs": [],
        "simulated_error_rate": 0.0,
        "policy_events": [],
        "environment": str((plan or {}).get("environment") or ""),
    }
    return save_policy_record(record)


def _build_traffic_segments(*, stage: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = [
        {
            "kind": "synthetic_verification",
            "percent": 100,
            "real_infra_mutation": False,
            "detail": "Synthetic probes only",
        },
    ]
    if cfg["shadow_traffic_mirror_simulation"] and stage in ("", "shadow"):
        segments.append(
            {
                "kind": "shadow_mirror_simulated",
                "percent": 0,
                "real_infra_mutation": False,
                "detail": "Shadow mirror simulated — 0% real production traffic",
            }
        )
    if stage in ("canary", "staged_rollout", "full_rollout"):
        pct = _governed_canary_percent(stage=stage, max_percent=cfg["max_canary_percent"])
        segments.append(
            {
                "kind": "canary_slice_simulated",
                "percent": pct,
                "real_infra_mutation": False,
                "detail": f"Governed canary slice {pct}% (simulation boundary)",
            }
        )
    return segments


def assess_canary_shadow_deployment_policy(
    *,
    execution_id: str,
    plan: dict[str, Any] | None = None,
    session_id: str = "",
) -> DeploymentStrategyPolicyAssessment:
    cfg = load_canary_shadow_policy_config()
    blockers: list[str] = []
    messages: list[str] = []

    if not cfg["enabled"]:
        blockers.append("canary_shadow_policy_disabled")

    record = get_or_create_policy_record(
        execution_id=execution_id,
        session_id=session_id,
        plan=plan,
    )
    rollout = load_rollout_journal(execution_id=execution_id) or {}
    stage = str(rollout.get("current_stage") or "shadow")
    strategy = _resolve_deployment_strategy(rollout_stage=stage)
    max_pct = int(cfg["max_canary_percent"])
    gov_pct = _governed_canary_percent(stage=stage, max_percent=max_pct)

    record["deployment_strategy"] = strategy
    record["governed_canary_percent"] = gov_pct
    record["traffic_segments"] = _build_traffic_segments(stage=stage, cfg=cfg)
    record = save_policy_record(record)

    health = _evaluate_canary_health(record, cfg=cfg)
    rollback_rec = _blast_radius_rollback_recommendation(stage=stage, health=health)

    shadow = load_shadow_journal(execution_id=execution_id) or {}
    verification = load_verification_receipt(execution_id=execution_id) or {}

    if strategy != "shadow_only" and cfg["require_synthetic_verification_traffic"]:
        if not record.get("synthetic_verification_runs"):
            blockers.append("synthetic_verification_traffic_required")

    if stage in ("canary", "staged_rollout", "full_rollout") and not health.health_passed:
        blockers.append("canary_health_evidence_insufficient")

    if health.promotion_pause_triggered:
        blockers.append("promotion_pause_threshold_exceeded")
        messages.append(
            f"Promotion paused: simulated error rate {health.error_rate:.2%} >= "
            f"threshold {cfg['promotion_pause_error_rate_threshold']:.2%}."
        )

    if not shadow.get("forward_shadow_completed") and stage == "shadow":
        blockers.append("shadow_forward_required_for_shadow_policy")

    if not (verification.get("assessment") or {}).get("verification_passed"):
        if stage != "shadow":
            blockers.append("verification_evidence_required_for_canary_policy")

    blockers.append("autonomous_production_deployment_prohibited")
    blockers.append("automatic_traffic_mutation_prohibited")
    messages.append("Shadow = 0% real traffic rehearsal. Canary = governed % cap with synthetic verification only.")

    return DeploymentStrategyPolicyAssessment(
        execution_id=execution_id,
        deployment_strategy=strategy,
        current_rollout_stage=stage,
        shadow_traffic_policy=dict(SHADOW_TRAFFIC_POLICY),
        canary_traffic_policy=dict(CANARY_TRAFFIC_POLICY),
        max_canary_percent=max_pct,
        governed_canary_percent=gov_pct,
        traffic_mutation_boundary="synthetic_only",
        autonomous_deployment_permitted=AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED,
        automatic_promotion_permitted=AUTOMATIC_PROMOTION_PERMITTED,
        synthetic_verification_recorded=bool(record.get("synthetic_verification_runs")),
        canary_health=health,
        blast_radius_rollback_recommendation=rollback_rec,
        blockers=blockers,
        messages=messages,
    )


def policy_blockers_for_rollout_advance(
    *,
    execution_id: str,
    rollout_stage: str,
    plan: dict[str, Any] | None = None,
) -> list[str]:
    """Policy-based advancement blockers for FIX 121 rollout gate integration."""
    assessment = assess_canary_shadow_deployment_policy(
        execution_id=execution_id,
        plan=plan,
    )
    policy_blockers = [
        b
        for b in assessment.blockers
        if b
        not in {
            "autonomous_production_deployment_prohibited",
            "automatic_traffic_mutation_prohibited",
        }
    ]
    if rollout_stage == "canary" and "synthetic_verification_traffic_required" in policy_blockers:
        return policy_blockers
    if rollout_stage in ("canary", "staged_rollout", "full_rollout"):
        return policy_blockers
    if rollout_stage == "shadow":
        return [b for b in policy_blockers if b == "shadow_forward_required_for_shadow_policy"]
    return []


def record_synthetic_verification_traffic(
    *,
    execution_id: str,
    user_text: str,
    session_id: str = "",
    simulated_error_rate: float = 0.0,
) -> dict[str, Any]:
    record = get_or_create_policy_record(execution_id=execution_id, session_id=session_id)
    if not extract_synthetic_verification_phrase(user_text):
        return append_policy_event(
            record,
            action="synthetic_verification_rejected",
            detail="Exact synthetic verification phrase required.",
            session_id=session_id,
        )

    runs = list(record.get("synthetic_verification_runs") or [])
    runs.append(
        {
            "run_id": f"syn-{len(runs) + 1}",
            "segment_kind": "synthetic_verification",
            "requests_simulated": 100,
            "real_infra_mutation": False,
            "session_id": session_id,
        }
    )
    record["synthetic_verification_runs"] = runs
    record["simulated_error_rate"] = max(0.0, float(simulated_error_rate))
    record = save_policy_record(record)
    return append_policy_event(
        record,
        action="synthetic_verification_recorded",
        detail="Synthetic verification traffic recorded (simulation only).",
        session_id=session_id,
    )
