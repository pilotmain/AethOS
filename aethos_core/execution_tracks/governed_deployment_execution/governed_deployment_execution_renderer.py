# SPDX-License-Identifier: Apache-2.0
"""FIX 337 / EXECUTION_TRACK_4 — render deployment execution deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_deployment_execution_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    lines = [
        "# Deployment Execution Report",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 337')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Deployments run under human approval. **Deployment execution ≠ deployment authority.**",
        "",
        "## Success criteria",
        "",
        f"- Deployment prepared: **{success.get('deployment_prepared')}**",
        f"- Deployment executed: **{success.get('deployment_executed')}**",
        f"- Receipts collected: **{success.get('deployment_receipts_collected')}**",
        f"- Verification performed: **{success.get('verification_performed')}**",
        f"- Track complete: **{success.get('track_complete')}**",
        "",
        "## Phase 4 — Deployment execution",
        "",
        "```json",
        _json_block(_section(payload, "phase_4_deployment_execution", "deployment_execution_report")),
        "```",
        "",
        "## Phase 8 — Dashboard",
        "",
        "```json",
        _json_block(_section(payload, "phase_8_deployment_dashboard", "deployment_execution_dashboard")),
        "```",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_deployment_verification_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_5_post_deploy_verification", "deployment_verification_report") or {}
    failure = _section(payload, "phase_7_failure_assessment", "deployment_failure_assessment") or {}
    lines = [
        "# Deployment Verification Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Verification",
        "",
        f"- Verified: **{report.get('verified')}**",
        f"- Deployment succeeded: **{report.get('deployment_succeeded')}**",
        f"- Endpoint reachable: **{report.get('endpoint_reachable')}**",
        f"- Health checks passed: **{report.get('health_checks_passed')}**",
        f"- Evidence captured: **{report.get('evidence_captured')}**",
        "",
        "## Failure assessment",
        "",
        f"- Failure detected: **{failure.get('failure_detected')}**",
        f"- Failure class: **{failure.get('failure_class', '—')}**",
        "",
    ]
    return "\n".join(lines)


def render_deployment_evidence_report(payload: dict[str, Any]) -> str:
    bundle = _section(payload, "phase_6_operational_evidence", "deployment_evidence_bundle") or {}
    registry = _section(payload, "phase_4_deployment_execution", "deployment_receipt_registry") or {}
    lines = [
        "# Deployment Evidence Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Evidence bundle",
        "",
        "```json",
        _json_block(bundle),
        "```",
        "",
        "## Receipt registry",
        "",
        "```json",
        _json_block(registry),
        "```",
    ]
    return "\n".join(lines)


def render_all_governed_deployment_execution_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "DEPLOYMENT_EXECUTION_REPORT.md": render_deployment_execution_report(payload),
        "DEPLOYMENT_VERIFICATION_REPORT.md": render_deployment_verification_report(payload),
        "DEPLOYMENT_EVIDENCE_REPORT.md": render_deployment_evidence_report(payload),
    }


def render_governed_deployment_execution(
    payload: dict[str, Any],
    *,
    focus: str = "deployment_execution_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_8_deployment_dashboard") or [{}])[0].get(
        "deployment_execution_dashboard", {}
    )
    lines = [
        "# Governed Deployment Execution",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 337')}",
        "",
        "Bounded deployment execution under human approval — rollback and trust remain separate.",
        "",
        f"Deployment: **{dashboard.get('deployment_status', '—')}**",
        f"Verification: **{dashboard.get('verification_status', '—')}**",
        f"Provider: **{dashboard.get('provider', '—')}**",
        f"Environment: **{dashboard.get('environment', '—')}**",
        f"Handoff ready: **{dashboard.get('handoff_ready', False)}**",
        "",
    ]

    if focus == "deployment_verification":
        report = (sections.get("phase_5_post_deploy_verification") or [{}])[0].get(
            "deployment_verification_report", {}
        )
        lines.extend(
            [
                "## Verification",
                "",
                f"Verified: **{report.get('verified')}**",
                f"URL: `{report.get('deployment_url', '—')}`",
                "",
            ]
        )
    else:
        plan = (sections.get("phase_2_deployment_planning") or [{}])[0].get("deployment_plan_report", {})
        lines.extend(
            [
                "## Supported Phase 1 providers",
                "",
                f"`{', '.join(plan.get('phase_1_providers') or [])}`",
                "",
            ]
        )

    lines.extend(["## Required review gates", ""])
    for gate in (
        "deployment_review_note",
        "deployment_readiness_review_note",
        "deployment_execution_review_note",
    ):
        lines.append(f"- `{gate}`")
    lines.append("")
    return "\n".join(lines)
