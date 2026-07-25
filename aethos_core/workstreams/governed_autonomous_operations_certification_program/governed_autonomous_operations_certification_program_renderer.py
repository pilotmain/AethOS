# SPDX-License-Identifier: Apache-2.0
"""PHASE_I3 / FIX 363 — render governed autonomous operations certification deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_autonomous_operations_certification_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_certification_candidate_registry", "autonomous_certification_candidate_registry") or {}
    lines = [
        "# Autonomous Operations Certification Report",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_I3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 363')}",
        "",
        "## Core principle",
        "",
        "Autonomous operations certification measures demonstrated capability. **Autonomous operations certification ≠ autonomous authority.**",
        "",
        f"- Certification level: **{metrics.get('autonomous_operations_certification_level')}**",
        f"- Certification score: **{metrics.get('autonomous_operations_certification_score')}**",
        f"- Execution reliability: **{metrics.get('execution_reliability_score')}**",
        f"- Deployment reliability: **{metrics.get('deployment_reliability_score')}**",
        f"- Verification reliability: **{metrics.get('verification_reliability_score')}**",
        f"- Certification candidates: **{registry.get('candidate_count')}**",
        f"- Autonomous authority: **{payload.get('autonomous_authority')}**",
    ]
    return "\n".join(lines)


def render_autonomous_capability_certification_matrix(payload: dict[str, Any]) -> str:
    matrix = _section(payload, "phase_5_capability_certification_matrix", "autonomous_capability_certification_matrix") or {}
    lines = [
        "# Autonomous Capability Certification Matrix",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Certified capabilities: **{len(matrix.get('certified_capabilities') or [])}**",
        f"- Conditionally certified: **{len(matrix.get('conditionally_certified_capabilities') or [])}**",
        f"- Uncertified: **{len(matrix.get('uncertified_capabilities') or [])}**",
        "",
        "## Capabilities",
        "",
    ]
    for cap in matrix.get("capabilities") or []:
        lines.append(
            f"- **{cap.get('capability_id')}** ({cap.get('status')}): certification rate **{cap.get('certification_rate')}**"
        )
    return "\n".join(lines)


def render_autonomous_reliability_certification_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_reliability_certification_analysis", "autonomous_reliability_certification_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Autonomous Reliability Certification Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Execution reliability score: **{metrics.get('execution_reliability_score')}**",
        f"- Deployment reliability score: **{metrics.get('deployment_reliability_score')}**",
        f"- Verification reliability score: **{metrics.get('verification_reliability_score')}**",
        f"- Sustained execution success: **{report.get('sustained_execution_success_demonstrated')}**",
        f"- Sustained deployment success: **{report.get('sustained_deployment_success_demonstrated')}**",
        f"- Approval bypass performed: **{payload.get('approval_bypass')}**",
    ]
    return "\n".join(lines)


def render_all_autonomous_operations_certification_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "AUTONOMOUS_OPERATIONS_CERTIFICATION_REPORT.md": render_autonomous_operations_certification_report(payload),
        "AUTONOMOUS_CAPABILITY_CERTIFICATION_MATRIX.md": render_autonomous_capability_certification_matrix(payload),
        "AUTONOMOUS_RELIABILITY_CERTIFICATION_REPORT.md": render_autonomous_reliability_certification_report(payload),
    }


def render_governed_autonomous_operations_certification_program(
    payload: dict[str, Any],
    *,
    focus: str = "autonomous_operations_certification_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Governed Autonomous Operations Certification Program",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_I3')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 363')}",
        "",
        f"Certification level: **{metrics.get('autonomous_operations_certification_level')}** · "
        f"Score: **{metrics.get('autonomous_operations_certification_score')}** · "
        f"Execution reliability: **{metrics.get('execution_reliability_score')}**",
        "",
        "## Operator commands",
        "",
        "- `autonomous certification candidate: candidate_id=..., workload=delivery, provider=Railway`",
        "- `autonomous certification note: ...`",
        "- `autonomous certification review approve: ...`",
        "- `show autonomous operations certification dashboard`",
        "",
    ]
    return "\n".join(lines)
