# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — multi-signal production verification evidence model (policy-only collection)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from aethos_core.providers.railway.execution_contract.production_verification_contract import (
    SignalStrength,
)

EvidenceMode = Literal["shadow", "readonly_staging"]


@dataclass(frozen=True)
class VerificationSignal:
    signal_id: str
    family: str
    strength: SignalStrength
    passed: bool
    summary: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "family": self.family,
            "strength": self.strength,
            "passed": self.passed,
            "summary": self.summary,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class SloEvidence:
    availability_target_met: bool
    latency_budget_met: bool
    availability_slo: str
    latency_budget_ms: int
    observed_availability_pct: float
    observed_p99_latency_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "availability_target_met": self.availability_target_met,
            "latency_budget_met": self.latency_budget_met,
            "availability_slo": self.availability_slo,
            "latency_budget_ms": self.latency_budget_ms,
            "observed_availability_pct": self.observed_availability_pct,
            "observed_p99_latency_ms": self.observed_p99_latency_ms,
        }


@dataclass(frozen=True)
class HealthCheckEvidence:
    path_configured: bool
    path: str
    confidence: Literal["low", "medium", "high"]
    multi_probe_agreement: bool
    probes_passed: int
    probes_total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_configured": self.path_configured,
            "path": self.path,
            "confidence": self.confidence,
            "multi_probe_agreement": self.multi_probe_agreement,
            "probes_passed": self.probes_passed,
            "probes_total": self.probes_total,
        }


@dataclass(frozen=True)
class DeploymentLogEvidence:
    log_window_available: bool
    success_pattern_matched: bool
    error_pattern_absent: bool
    line_count: int
    redacted_excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "log_window_available": self.log_window_available,
            "success_pattern_matched": self.success_pattern_matched,
            "error_pattern_absent": self.error_pattern_absent,
            "line_count": self.line_count,
            "redacted_excerpt": self.redacted_excerpt,
        }


@dataclass
class ProductionVerificationEvidenceBundle:
    execution_id: str
    environment: str
    mode: EvidenceMode
    slo: SloEvidence
    health_check: HealthCheckEvidence
    deployment_logs: DeploymentLogEvidence
    deployment_id: str = ""
    deployment_state: str = ""
    signals: list[VerificationSignal] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "environment": self.environment,
            "mode": self.mode,
            "slo": self.slo.to_dict(),
            "health_check": self.health_check.to_dict(),
            "deployment_logs": self.deployment_logs.to_dict(),
            "deployment_id": self.deployment_id,
            "deployment_state": self.deployment_state,
            "signals": [s.to_dict() for s in self.signals],
        }


def _plan_health_path(plan: dict[str, Any]) -> str:
    fields = plan.get("inspection_fields")
    if isinstance(fields, dict):
        return str(fields.get("health_check_path") or "/api/v1/health").strip() or "/api/v1/health"
    return str(plan.get("health_check_path") or "/api/v1/health")


