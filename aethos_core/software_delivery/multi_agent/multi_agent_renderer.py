# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — multi-agent collaboration renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.multi_agent.multi_agent_contract import (
    BOUNDED_AGENT_ROLE_IDS,
    EXECUTOR_AGENT_ENABLED_FIX_127,
)


def render_collaboration_blocked(*, blockers: list[str], detail: str = "") -> str:
    lines = ["# Software Delivery — Agent Collaboration Blocked", "", "## Blockers"]
    for blocker in blockers:
        lines.append(f"- `{blocker}`")
    if detail:
        lines.extend(["", detail])
    return "\n".join(lines)


def render_collaboration_report(record: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Bounded Agent Collaboration (FIX 127)",
        "",
        f"- collaboration_id: `{record.get('collaboration_id', '')}`",
        f"- status: **{record.get('status', '')}**",
        f"- plan_id: `{record.get('plan_id', '')}`",
        f"- agents_run: **{len(record.get('agent_outputs') or [])}**",
        "",
        "## Boundaries",
        f"- executor_agent: **{record.get('executor_agent_enabled', EXECUTOR_AGENT_ENABLED_FIX_127)}**",
        f"- mutation_performed: **{record.get('mutation_performed', False)}**",
        f"- self_authorizing: **{record.get('self_authorizing', False)}**",
        "",
        "## Agent outputs",
    ]
    for output in record.get("agent_outputs") or []:
        lines.extend(
            [
                f"### {output.get('title', output.get('agent_role_id', ''))}",
                "",
                "**Findings**",
                *[f"- {f}" for f in output.get("findings") or []],
                "",
                "**Recommendations**",
                *[f"- {r}" for r in output.get("recommendations") or []],
                "",
            ]
        )
    lines.append(
        "Agents are **advisory only**. Governed mutations remain in FIX 125A–125I with human approval."
    )
    return "\n".join(lines)


def render_collaboration_status(record: dict[str, Any]) -> str:
    roles = [o.get("agent_role_id") for o in record.get("agent_outputs") or []]
    return "\n".join(
        [
            "# Software Delivery — Agent Collaboration Status",
            "",
            f"- status: **{record.get('status', '')}**",
            f"- roles completed: {', '.join(roles) or 'none'}",
            f"- available roles: {', '.join(BOUNDED_AGENT_ROLE_IDS)}",
            "",
            "Run `show software delivery agent collaboration report` for details.",
        ]
    )
