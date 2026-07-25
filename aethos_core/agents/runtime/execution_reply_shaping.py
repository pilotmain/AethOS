# SPDX-License-Identifier: Apache-2.0
"""Execution reply shaping — operational embodiment, not advisory description."""

from __future__ import annotations

from typing import Any


def compose_agent_initialization_reply(
    *,
    entities: list[dict[str, Any]],
    workspace: dict[str, Any],
    objective: str,
    spawn_batch: dict[str, Any] | None = None,
) -> str:
    spawned = list((spawn_batch or {}).get("agents") or [])
    lines: list[str] = []
    for agent in spawned:
        name = str(agent.get("name") or "Agent")
        skills = list(agent.get("skills") or [])
        if skills:
            lines.append(f"**{name}** initialized with skills: {', '.join(skills[:6])}.")
        else:
            lines.append(f"**{name}** initialized.")
    if not lines:
        lines = [f"**{e['name']}** initialized." for e in entities if e.get("name")] or ["Agents initialized."]
    body = "\n".join(lines)
    steps = workspace.get("plan_steps") or []
    plan = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps[:4]))
    objective_line = objective.strip() or "Ready for your next instruction."
    board_note = ""
    if spawned:
        board_note = (
            f"\n\n**{len(spawned)} live lane(s)** on the orchestration board — "
            "each agent is a distinct subagent session you can follow there."
        )
    skills_note = ""
    if (spawn_batch or {}).get("skills_attached"):
        skills_note = "\n\nSkills were attached per role so each agent can perform its specialty."
    return (
        f"{body}\n\n"
        f"**Objective:** {objective_line}\n\n"
        f"**Plan:**\n{plan}"
        f"{skills_note}"
        f"{board_note}\n\n"
        "Ask anytime for status or what each agent is doing."
    )


def compose_entity_status_reply(*, entities: list[dict[str, Any]], workspace: dict[str, Any]) -> str:
    if not entities:
        return (
            "No agents are active in this session yet.\n\n"
            "Tell me which roles to spawn (e.g. development and QA) and I'll stand them up on the orchestration board."
        )
    names = ", ".join(e.get("name", "entity") for e in entities)
    objective = workspace.get("objective") or "on-demand agents from your request"
    return (
        f"Yes — **{names}** are initialized and tracked in this session.\n\n"
        f"Current objective: **{objective}**.\n"
        f"Status: {workspace.get('status') or entities[0].get('status', 'active')}."
    )


def compose_workspace_results_reply(*, entities: list[dict[str, Any]], workspace: dict[str, Any]) -> str:
    if not entities and not workspace:
        return (
            "I don't have an active operational workspace tied to this thread yet.\n\n"
            "Initialize agents first, then I can point you to their accumulated results."
        )
    names = ", ".join(e.get("name", "entity") for e in entities) or "operational agents"
    artifact = workspace.get("artifact_ref")
    artifact_line = f"\n\nLatest artifact: `{artifact}`." if artifact else ""
    objective = workspace.get("objective") or "your assigned objective"
    return (
        f"**{names}** are working within the active operational workspace.\n\n"
        f"Objective: **{objective}**.\n"
        "Outputs accumulate here as agents progress — "
        "check the orchestration board for live lanes, or ask for a specific agent's conclusions."
        f"{artifact_line}"
    )
