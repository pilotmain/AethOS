# SPDX-License-Identifier: Apache-2.0
"""Operational agent roles — governed task roles, not autonomous personalities."""

from __future__ import annotations

from typing import Any


def run_operational_pipeline(
    *,
    provider: str,
    service_name: str,
    project_name: str | None = None,
    environment: str | None = None,
    phase: str = "diagnose",
    logs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Lightweight multi-role pipeline: collect → diagnose → plan → verify."""
    evidence = _role_evidence_collector(provider=provider, service_name=service_name, logs=logs)
    diagnosis = _role_failure_diagnoser(provider=provider, evidence=evidence)
    fix_plan = _role_fix_planner(provider=provider, diagnosis=diagnosis, target_name=service_name)
    verification = _role_verifier(provider=provider, phase=phase, evidence=evidence)
    return {
        "ok": True,
        "provider": provider,
        "service_name": service_name,
        "project_name": project_name,
        "environment": environment,
        "phase": phase,
        "evidence": evidence,
        "diagnosis": diagnosis,
        "fix_plan": fix_plan,
        "verification": verification,
        "roles": ["evidence_collector", "failure_diagnoser", "fix_planner", "verifier"],
    }


def _role_evidence_collector(
    *,
    provider: str,
    service_name: str,
    logs: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    collected = list(logs or [])
    if provider == "railway" and not collected:
        from aethos_core.providers.railway.cli_executor import railway_logs

        collected = list((railway_logs(service_name=service_name).get("logs") or [])[-50:])
    return {"provider": provider, "service_name": service_name, "logs": collected}


def _role_failure_diagnoser(*, provider: str, evidence: dict[str, Any]) -> dict[str, Any]:
    logs = evidence.get("logs") or []
    if provider == "railway":
        from aethos_core.provider_diagnosis.railway import diagnose_railway_runtime

        return diagnose_railway_runtime(logs=logs, health_summary="degraded")
    return {"ok": False, "summary": "Diagnosis unavailable for provider."}


def _role_fix_planner(*, provider: str, diagnosis: dict[str, Any], target_name: str) -> dict[str, Any]:
    if provider == "railway":
        from aethos_core.provider_diagnosis.railway import propose_railway_fix

        return propose_railway_fix(diagnosis=diagnosis, target_name=target_name)
    return {"ok": False, "summary": "Fix planning unavailable.", "requires_approval": True}


def _role_verifier(*, provider: str, phase: str, evidence: dict[str, Any]) -> dict[str, Any]:
    if phase == "verify":
        return {"status": "pending_verification", "confidence": "bounded", "provider": provider}
    return {"status": "not_run", "confidence": "bounded", "provider": provider, "log_count": len(evidence.get("logs") or [])}
