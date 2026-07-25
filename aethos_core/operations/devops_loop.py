# SPDX-License-Identifier: Apache-2.0
"""End-to-end DevOps operational loop — observe, diagnose, fix, verify."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_agents.roles import run_operational_pipeline


def run_devops_loop(
    *,
    provider: str,
    service_name: str,
    project_name: str | None = None,
    environment: str | None = None,
    phase: str = "diagnose",
    logs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Governed DevOps loop — no mutation without approval."""
    return run_operational_pipeline(
        provider=provider,
        service_name=service_name,
        project_name=project_name,
        environment=environment,
        phase=phase,
        logs=logs,
    )


def devops_loop_summary(result: dict[str, Any]) -> str:
    diagnosis = result.get("diagnosis") or {}
    fix_plan = result.get("fix_plan") or {}
    verification = result.get("verification") or {}
    lines = []
    if diagnosis.get("summary"):
        lines.append(f"Diagnosis: {diagnosis.get('summary')}")
    if diagnosis.get("likely_cause"):
        lines.append(f"Likely cause: {diagnosis.get('likely_cause')}")
    if fix_plan.get("summary"):
        lines.append(f"Fix plan: {fix_plan.get('summary')}")
    if verification.get("status"):
        lines.append(f"Verification: {verification.get('status')}")
    return "\n".join(lines) if lines else "DevOps loop completed — review evidence in Mission Control."
