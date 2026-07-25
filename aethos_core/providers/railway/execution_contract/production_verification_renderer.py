# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production verification evidence reports."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.production_verification_evidence import (
    ProductionVerificationEvidenceBundle,
)
from aethos_core.providers.railway.execution_contract.production_verification_rules import (
    ProductionVerificationAssessment,
    load_production_verification_rules_config,
)
from aethos_core.providers.railway.execution_contract.production_verification_service import (
    assess_production_verification_readiness,
)


def render_production_verification_evidence_report(
    *,
    evidence: ProductionVerificationEvidenceBundle,
    assessment: ProductionVerificationAssessment,
    receipt: dict[str, Any] | None = None,
) -> str:
    rules = load_production_verification_rules_config()
    lines = [
        "# Railway Production Verification Evidence",
        "",
        f"- execution_id: `{evidence.execution_id}`",
        f"- environment: **{evidence.environment}**",
        f"- mode: **{evidence.mode}**",
        f"- verification_passed: **{str(assessment.verification_passed).lower()}**",
        f"- strong_signals: **{assessment.strong_signal_count}** (min {rules.min_strong_signals})",
        f"- signal_families: **{', '.join(assessment.families_present) or 'none'}**",
        f"- rollback_recommendation: **{assessment.rollback_recommendation}**",
        f"- incident_escalation: **{assessment.incident_escalation}**",
        "",
        "## SLO evidence",
        f"- availability_slo: {evidence.slo.availability_slo}",
        f"- availability_target_met: **{str(evidence.slo.availability_target_met).lower()}**",
        f"- latency_budget_ms: {evidence.slo.latency_budget_ms}",
        f"- latency_budget_met: **{str(evidence.slo.latency_budget_met).lower()}**",
        f"- observed_availability_pct: {evidence.slo.observed_availability_pct}",
        f"- observed_p99_latency_ms: {evidence.slo.observed_p99_latency_ms}",
        "",
        "## Health check confidence",
        f"- path: `{evidence.health_check.path}`",
        f"- confidence: **{evidence.health_check.confidence}**",
        f"- multi_probe_agreement: **{str(evidence.health_check.multi_probe_agreement).lower()}**",
        f"- probes: {evidence.health_check.probes_passed}/{evidence.health_check.probes_total}",
        "",
        "## Deployment log evidence",
        f"- log_window_available: **{str(evidence.deployment_logs.log_window_available).lower()}**",
        f"- success_pattern_matched: **{str(evidence.deployment_logs.success_pattern_matched).lower()}**",
        f"- error_pattern_absent: **{str(evidence.deployment_logs.error_pattern_absent).lower()}**",
        f"- redacted_excerpt: {evidence.deployment_logs.redacted_excerpt}",
        "",
        "## Signals",
    ]
    for signal in evidence.signals:
        status = "pass" if signal.passed else "fail"
        lines.append(
            f"- `{signal.signal_id}` ({signal.family}/{signal.strength}): **{status}** — {signal.summary}"
        )
    if assessment.blockers:
        lines.extend(["", "## Blockers"])
        for code in assessment.blockers:
            lines.append(f"- `{code}`")
    if assessment.messages:
        lines.extend(["", "## Policy messages"])
        for msg in assessment.messages:
            lines.append(f"- {msg}")
    if receipt:
        lines.extend(
            [
                "",
                "## Receipt",
                f"- receipt_id: `{receipt.get('receipt_id')}`",
                f"- schema_version: {receipt.get('schema_version')}",
                f"- mutation_performed: **false**",
            ]
        )
    lines.extend(
        [
            "",
            "No live production mutation performed. Verification requires multiple independent signals.",
        ]
    )
    return "\n".join(lines)


def render_production_verification_readiness(*, readiness: dict[str, Any]) -> str:
    lines = [
        "# Railway Production Verification Readiness",
        "",
        f"- ready: **{str(readiness.get('ready')).lower()}**",
        f"- slo_verification_required: **{str(readiness.get('slo_verification_required')).lower()}**",
    ]
    blockers = readiness.get("blockers") or []
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- `{code}`")
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)
