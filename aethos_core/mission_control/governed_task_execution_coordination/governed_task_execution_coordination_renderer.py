# SPDX-License-Identifier: Apache-2.0
"""FIX 172 — Markdown renderer for governed task execution coordination."""

from __future__ import annotations

from typing import Any


def render_governed_task_execution_coordination(governed_task_execution_coordination: dict[str, Any]) -> str:
    sections = governed_task_execution_coordination.get("sections") or {}

    lines = [
        "# Governed Task Execution Coordination (FIX 172 — coordinate without executing)",
        "",
        f"- session_id: `{governed_task_execution_coordination.get('session_id', '')}`",
        f"- coordination records: **{governed_task_execution_coordination.get('coordination_record_count', 0)}**",
        f"- packages coordinated: **{governed_task_execution_coordination.get('package_count', 0)}**",
        f"- coordination tier: `{governed_task_execution_coordination.get('coordination_tier') or 'none'}`",
        f"- coordination ready: **{governed_task_execution_coordination.get('coordination_ready', False)}**",
        f"- execution performed: **{governed_task_execution_coordination.get('execution_performed', False)}** _(always false)_",
        f"- gate bypass: **{governed_task_execution_coordination.get('gate_bypass_enabled', False)}** _(always false)_",
        "",
        governed_task_execution_coordination.get("invariant", ""),
        "",
        "_Execution coordination assigns and tracks — existing gates still decide outcomes._",
        "",
    ]

    for title, key in (
        ("Participation context read", "participation_context_read"),
        ("Package agent assignments", "package_agent_assignments"),
        ("Package lifecycle tracking", "package_lifecycle_tracking"),
        ("Dependency and sequencing coordination", "dependency_and_sequencing_coordination"),
        ("Parallel readiness coordination", "parallel_readiness_coordination"),
        ("Escalation monitoring", "escalation_monitoring"),
        ("Gate-routed package outcomes", "gate_routed_package_outcomes"),
        ("Forbidden coordination actions", "forbidden_coordination_actions"),
        ("Next-step coordination sequence", "next_step_coordination_sequence"),
        ("Coordination integrity scoring", "coordination_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("lifecycle_id"):
                lines.append(
                    f"- **{item.get('lifecycle_id')}**: state={item.get('lifecycle_state')} "
                    f"executed={item.get('execution_performed')}"
                )
            elif item.get("assignment_id"):
                lines.append(
                    f"- assignment `{item.get('assignment_id')}`: agent={item.get('agent_role_id')} "
                    f"package={item.get('package_id')}"
                )
            elif item.get("sequence_step") is not None:
                lines.append(
                    f"- step {item.get('sequence_step')}: `{item.get('agent_role_id')}` "
                    f"depends_on={item.get('depends_on')}"
                )
            elif item.get("coordination_id"):
                lines.append(f"- **{item.get('coordination_id')}**: {item.get('detail')}")
            elif item.get("monitor_id"):
                lines.append(
                    f"- monitor `{item.get('monitor_id')}`: escalation={item.get('escalation_required')}"
                )
            elif item.get("outcome_id"):
                lines.append(
                    f"- outcome `{item.get('outcome_id')}`: gate={item.get('gate_id')} bypass={item.get('gate_bypass', False)}"
                )
            elif item.get("read_id"):
                lines.append(
                    f"- **{item.get('read_id')}**: ready={item.get('coordination_ready')}"
                )
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} label={item.get('integrity_label')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Execution coordination ≠ execution authority — humans re-engage only on escalation._")
    return "\n".join(lines)
