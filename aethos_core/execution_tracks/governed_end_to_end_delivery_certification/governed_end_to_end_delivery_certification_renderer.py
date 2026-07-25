# SPDX-License-Identifier: Apache-2.0
"""FIX 338 / EXECUTION_TRACK_5 — render delivery certification deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_end_to_end_delivery_certification_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    status = _section(payload, "phase_7_readiness_assessment", "delivery_certification_status") or {}
    lines = [
        "# End-to-End Delivery Certification Report",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_5')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 338')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Certification measures execution quality. **Delivery certification ≠ delivery authority.**",
        "",
        "## Certification status",
        "",
        f"- Status: **{status.get('status', 'NOT_CERTIFIED')}**",
        f"- Runs: **{status.get('run_count', 0)}**",
        f"- Pass rate: **{status.get('pass_rate', 0.0)}**",
        "",
        "## Success criteria",
        "",
        f"- End-to-end delivery demonstrated: **{success.get('end_to_end_delivery_demonstrated')}**",
        f"- Repeatable delivery: **{success.get('repeatable_delivery')}**",
        f"- Evidence-backed delivery: **{success.get('evidence_backed_delivery')}**",
        f"- Measurable quality: **{success.get('measurable_delivery_quality')}**",
        f"- Track complete: **{success.get('track_complete')}**",
        "",
        "## Certification scenarios",
        "",
    ]
    for scenario_id, name in (payload.get("certification_scenarios") or {}).items():
        lines.append(f"- `{scenario_id}` — {name}")
    lines.extend(["", "## Non-goals", ""])
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_delivery_reliability_report(payload: dict[str, Any]) -> str:
    reliability = _section(payload, "phase_3_reliability_analysis", "delivery_reliability_report") or {}
    quality = _section(payload, "phase_2_execution_quality", "execution_quality_report") or {}
    lines = [
        "# Delivery Reliability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Reliability",
        "",
        f"- Pass rate: **{reliability.get('pass_rate')}**",
        f"- Failure rate: **{reliability.get('failure_rate')}**",
        f"- Recovery rate: **{reliability.get('recovery_rate')}**",
        f"- Intervention rate: **{reliability.get('intervention_rate')}**",
        "",
        "## Execution quality",
        "",
        f"- Workspace success: **{quality.get('workspace_success_rate')}**",
        f"- Generation success: **{quality.get('generation_success_rate')}**",
        f"- Git success: **{quality.get('git_success_rate')}**",
        f"- Deployment success: **{quality.get('deployment_success_rate')}**",
        f"- Verification success: **{quality.get('verification_success_rate')}**",
        "",
    ]
    return "\n".join(lines)


def render_delivery_certification_evidence_report(payload: dict[str, Any]) -> str:
    bundle = _section(payload, "phase_6_evidence_certification", "delivery_certification_evidence_bundle") or {}
    registry = _section(payload, "phase_1_delivery_run_registry", "delivery_run_registry") or {}
    lines = [
        "# Delivery Certification Evidence Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Evidence bundle",
        "",
        "```json",
        _json_block(bundle),
        "```",
        "",
        "## Delivery run registry",
        "",
        "```json",
        _json_block(registry),
        "```",
    ]
    return "\n".join(lines)


def render_all_governed_end_to_end_delivery_certification_deliverables(
    payload: dict[str, Any],
) -> dict[str, str]:
    return {
        "END_TO_END_DELIVERY_CERTIFICATION_REPORT.md": render_end_to_end_delivery_certification_report(payload),
        "DELIVERY_RELIABILITY_REPORT.md": render_delivery_reliability_report(payload),
        "DELIVERY_CERTIFICATION_EVIDENCE_REPORT.md": render_delivery_certification_evidence_report(payload),
    }


def render_governed_end_to_end_delivery_certification(
    payload: dict[str, Any],
    *,
    focus: str = "delivery_certification_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_8_certification_dashboard") or [{}])[0].get(
        "delivery_certification_dashboard", {}
    )
    status_block = (sections.get("phase_7_readiness_assessment") or [{}])[0].get(
        "delivery_certification_status", {}
    )
    lines = [
        "# End-to-End Delivery Certification",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_5')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 338')}",
        "",
        "Certification measures governed delivery quality — certification does not grant authority.",
        "",
        f"Status: **{dashboard.get('certification_status', status_block.get('status', 'NOT_CERTIFIED'))}**",
        f"Runs: **{dashboard.get('run_count', 0)}**",
        f"Pass rate: **{dashboard.get('pass_rate', 0.0)}**",
        f"Core scenarios passed: **{dashboard.get('core_scenarios_passed', [])}**",
        "",
    ]

    if focus == "delivery_certification_status":
        lines.extend(
            [
                "## Readiness assessment",
                "",
                f"All core scenarios passed: **{status_block.get('all_core_scenarios_passed')}**",
                f"Human approved: **{status_block.get('human_certification_approved')}**",
                f"Evidence complete: **{status_block.get('evidence_complete')}**",
                "",
            ]
        )
    else:
        lines.extend(["## Certification scenarios", ""])
        for scenario_id, name in (payload.get("certification_scenarios") or {}).items():
            lines.append(f"- `{scenario_id}` — {name}")
        lines.append("")

    lines.extend(["## Required review gates", ""])
    for gate in (
        "certification_review_note",
        "certification_readiness_review_note",
        "certification_evidence_review_note",
    ):
        lines.append(f"- `{gate}`")
    lines.append("")
    return "\n".join(lines)
