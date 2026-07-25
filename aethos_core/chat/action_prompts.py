# SPDX-License-Identifier: Apache-2.0
"""Chat copy for runtime action proposals."""

from __future__ import annotations

from aethos_core.runtime.actions import RuntimeAction
from aethos_core.runtime.authority import authority


def _proposal_footer(action: RuntimeAction) -> str:
    return (
        f"\n\n**Action proposed:** `{action.id}`\n"
        f"**Type:** {action.action_type}\n"
        "Approve in **Mission Control → Jobs** before it runs."
    )


def propose_restart_reply(session_id: str = "default") -> tuple[str, str, dict[str, str]]:
    action = authority.propose_action("runtime_restart", source="chat", session_id=session_id)
    body = (
        "I can propose a **runtime restart** action. It requires your approval before anything runs.\n\n"
        "No automatic restart happens from chat alone."
    )
    return (
        body + _proposal_footer(action),
        "action_proposal",
        {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
    )


def propose_terminal_probe_reply(session_id: str = "default") -> tuple[str, str, dict[str, str]]:
    action = authority.propose_action("terminal_probe", source="chat", session_id=session_id)
    caps = authority.capabilities
    if caps["host_executor_enabled"]:
        intro = (
            "I can run a **read-only terminal probe** after approval "
            "(checks shell on PATH and `uname`)."
        )
    else:
        intro = (
            "Host executor is **off**. I proposed a terminal probe anyway — "
            "approve after enabling `HOST_EXECUTOR_ENABLED=true`, or enable first in `.env`."
        )
    return intro + _proposal_footer(action), "action_proposal", {"proposed_action_id": action.id}


def propose_vercel_cli_probe_reply(session_id: str = "default") -> tuple[str, str, dict[str, str]]:
    action = authority.propose_action("vercel_cli_probe", source="chat", session_id=session_id)
    body = (
        "I can run a **read-only Vercel CLI check** (`which vercel`, `vercel --version`) "
        "after approval. No deploy or login commands run automatically."
    )
    return (
        body + _proposal_footer(action),
        "action_proposal",
        {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
    )


def propose_browser_automation_enable(session_id: str = "default") -> tuple[str, str, dict[str, str]]:
    action = authority.propose_action(
        "settings_change_proposal",
        {"flag": "BROWSER_AUTOMATION_ENABLED", "value": "true"},
        source="chat",
        session_id=session_id,
    )
    body = (
        "I can propose enabling **browser automation** via settings change. "
        "You still edit `.env` manually after approval (MVP)."
    )
    return (
        body + _proposal_footer(action),
        "action_proposal",
        {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
    )


def propose_host_executor_enable(session_id: str = "default") -> tuple[str, str, dict[str, str]]:
    action = authority.propose_action(
        "settings_change_proposal",
        {"flag": "HOST_EXECUTOR_ENABLED", "value": "true"},
        source="chat",
        session_id=session_id,
    )
    body = (
        "I can propose enabling the **host executor** via settings change. "
        "You still edit `.env` manually after approval (MVP)."
    )
    return (
        body + _proposal_footer(action),
        "action_proposal",
        {"proposed_action_id": action.id, "proposed_action_type": action.action_type},
    )
