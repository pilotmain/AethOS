# SPDX-License-Identifier: Apache-2.0
"""Compose workflow discovery replies for operators."""

from __future__ import annotations

from typing import Any


def compose_workflow_discovery_sections(diagnosis: dict[str, Any]) -> list[str]:
    if not diagnosis:
        return []
    repo = str(diagnosis.get("repository") or "the repository")
    lines = [
        f"I could not find any workflow run to rerun for **{repo}**.",
        "",
        "I checked workflow discovery:",
    ]
    lines.append(
        f"- `.github/workflows/`: **{'found' if diagnosis.get('workflows_dir_found') else 'not found'}**"
    )
    names = list(diagnosis.get("workflow_file_names") or [])
    if names:
        lines.append(f"- workflow files: {', '.join(f'`{name}`' for name in names)}")
    else:
        lines.append("- workflow files: none detected")
    triggers = list((diagnosis.get("trigger_analysis") or {}).get("all_triggers") or [])
    if triggers:
        lines.append(f"- triggers: {', '.join(f'`{trigger}`' for trigger in triggers)}")
    else:
        lines.append("- triggers: none detected")
    lines.append(f"- Actions status: **{diagnosis.get('actions_status') or 'unknown'}**")
    lines.append(f"- default branch: `{diagnosis.get('default_branch') or '—'}`")
    auth_state = diagnosis.get("auth_state")
    if auth_state:
        lines.append(f"- GitHub auth: `{auth_state}`")
    lines.extend(["", f"Likely reason:\n{diagnosis.get('likely_reason') or 'Unknown.'}"])
    lines.extend(["", "No rerun is possible until a workflow run exists.", "", "Next steps:"])
    for step in diagnosis.get("next_steps") or []:
        lines.append(f"- {step}")
    return lines


def compose_workflow_discovery_reply(diagnosis: dict[str, Any]) -> str:
    return "\n".join(compose_workflow_discovery_sections(diagnosis))


def compose_workflow_discovery_summary(diagnosis: dict[str, Any]) -> str:
    repo = str(diagnosis.get("repository") or "the repository")
    reason = str(diagnosis.get("likely_reason") or "No workflow run history is available.")
    workflows = "found" if diagnosis.get("workflows_dir_found") else "not found"
    return (
        f"No workflow run exists for **{repo}**. Workflow discovery: `.github/workflows/` {workflows}; "
        f"Actions status **{diagnosis.get('actions_status') or 'unknown'}**. Likely reason: {reason}"
    )
