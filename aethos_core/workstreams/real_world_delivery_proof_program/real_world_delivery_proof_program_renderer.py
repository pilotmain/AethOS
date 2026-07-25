# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_C1 / FIX 339 — render real world delivery proof deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_real_world_delivery_proof_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real World Delivery Proof Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_C1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 339')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Operational proof measures real delivery execution. **Operational proof ≠ authority expansion.**",
        "",
        "## Wave 1 repositories",
        "",
    ]
    for repo in payload.get("wave_1_repositories") or []:
        lines.append(f"- **{repo.get('display_name')}** (`{repo.get('repository')}`)")
    lines.extend(
        [
            "",
            "## Success criteria",
            "",
            f"- Successful deliveries: **{success.get('successful_deliveries')}**",
            f"- Repeatable deliveries: **{success.get('repeatable_deliveries')}**",
            f"- Measurable quality: **{success.get('measurable_delivery_quality')}**",
            f"- Operational stability: **{success.get('operational_stability')}**",
            f"- Program complete: **{success.get('program_complete')}**",
            "",
            "## Metrics",
            "",
            f"- Successful deliveries: **{metrics.get('successful_deliveries', 0)}**",
            f"- Failed deliveries: **{metrics.get('failed_deliveries', 0)}**",
            f"- Deployments verified: **{metrics.get('deployments_verified', 0)}**",
            f"- Human interventions: **{metrics.get('human_interventions', 0)}**",
            f"- Avg time-to-delivery: **{metrics.get('time_to_delivery_ms', 0)}ms**",
            "",
            "## Non-goals",
            "",
        ]
    )
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_delivery_reliability_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_reliability_tracking", "delivery_reliability_report") or {}
    incidents = _section(payload, "phase_5_incident_tracking", "delivery_incident_registry") or {}
    lines = [
        "# Delivery Reliability Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_C1')}",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Reliability",
        "",
        f"- Success rate: **{report.get('success_rate')}**",
        f"- Failure rate: **{report.get('failure_rate')}**",
        f"- Intervention rate: **{report.get('intervention_rate')}**",
        f"- Average completion time: **{report.get('average_completion_time_ms')}ms**",
        "",
        "## Incidents",
        "",
        f"- Generation failures: **{incidents.get('generation_failures', 0)}**",
        f"- Git failures: **{incidents.get('git_failures', 0)}**",
        f"- Deployment failures: **{incidents.get('deployment_failures', 0)}**",
        f"- Verification failures: **{incidents.get('verification_failures', 0)}**",
        "",
    ]
    return "\n".join(lines)


def render_delivery_trust_impact_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_8_trust_impact_analysis", "delivery_trust_impact_report") or {}
    bundle = _section(payload, "phase_6_operational_evidence", "operational_proof_evidence_bundle") or {}
    lines = [
        "# Delivery Trust Impact Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Trust impact (advisory only)",
        "",
        f"- Execution maturity: **{report.get('execution_maturity')}**",
        f"- Trust promotion performed: **{report.get('trust_promotion_performed')}**",
        f"- Intervention reduction signal: **{report.get('intervention_reduction_signal')}**",
        f"- Pass rate: **{report.get('pass_rate')}**",
        "",
        "## Evidence bundle summary",
        "",
        "```json",
        _json_block(
            {
                "execution_id": bundle.get("execution_id"),
                "repository": bundle.get("repository"),
                "evidence_complete": bundle.get("evidence_complete"),
                "trust_mutation_performed": bundle.get("trust_mutation_performed"),
            }
        ),
        "```",
    ]
    return "\n".join(lines)


def render_all_real_world_delivery_proof_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "REAL_WORLD_DELIVERY_PROOF_REPORT.md": render_real_world_delivery_proof_report(payload),
        "DELIVERY_RELIABILITY_REPORT.md": render_delivery_reliability_report(payload),
        "DELIVERY_TRUST_IMPACT_REPORT.md": render_delivery_trust_impact_report(payload),
    }


def render_real_world_delivery_proof_program(
    payload: dict[str, Any],
    *,
    focus: str = "delivery_proof_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_7_executive_visibility") or [{}])[0].get("delivery_proof_dashboard", {})
    metrics = payload.get("metrics") or {}
    lines = [
        "# Real World Delivery Proof Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_C1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 339')}",
        "",
        "Operational proof of governed delivery across Wave 1 repositories — proof does not expand authority.",
        "",
        f"Successful deliveries: **{metrics.get('successful_deliveries', 0)}**",
        f"Failed deliveries: **{metrics.get('failed_deliveries', 0)}**",
        f"Deployments verified: **{metrics.get('deployments_verified', 0)}**",
        "",
    ]

    if focus == "delivery_proof_status":
        trust = (sections.get("phase_8_trust_impact_analysis") or [{}])[0].get(
            "delivery_trust_impact_report", {}
        )
        lines.extend(
            [
                "## Trust impact (advisory)",
                "",
                f"Execution maturity: **{trust.get('execution_maturity', '—')}**",
                f"Trust promotion: **{trust.get('trust_promotion_performed', False)}**",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Executive visibility",
                "",
                f"FIX modules: `{', '.join(dashboard.get('executive_fix_modules') or [])}`",
                "",
            ]
        )

    lines.extend(["## Operator commands", ""])
    lines.extend(
        [
            "- `delivery proof note: ...`",
            "- `delivery proof run: repository=aethos type=documentation`",
            "- `delivery proof review approve: ...`",
            "- `show delivery proof dashboard`",
            "",
        ]
    )
    return "\n".join(lines)
