# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — Markdown renderer for bounded delivery work packages."""

from __future__ import annotations

from typing import Any


def render_bounded_delivery_work_packages(bounded_delivery_work_packages: dict[str, Any]) -> str:
    sections = bounded_delivery_work_packages.get("sections") or {}

    lines = [
        "# Bounded Multi-Agent Delivery Work Packages (FIX 168 — package cognition)",
        "",
        f"- session_id: `{bounded_delivery_work_packages.get('session_id', '')}`",
        f"- work package records: **{bounded_delivery_work_packages.get('work_package_record_count', 0)}**",
        f"- agent packages: **{bounded_delivery_work_packages.get('agent_package_count', 0)}**",
        f"- selected path: `{bounded_delivery_work_packages.get('selected_path_id') or 'pending'}`",
        f"- autonomous execution: **{bounded_delivery_work_packages.get('autonomous_execution_enabled', False)}** _(always false)_",
        f"- code write: **{bounded_delivery_work_packages.get('code_write_enabled', False)}** _(always false)_",
        "",
        bounded_delivery_work_packages.get("invariant", ""),
        "",
        "_Work packages scope bounded delivery — no execution, code writes, PR actions, or Railway mutation._",
        "",
    ]

    for title, key in (
        ("Handoff artifact read", "handoff_artifact_read"),
        ("Role-scoped work packages", "role_scoped_work_packages"),
        ("Agent package assignments", "agent_package_assignments"),
        ("Package inputs and outputs", "package_inputs_outputs"),
        ("Required package gates", "required_package_gates"),
        ("Package forbidden actions", "package_forbidden_actions"),
        ("Package artifact registry", "package_artifact_registry"),
        ("Next-step readiness sequence", "next_step_readiness_sequence"),
        ("Delivery integrity scoring", "delivery_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("package_id") and item.get("agent_role_id"):
                lines.append(
                    f"- **{item.get('package_id')}** ({item.get('agent_role_id')}): "
                    f"inputs={len(item.get('inputs') or [])} outputs={len(item.get('outputs') or [])}"
                )
            elif item.get("assignment_id"):
                lines.append(
                    f"- **{item.get('assignment_id')}**: {item.get('display_name') or item.get('agent_role_id')} "
                    f"assigned={item.get('assigned', item.get('agent_count') is not None)}"
                )
            elif item.get("gate_id"):
                lines.append(f"- gate `{item.get('gate_id')}` agent={item.get('agent_role_id', item.get('source', ''))}")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("registry_id"):
                lines.append(f"- registry `{item.get('registry_id')}` agent={item.get('agent_role_id')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} "
                    f"label={item.get('integrity_label')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            elif item.get("title"):
                lines.append(f"- **{item.get('title')}**: {item.get('focus')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Work packages ≠ execution authority — humans enter governed delivery with explicit approval._")
    return "\n".join(lines)
