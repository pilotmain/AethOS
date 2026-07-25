# SPDX-License-Identifier: Apache-2.0
"""Vercel live readonly diagnostics orchestrator."""

from __future__ import annotations

from aethos_core.providers.vercel.diagnostics.deployment_evidence_collector import collect_vercel_live_evidence
from aethos_core.providers.vercel.diagnostics.diagnosis_composer import compose_vercel_live_diagnosis_reply


def run_vercel_live_diagnostics(
    token: str,
    *,
    project_name: str = "",
    session_id: str = "default",
    operation: str = "live_diagnosis",
) -> tuple[str, dict[str, str]]:
    evidence = collect_vercel_live_evidence(
        token,
        project_name=project_name,
        session_id=session_id,
        operation=operation,
    )
    reply = compose_vercel_live_diagnosis_reply(evidence, operation=operation)
    meta = {
        "route_id": "provider_readonly_intent",
        "matched_module": "providers.vercel.diagnostics.vercel_live_diagnostics",
        "readonly_provider": "vercel",
        "readonly_operation": operation,
        "vercel_live_diagnostics": "true",
        "github_correlation": "true" if dict(evidence.get("github_correlation") or {}).get("available") else "false",
        "failed_deployment": "true" if evidence.get("failed_deployment") else "false",
    }
    if evidence.get("project_name"):
        meta["project"] = str(evidence["project_name"])
    return reply, meta
