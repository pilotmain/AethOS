# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 / FIX 347 — render first customer delivery pilot deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_first_customer_delivery_pilot_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    request = _section(payload, "phase_1_customer_request_intake", "customer_delivery_request") or {}
    lines = [
        "# First Customer Delivery Pilot Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 347')}",
        "",
        "## Core principle",
        "",
        "Customer delivery pilot executes within approved bounds. "
        "**Customer delivery pilot ≠ customer authority.**",
        "",
        f"- Customer goal: **{request.get('goal', '—')}**",
        f"- Request type: **{request.get('request_label', request.get('request_type', '—'))}**",
        f"- Pilot execution completed: **{success.get('pilot_execution_completed')}**",
        f"- Customer authority granted: **{success.get('customer_authority_granted')}**",
        f"- Automatic customer acceptance: **{success.get('automatic_customer_acceptance')}**",
        "",
        "## Metrics",
        "",
        f"- Time to workspace: **{metrics.get('time_to_workspace_ms', 0)}ms**",
        f"- Time to code: **{metrics.get('time_to_code_ms', 0)}ms**",
        f"- Time to PR: **{metrics.get('time_to_pr_ms', 0)}ms**",
        f"- Time to deploy: **{metrics.get('time_to_deploy_ms', 0)}ms**",
        f"- Verification outcome: **{metrics.get('verification_outcome', 'PENDING')}**",
        f"- Human approvals: **{metrics.get('human_approval_count', 0)}**",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_customer_delivery_evidence_bundle(payload: dict[str, Any]) -> str:
    cert = _section(payload, "phase_7_end_to_end_certification", "customer_delivery_certification_report") or {}
    bundle = _section(payload, "phase_7_end_to_end_certification", "delivery_evidence_bundle") or {}
    lines = [
        "# Customer Delivery Evidence Bundle",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Certification",
        "",
        f"- Scenario: **{bundle.get('scenario_id', '—')}**",
        f"- Passed: **{bundle.get('passed', cert.get('passed'))}**",
        f"- Run ID: **{bundle.get('run_id', '—')}**",
        "",
        "## ET receipts",
        "",
        "```json",
        _json_block(
            {
                "workspace": _section(payload, "phase_3_workspace_creation", "customer_workspace_report"),
                "generation": _section(payload, "phase_4_code_generation", "customer_code_generation_report"),
                "git_delivery": _section(payload, "phase_5_git_delivery", "customer_git_delivery_report"),
                "deployment": _section(payload, "phase_6_deployment", "customer_deployment_report"),
            }
        ),
        "```",
    ]
    return "\n".join(lines)


def render_customer_value_realization_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_9_value_realization", "customer_value_realization_report") or {}
    if not report:
        phase = (payload.get("sections") or {}).get("phase_9_value_realization", [{}])[0]
        report = phase
    scorecard = report.get("value_scorecard") or {}
    lines = [
        "# Customer Value Realization Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Value realized: **{report.get('value_realized')}**",
        f"- Customer satisfaction: **{report.get('customer_satisfaction')}**",
        f"- Overall level: **{scorecard.get('overall_level', '—')}**",
        f"- Composed from FIX 323: **{report.get('composed_from_fix_323')}**",
    ]
    return "\n".join(lines)


def render_all_first_customer_delivery_pilot_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "FIRST_CUSTOMER_DELIVERY_PILOT_REPORT.md": render_first_customer_delivery_pilot_report(payload),
        "CUSTOMER_DELIVERY_EVIDENCE_BUNDLE.md": render_customer_delivery_evidence_bundle(payload),
        "CUSTOMER_VALUE_REALIZATION_REPORT.md": render_customer_value_realization_report(payload),
    }


def render_first_customer_delivery_pilot_program(
    payload: dict[str, Any],
    *,
    focus: str = "customer_delivery_pilot_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# First Customer Delivery Pilot Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_F1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 347')}",
        "",
        "First governed customer delivery pilot — pilot does not grant customer authority.",
        "",
        f"Verification outcome: **{metrics.get('verification_outcome', 'PENDING')}**",
        f"Value realized: **{metrics.get('value_realized', False)}**",
        "",
        "## Operator commands",
        "",
        "- `customer delivery request: goal=..., scope=..., type=health_check_endpoint`",
        "- `customer delivery pilot run`",
        "- `customer pilot note: ...`",
        "- `customer pilot review approve: ...`",
        "- `show customer delivery pilot dashboard`",
        "",
    ]
    return "\n".join(lines)