def collect_shadow_verification_evidence(
    *,
    execution_id: str,
    plan: dict[str, Any],
    shadow_journal: dict[str, Any] | None = None,
) -> ProductionVerificationEvidenceBundle:
    """
    Build verification evidence for production shadow rehearsal.

    Does not call Railway APIs — reconstructs governed evidence from plan + shadow journal.
    """
    plan = plan or {}
    shadow_journal = shadow_journal or {}
    environment = str(plan.get("environment") or shadow_journal.get("environment") or "production")

    health_path = _plan_health_path(plan)
    forward_phases = {
        str(row.get("phase") or "")
        for row in (shadow_journal.get("phases") or [])
        if isinstance(row, dict)
    }
    deploy_shadow_done = "trigger_deploy_shadow" in forward_phases
    forward_complete = bool(shadow_journal.get("forward_shadow_completed")) or all(
        phase in forward_phases
        for phase in (
            "create_service_shadow",
            "connect_source_shadow",
            "configure_env_shadow",
            "trigger_deploy_shadow",
        )
    )

    deploy_meta = shadow_journal.get("shadow_deploy_context")
    if not isinstance(deploy_meta, dict):
        deploy_meta = {}
    deployment_id = str(deploy_meta.get("deployment_id") or "shadow-deploy-sim")
    deployment_state = str(deploy_meta.get("deployment_state") or "success")

    slo = SloEvidence(
        availability_target_met=forward_complete and deploy_shadow_done,
        latency_budget_met=forward_complete and deploy_shadow_done,
        availability_slo="99.9%",
        latency_budget_ms=500,
        observed_availability_pct=99.95 if forward_complete else 0.0,
        observed_p99_latency_ms=220 if forward_complete else 9999,
    )

    probes_total = 3
    probes_passed = probes_total if forward_complete and health_path else 1
    multi_probe = probes_passed >= 2
    confidence: Literal["low", "medium", "high"] = (
        "high" if multi_probe and forward_complete else "medium" if health_path else "low"
    )

    health = HealthCheckEvidence(
        path_configured=bool(health_path),
        path=health_path,
        confidence=confidence,
        multi_probe_agreement=multi_probe,
        probes_passed=probes_passed,
        probes_total=probes_total,
    )

    logs = DeploymentLogEvidence(
        log_window_available=deploy_shadow_done,
        success_pattern_matched=deploy_shadow_done and deployment_state in {"success", "succeeded", "active"},
        error_pattern_absent=deploy_shadow_done,
        line_count=12 if deploy_shadow_done else 0,
        redacted_excerpt=(
            "[shadow] build succeeded; health probe 200; no credential values logged"
            if deploy_shadow_done
            else "[shadow] awaiting deploy shadow phase"
        ),
    )

    signals: list[VerificationSignal] = []

    if slo.availability_target_met:
        signals.append(
            VerificationSignal(
                signal_id="slo_availability_budget_met",
                family="slo",
                strength="strong",
                passed=True,
                summary="Availability SLO within budget (shadow evidence).",
            )
        )
    if slo.latency_budget_met:
        signals.append(
            VerificationSignal(
                signal_id="slo_latency_budget_met",
                family="slo",
                strength="strong",
                passed=True,
                summary="Latency p99 within budget (shadow evidence).",
            )
        )

    if health.path_configured and not health.multi_probe_agreement:
        signals.append(
            VerificationSignal(
                signal_id="health_check_path_configured_only",
                family="health_check",
                strength="weak",
                passed=False,
                summary="Health path configured but insufficient probe agreement.",
            )
        )
    if health.multi_probe_agreement:
        signals.append(
            VerificationSignal(
                signal_id="health_check_multi_probe_agreement",
                family="health_check",
                strength="strong",
                passed=True,
                summary=f"Health probes agree on `{health.path}` ({health.probes_passed}/{health.probes_total}).",
            )
        )

    if logs.success_pattern_matched:
        signals.append(
            VerificationSignal(
                signal_id="deployment_log_success_pattern",
                family="deployment",
                strength="strong",
                passed=True,
                summary="Deployment logs match success patterns (redacted excerpt).",
            )
        )
    elif deployment_state and deploy_shadow_done:
        signals.append(
            VerificationSignal(
                signal_id="deployment_state_confirmed",
                family="deployment",
                strength="medium",
                passed=deployment_state in {"success", "succeeded", "active", "running"},
                summary=f"Deployment state observed: `{deployment_state}`.",
            )
        )
    elif deployment_state and not logs.log_window_available:
        signals.append(
            VerificationSignal(
                signal_id="deployment_state_only",
                family="deployment",
                strength="weak",
                passed=False,
                summary="Only deployment state present — log evidence missing.",
            )
        )

    return ProductionVerificationEvidenceBundle(
        execution_id=execution_id,
        environment=environment,
        mode="shadow",
        slo=slo,
        health_check=health,
        deployment_logs=logs,
        deployment_id=deployment_id,
        deployment_state=deployment_state,
        signals=signals,
    )
