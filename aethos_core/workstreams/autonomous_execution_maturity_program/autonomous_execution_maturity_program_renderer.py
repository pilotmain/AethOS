# SPDX-License-Identifier: Apache-2.0
"""PHASE_I1 / FIX 361 — render autonomous execution maturity deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_autonomous_execution_maturity_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    registry = _section(payload, "phase_1_autonomous_execution_registry", "autonomous_execution_registry") or {}
    lines = [
        "# Autonomous Execution Maturity Report",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_I1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 361')}",
        "",
        "## Core principle",
        "",
        "Autonomous execution maturity measures capability. **Autonomous execution maturity ≠ autonomous authority.**",
        "",
        f"- Autonomous maturity level: **{metrics.get('autonomous_maturity_level')}**",
        f"- Autonomous execution maturity score: **{metrics.get('autonomous_execution_maturity_score')}**",
        f"- Execution success rate: **{metrics.get('execution_success_rate')}**",
        f"- Planning accuracy score: **{metrics.get('planning_accuracy_score')}**",
        f"- Recovery effectiveness: **{metrics.get('recovery_effectiveness_score')}**",
        f"- Execution requests tracked: **{registry.get('request_count')}**",
        f"- Autonomous authority: **{payload.get('autonomous_authority')}**",
    ]
    return "\n".join(lines)


def render_autonomous_capability_matrix(payload: dict[str, Any]) -> str:
    capabilities = _section(payload, "phase_7_autonomous_capability_registry", "autonomous_capability_registry") or {}
    lines = [
        "# Autonomous Capability Matrix",
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
            f"- **{cap.get('capability_id')}** ({cap.get('status')}): success rate **{cap.get('success_rate')}**"
        )
    return "\n".join(lines)


def render_human_intervention_analysis(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_human_intervention_analysis", "human_intervention_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Human Intervention Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Human intervention rate: **{metrics.get('human_intervention_rate')}**",
        f"- Approval count: **{report.get('approval_count')}**",
        f"- Correction notes: **{report.get('correction_notes')}**",
        f"- Overrides: **{report.get('overrides')}**",
        f"- Humans remain final authority: **{report.get('humans_remain_final_authority')}**",
        f"- Governance bypass performed: **{payload.get('governance_bypass')}**",
    ]
    return "\n".join(lines)


def render_all_autonomous_execution_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "AUTONOMOUS_EXECUTION_MATURITY_REPORT.md": render_autonomous_execution_maturity_report(payload),
        "AUTONOMOUS_CAPABILITY_MATRIX.md": render_autonomous_capability_matrix(payload),
        "HUMAN_INTERVENTION_ANALYSIS.md": render_human_intervention_analysis(payload),
    }


def render_autonomous_execution_maturity_program(
    payload: dict[str, Any],
    *,
    focus: str = "autonomous_execution_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Autonomous Execution Maturity Program",
        "",
        f"**Phase:** {payload.get('phase_id', 'PHASE_I1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 361')}",
        "",
        f"Maturity: **{metrics.get('autonomous_maturity_level')}** · "
        f"Score: **{metrics.get('autonomous_execution_maturity_score')}** · "
        f"Success: **{metrics.get('execution_success_rate')}**",
        "",
        "## Operator commands",
        "",
        "- `autonomous execution request: request_id=..., category=delivery, outcome=passed`",
        "- `autonomous execution note: ...`",
        "- `autonomous execution review approve: ...`",
        "- `show autonomous execution dashboard`",
        "",
    ]
    return "\n".join(lines)
