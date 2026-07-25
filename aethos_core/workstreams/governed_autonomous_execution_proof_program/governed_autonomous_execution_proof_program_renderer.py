# SPDX-License-Identifier: Apache-2.0
"""PHASE_I2 / FIX 362 — render governed autonomous execution proof deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_autonomous_execution_proof_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_autonomous_run_registry", "autonomous_run_registry") or {}
    lines = [
        "# Autonomous Execution Proof Report",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_I2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 362')}",
        "",
        "## Core principle",
        "",
        "Autonomous execution proof measures demonstrated capability. **Autonomous execution proof ≠ autonomous authority.**",
        "",
        f"- Autonomous proof level: **{metrics.get('autonomous_proof_level')}**",
        f"- Autonomous execution proof score: **{metrics.get('autonomous_execution_proof_score')}**",
        f"- Success evidence score: **{metrics.get('success_evidence_score')}**",
        f"- Recovery evidence score: **{metrics.get('recovery_evidence_score')}**",
        f"- Consistency score: **{metrics.get('consistency_score')}**",
        f"- Autonomous runs tracked: **{registry.get('run_count')}**",
        f"- Autonomous authority: **{payload.get('autonomous_authority')}**",
    ]
    return "\n".join(lines)


def render_autonomous_capability_proof_matrix(payload: dict[str, Any]) -> str:
    capabilities = _section(payload, "phase_5_capability_proof_analysis", "autonomous_capability_proof_report") or {}
    lines = [
        "# Autonomous Capability Proof Matrix",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Proven capabilities: **{len(capabilities.get('proven_capabilities') or [])}**",
        f"- Partially proven: **{len(capabilities.get('partially_proven_capabilities') or [])}**",
        f"- Unproven: **{len(capabilities.get('unproven_capabilities') or [])}**",
        "",
        "## Capabilities",
        "",
    ]
    for cap in capabilities.get("capabilities") or []:
        lines.append(
            f"- **{cap.get('capability_id')}** ({cap.get('status')}): proof rate **{cap.get('proof_rate')}**"
        )
    return "\n".join(lines)


def render_autonomous_recovery_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_3_recovery_evidence_analysis", "autonomous_recovery_evidence_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Autonomous Recovery Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Recovery evidence score: **{metrics.get('recovery_evidence_score')}**",
        f"- Failures detected: **{report.get('failures_detected')}**",
        f"- Failures recovered: **{report.get('failures_recovered')}**",
        f"- Recovery quality score: **{report.get('recovery_quality_score')}**",
        f"- Approval bypass performed: **{payload.get('approval_bypass')}**",
    ]
    return "\n".join(lines)


def render_all_autonomous_execution_proof_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "AUTONOMOUS_EXECUTION_PROOF_REPORT.md": render_autonomous_execution_proof_report(payload),
        "AUTONOMOUS_CAPABILITY_PROOF_MATRIX.md": render_autonomous_capability_proof_matrix(payload),
        "AUTONOMOUS_RECOVERY_ANALYSIS.md": render_autonomous_recovery_analysis(payload),
    }


def render_governed_autonomous_execution_proof_program(
    payload: dict[str, Any],
    *,
    focus: str = "autonomous_execution_proof_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Governed Autonomous Execution Proof Program",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_I2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 362')}",
        "",
        f"Proof level: **{metrics.get('autonomous_proof_level')}** · "
        f"Score: **{metrics.get('autonomous_execution_proof_score')}** · "
        f"Success evidence: **{metrics.get('success_evidence_score')}**",
        "",
        "## Operator commands",
        "",
        "- `autonomous proof run: run_id=..., category=delivery, outcome=passed, verification=verified`",
        "- `autonomous proof note: ...`",
        "- `autonomous proof review approve: ...`",
        "- `show autonomous execution proof dashboard`",
        "",
    ]
    return "\n".join(lines)
