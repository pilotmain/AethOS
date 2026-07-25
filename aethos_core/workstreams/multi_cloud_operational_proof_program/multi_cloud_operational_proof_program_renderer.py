# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D2 / FIX 342 — render multi-cloud operational proof deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_multi_cloud_operational_proof_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    dashboard = _section(payload, "phase_8_executive_visibility", "multi_cloud_dashboard") or {}
    lines = [
        "# Multi-Cloud Operational Proof Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_D2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 342')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Evidence collection does not grant authority. **Multi-cloud proof ≠ provider authority.**",
        "",
        "## Providers",
        "",
    ]
    for provider in payload.get("all_proof_providers") or []:
        wave = "Wave 1" if provider in (payload.get("wave_1_providers") or []) else "Phase 1 baseline"
        lines.append(f"- **{provider}** ({wave})")
    lines.extend(
        [
            "",
            "## Success criteria",
            "",
            f"- Multi-cloud deployments demonstrated: **{success.get('multi_cloud_deployments_demonstrated')}**",
            f"- Evidence captured: **{success.get('evidence_captured')}**",
            f"- Wave 1 multi-cloud proven: **{success.get('wave_1_multi_cloud_proven')}**",
            f"- Governance unchanged: **{success.get('governance_unchanged')}**",
            f"- Program complete: **{success.get('program_complete')}**",
            "",
            "## Dashboard",
            "",
            f"- Wave 1 proven: **{dashboard.get('wave_1_multi_cloud_proven')}**",
            "",
            "## Non-goals",
            "",
        ]
    )
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_provider_reliability_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_reliability_tracking", "provider_reliability_report") or {}
    lines = [
        "# Provider Reliability Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Per-provider reliability",
        "",
    ]
    for row in report.get("per_provider") or []:
        lines.append(
            f"- **{row.get('provider')}** — success `{row.get('success_rate')}`, "
            f"verification `{row.get('verification_rate')}`, executions `{row.get('execution_count')}`"
        )
    lines.append("")
    return "\n".join(lines)


def render_provider_maturity_scorecard(payload: dict[str, Any]) -> str:
    scorecard = _section(payload, "phase_7_comparative_analysis", "provider_maturity_scorecard") or {}
    lines = [
        "# Provider Maturity Scorecard",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "Comparative maturity across Railway, Vercel, AWS, Kubernetes, Azure, and GCP.",
        "",
        "```json",
        _json_block(scorecard),
        "```",
    ]
    return "\n".join(lines)


def render_all_multi_cloud_operational_proof_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "MULTI_CLOUD_OPERATIONAL_PROOF_REPORT.md": render_multi_cloud_operational_proof_report(payload),
        "PROVIDER_RELIABILITY_REPORT.md": render_provider_reliability_report(payload),
        "PROVIDER_MATURITY_SCORECARD.md": render_provider_maturity_scorecard(payload),
    }


def render_multi_cloud_operational_proof_program(
    payload: dict[str, Any],
    *,
    focus: str = "multi_cloud_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_executive_visibility", "multi_cloud_dashboard") or {}
    scorecard = _section(payload, "phase_7_comparative_analysis", "provider_maturity_scorecard") or {}
    lines = [
        "# Multi-Cloud Operational Proof Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_D2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 342')}",
        "",
        "Operational proof across all supported cloud providers under unchanged governance.",
        "",
        f"Wave 1 proven: **{dashboard.get('wave_1_multi_cloud_proven', False)}**",
        f"Comparable to Phase 1: **{scorecard.get('comparable_to_phase_1', False)}**",
        "",
        "## Operator commands",
        "",
        "- `provider proof note: ...`",
        "- `provider proof run: provider=aws`",
        "- `provider proof run wave: ...`",
        "- `provider proof review approve: ...`",
        "- `show multi cloud dashboard`",
        "",
    ]
    return "\n".join(lines)
