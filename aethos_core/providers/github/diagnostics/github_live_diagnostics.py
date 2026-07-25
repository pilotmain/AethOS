# SPDX-License-Identifier: Apache-2.0
"""GitHub live readonly diagnostics orchestrator."""

from __future__ import annotations

from aethos_core.providers.github.diagnostics.diagnosis_composer import compose_github_live_diagnosis_reply
from aethos_core.providers.github.diagnostics.live_evidence_collector import collect_github_live_evidence


def run_github_live_diagnostics(
    token: str,
    *,
    repository: str,
    session_id: str = "default",
    operation: str = "live_diagnosis",
) -> tuple[str, dict[str, str]]:
    evidence = collect_github_live_evidence(
        token,
        repository=repository,
        session_id=session_id,
        operation=operation,
    )
    reply = compose_github_live_diagnosis_reply(evidence, operation=operation)
    meta = {
        "route_id": "provider_readonly_intent",
        "matched_module": "providers.github.diagnostics.github_live_diagnostics",
        "readonly_provider": "github",
        "readonly_operation": operation,
        "repository": str(evidence.get("repository") or repository),
        "github_live_diagnostics": "true",
        "workflow_failures": "true" if _has_workflow_failures(evidence) else "false",
    }
    return reply, meta


def _has_workflow_failures(evidence: dict) -> bool:
    diagnostic = dict(evidence.get("workflow_diagnostic") or {})
    checks = dict(evidence.get("checks") or {})
    return bool(diagnostic.get("latest_failed_run")) or bool(checks.get("failed_count"))
