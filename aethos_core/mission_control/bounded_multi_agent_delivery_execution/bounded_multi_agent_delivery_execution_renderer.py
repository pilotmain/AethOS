# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — Markdown renderer for bounded multi-agent delivery execution."""

from __future__ import annotations

from typing import Any


def render_bounded_multi_agent_delivery_execution(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    pipeline_state = payload.get("pipeline_state", "BLOCKED")

    lines = [
        "# Bounded Multi-Agent Delivery Execution (FIX 189 — agents work, gates decide)",
        "",
        f"- pipeline state: **{pipeline_state}**",
        f"- execution ready: **{payload.get('execution_ready', False)}**",
        f"- agent execution authority: **{payload.get('agent_execution_authority', False)}** _(always false)_",
        f"- merge authority: **{payload.get('merge_authority', False)}** _(always false)_",
        f"- deploy authority: **{payload.get('deploy_authority', False)}** _(always false)_",
        "",
        payload.get("invariant", ""),
        "",
        "## Agent execution packages",
        "",
    ]

    for pkg in sections.get("agent_execution_packages") or []:
        lines.append(
            f"- `{pkg.get('agent_role_id')}`: {pkg.get('display_name')} — "
            f"work performed **{pkg.get('work_performed')}**"
        )
    lines.append("")

    gates = (sections.get("execution_gates") or [{}])[0]
    lines.extend(
        [
            "## Execution gates",
            "",
            f"- FIX 170 authorization: **{gates.get('fix_170_authorization_granted')}**",
            f"- FIX 168 work packages: **{gates.get('fix_168_work_packages_ok')}**",
            f"- FIX 171 participation: **{gates.get('fix_171_participation_ready')}**",
            f"- eligible to run pipeline: **{gates.get('eligible_to_run_pipeline')}**",
            "",
            "## Agent execution registry",
            "",
        ]
    )
    for entry in sections.get("agent_execution_registry") or []:
        lines.append(f"- `{entry.get('agent_role_id')}`: {entry.get('status')} — {entry.get('artifact_type')}")
    lines.append("")

    rec = (sections.get("execution_readiness_assessment") or [{}])[0]
    lines.append(f"## Readiness: {rec.get('assessment_label', 'unknown')}")
    lines.append("")
    lines.append("_Run `run bounded agent delivery execution` after authorization envelope is granted._")
    return "\n".join(lines)
