# SPDX-License-Identifier: Apache-2.0
"""Blast-radius analysis for governed mutations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BlastRadiusAnalysis:
    scope: str
    reversibility: str
    dependency_impact: list[str]
    expected_downtime: str
    production_impact: bool
    context_signals: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "scope": self.scope,
            "reversibility": self.reversibility,
            "dependency_impact": self.dependency_impact,
            "expected_downtime": self.expected_downtime,
            "production_impact": self.production_impact,
        }
        if self.context_signals:
            out["context_signals"] = self.context_signals
        return out


def _context_signals(
    *,
    provider: str,
    operation_type: str,
    target_name: str | None,
    target_status: str,
    context: dict[str, Any] | None,
) -> list[str]:
    ctx = context or {}
    signals: list[str] = []
    if target_status == "resolved":
        signals.append("target_resolved")
    if provider == "railway":
        if ctx.get("production_environment") or operation_type in ("restart", "redeploy"):
            signals.append("railway_production_environment")
        if operation_type == "restart":
            signals.append("service_availability_impact")
        if ctx.get("recent_deploy_failures"):
            signals.append("recent_deploy_failures")
        if ctx.get("public_service"):
            signals.append("public_service_exposure")
    if provider == "github":
        if ctx.get("protected_branch") or operation_type == "workflow_rerun":
            signals.append("ci_pipeline_trigger")
        if ctx.get("deploy_workflow"):
            signals.append("deploy_workflow_linked")
        if operation_type == "workflow_rerun":
            signals.append("downstream_deploy_gates")
    if provider == "vercel":
        if ctx.get("production_alias") or operation_type == "redeploy":
            signals.append("vercel_production_alias")
        if ctx.get("public_domain"):
            signals.append("public_production_domain")
        if operation_type == "redeploy":
            signals.append("edge_traffic_impact")
    if target_name and any(k in (target_name or "").lower() for k in ("prod", "production", "global")):
        signals.append("production_target_name_hint")
    return signals


def analyze_blast_radius(
    *,
    provider: str,
    operation_type: str,
    target_name: str | None,
    target_status: str = "unknown",
    context: dict[str, Any] | None = None,
) -> BlastRadiusAnalysis:
    ctx = context or {}
    signals = _context_signals(
        provider=provider,
        operation_type=operation_type,
        target_name=target_name,
        target_status=target_status,
        context=ctx,
    )
    scope = "production" if target_status == "resolved" or "production_target_name_hint" in signals else "unknown"
    if provider == "railway" and "railway_production_environment" in signals:
        scope = "production"
    if provider == "vercel" and "vercel_production_alias" in signals:
        scope = "production"
    production_impact = scope == "production" or "public_service_exposure" in signals

    if operation_type == "workflow_rerun":
        return BlastRadiusAnalysis(
            scope="staging" if not ctx.get("deploy_workflow") else "production",
            reversibility="reversible",
            dependency_impact=["CI pipeline", "downstream deploy gates"],
            expected_downtime="none",
            production_impact=bool(ctx.get("deploy_workflow")),
            context_signals=signals,
        )

    if operation_type in ("create_branch", "create_pr"):
        return BlastRadiusAnalysis(
            scope="local",
            reversibility="reversible",
            dependency_impact=["git history", "PR review queue"],
            expected_downtime="none",
            production_impact=False,
            context_signals=signals,
        )

    if operation_type == "set_env_var":
        return BlastRadiusAnalysis(
            scope=scope,
            reversibility="partially_reversible",
            dependency_impact=["runtime config", "auth tokens", "feature flags"],
            expected_downtime="minimal",
            production_impact=production_impact,
            context_signals=signals,
        )

    if operation_type == "restart":
        return BlastRadiusAnalysis(
            scope=scope,
            reversibility="reversible",
            dependency_impact=["service availability", "active sessions"],
            expected_downtime="minimal",
            production_impact=production_impact,
            context_signals=signals,
        )

    if operation_type == "redeploy":
        downtime = "moderate" if production_impact else "minimal"
        return BlastRadiusAnalysis(
            scope=scope,
            reversibility="reversible",
            dependency_impact=["deployment state", "linked services", "shared cache"],
            expected_downtime=downtime,
            production_impact=production_impact,
            context_signals=signals,
        )

    if provider == "local":
        return BlastRadiusAnalysis(
            scope="local",
            reversibility="partially_reversible",
            dependency_impact=["working tree", "local git state"],
            expected_downtime="none",
            production_impact=False,
            context_signals=signals,
        )

    return BlastRadiusAnalysis(
        scope=scope,
        reversibility="unknown",
        dependency_impact=["provider-managed resources"],
        expected_downtime="unknown",
        production_impact=production_impact,
        context_signals=signals,
    )
