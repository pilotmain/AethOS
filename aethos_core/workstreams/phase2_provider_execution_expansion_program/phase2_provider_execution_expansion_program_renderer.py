# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D1 / FIX 341 — render Phase 2 provider expansion deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_phase2_provider_expansion_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    registry = _section(payload, "phase_1_provider_expansion_registry", "provider_expansion_registry") or {}
    dashboard = _section(payload, "phase_8_expansion_dashboard", "expansion_dashboard") or {}
    lines = [
        "# Phase 2 Provider Expansion Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_D1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 341')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "New providers inherit existing governance. **Provider expansion ≠ authority expansion.**",
        "",
        "## Wave 1 providers",
        "",
    ]
    for provider in payload.get("wave_1_provider_order") or []:
        services = (payload.get("provider_scopes") or {}).get(provider, [])
        lines.append(f"- **{provider}** — {', '.join(services)}")
    lines.extend(
        [
            "",
            "## Success criteria",
            "",
            f"- Phase 2 providers executable: **{success.get('phase2_providers_executable')}**",
            f"- Multi-cloud execution demonstrated: **{success.get('multi_cloud_execution_demonstrated')}**",
            f"- Governance inherited: **{success.get('governance_inherited')}**",
            f"- Program complete: **{success.get('program_complete')}**",
            "",
            "## Expansion dashboard",
            "",
            f"- Expansion approved: **{dashboard.get('expansion_approved')}**",
            f"- Execution count: **{dashboard.get('execution_count', 0)}**",
            f"- Provider registry count: **{registry.get('provider_count', 0)}**",
            "",
            "## Non-goals",
            "",
        ]
    )
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_aws_execution_readiness_report(payload: dict[str, Any]) -> str:
    aws = (payload.get("sections") or {}).get("phase_2_aws_execution", [{}])[0]
    readiness = (payload.get("sections") or {}).get("phase_7_readiness_assessment", [{}])[0].get(
        "readiness_assessment", {}
    )
    aws_assessment = (readiness.get("providers") or {}).get("AWS", {})
    lines = [
        "# AWS Execution Readiness Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## AWS scope",
        "",
        "- ECS",
        "- Lambda",
        "- API Gateway",
        "",
        "## Readiness",
        "",
        f"- Credentials configured: **{aws_assessment.get('credentials_configured')}**",
        f"- Execution simulated: **{aws_assessment.get('execution_simulated')}**",
        f"- Execution readiness: **{aws_assessment.get('execution_readiness')}**",
        "",
        "## Latest deployment",
        "",
        "```json",
        _json_block(aws.get("aws_deployment_report") or {}),
        "```",
    ]
    return "\n".join(lines)


def render_kubernetes_execution_readiness_report(payload: dict[str, Any]) -> str:
    k8s = (payload.get("sections") or {}).get("phase_3_kubernetes_execution", [{}])[0]
    readiness = (payload.get("sections") or {}).get("phase_7_readiness_assessment", [{}])[0].get(
        "readiness_assessment", {}
    )
    k8s_assessment = (readiness.get("providers") or {}).get("Kubernetes", {})
    lines = [
        "# Kubernetes Execution Readiness Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Kubernetes scope",
        "",
        "- Deployment rollout",
        "- Health verification",
        "- Rollback preparation (no rollback execution)",
        "",
        "## Readiness",
        "",
        f"- Credentials configured: **{k8s_assessment.get('credentials_configured')}**",
        f"- Execution readiness: **{k8s_assessment.get('execution_readiness')}**",
        "",
        "## Latest deployment",
        "",
        "```json",
        _json_block(k8s.get("kubernetes_deployment_report") or {}),
        "```",
        "",
        "## Verification",
        "",
        "```json",
        _json_block(k8s.get("kubernetes_verification_report") or {}),
        "```",
    ]
    return "\n".join(lines)


def render_all_phase2_provider_expansion_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "PHASE2_PROVIDER_EXPANSION_REPORT.md": render_phase2_provider_expansion_report(payload),
        "AWS_EXECUTION_READINESS_REPORT.md": render_aws_execution_readiness_report(payload),
        "KUBERNETES_EXECUTION_READINESS_REPORT.md": render_kubernetes_execution_readiness_report(payload),
    }


def render_phase2_provider_execution_expansion_program(
    payload: dict[str, Any],
    *,
    focus: str = "expansion_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_expansion_dashboard", "expansion_dashboard") or {}
    lines = [
        "# Phase 2 Provider Execution Expansion",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_D1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 341')}",
        "",
        "Multi-cloud governed deployment under inherited ET1–ET4 governance.",
        "",
        f"Expansion approved: **{dashboard.get('expansion_approved', False)}**",
        f"Executions: **{dashboard.get('execution_count', 0)}**",
        f"Ready providers: **{dashboard.get('ready_count', 0)}**",
        "",
        "## Operator commands",
        "",
        "- `phase2 provider readiness review: provider=aws`",
        "- `phase2 provider execution review: provider=aws service=ECS`",
        "- `phase2 provider expansion review approve: ...`",
        "- `phase2 provider deploy: provider=aws service=ECS environment=staging`",
        "- `show phase2 provider dashboard`",
        "",
    ]
    return "\n".join(lines)
