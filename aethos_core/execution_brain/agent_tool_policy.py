# SPDX-License-Identifier: Apache-2.0
"""Channel-scoped agent tool policy — admin/public allowlists + AethOS governance."""

from __future__ import annotations

from typing import Any

# Restricted on external/untrusted channels (Telegram, Slack, etc.)
CHANNEL_RESTRICTED_TOOLS = frozenset(
    {
        "terminal_create_preflight",
        "cursor_open_preflight",
        "provider_create_mutation_preflight",
        "provider_exec",
    }
)

READONLY_CHANNEL_TOOLS = frozenset(
    {
        "web_search",
        "provider_catalog",
        "provider_validate",
        "provider_inventory",
        "provider_inventory_all",
        "provider_health",
        "provider_logs",
        "provider_workflows",
        "agent_list",
        "agent_sessions_list",
        "skill_recall",
        "memory_recall",
        "research_run",
    }
)

# Network-facing / mutating tools denied to non-main (sandboxed) sessions —
# spawned subagents, group sessions, and untrusted inbound channels (handoff §12).
# Includes forward-compat names for capabilities landing in later steps.
SANDBOX_DENY_TOOLS = frozenset(
    CHANNEL_RESTRICTED_TOOLS
    | {
        "channel_send",
        "canvas_render",
    }
)

# Operator's own "main" session ids — run on host with full access (handoff §12).
_MAIN_SESSION_IDS = frozenset({"", "main", "operator", "default", "mcp"})

# Authenticated Mission Control / web chat surfaces (not external channels).
_OPERATOR_UI_CHANNELS = frozenset({"chat", "webchat", "mission_control", "mc", "operator"})
_OPERATOR_UI_SURFACES = frozenset({"webchat", "web", "mission_control", "mc", "operator"})


def normalize_channel(channel: str) -> str:
    return (channel or "chat").strip().lower()


def is_restricted_channel(channel: str) -> bool:
    return normalize_channel(channel) in {"telegram", "slack", "discord", "sms", "whatsapp"}


def is_main_session(session_id: str) -> bool:
    """The solo operator's own session (host, full access). Subagent session keys are non-main."""
    sid = (session_id or "").strip().lower()
    if not sid:
        return True
    from aethos_core.agents.runtime.subagent_session_store import is_subagent_session_key

    if is_subagent_session_key(sid):
        return False
    return sid in _MAIN_SESSION_IDS


def is_operator_trusted_ui_session(
    session_id: str,
    *,
    channel: str = "chat",
    surface: str = "",
) -> bool:
    """Signed-in Mission Control / web chat — full tool access for the tenant owner.

    Generated web session ids (``sess-…``) are trusted here. External inbound
    channels and spawned subagent sessions stay sandboxed.
    """
    if is_restricted_channel(channel):
        return False
    from aethos_core.agents.runtime.subagent_session_store import is_subagent_session_key

    sid = (session_id or "").strip()
    if is_subagent_session_key(sid):
        return False
    ch = normalize_channel(channel)
    surf = (surface or "").strip().lower()
    if ch in _OPERATOR_UI_CHANNELS or surf in _OPERATOR_UI_SURFACES:
        return True
    return is_main_session(session_id)


def is_sandboxed_session(
    session_id: str,
    *,
    channel: str = "chat",
    surface: str = "",
) -> bool:
    """Non-main sessions are sandboxed when SANDBOX_NONMAIN_ENABLED (default on, handoff §12)."""
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "sandbox_nonmain_enabled", True):
        return False
    if is_restricted_channel(channel):
        return True
    if is_operator_trusted_ui_session(session_id, channel=channel, surface=surface):
        return False
    return not is_main_session(session_id)


def is_tool_allowed(
    tool_name: str,
    *,
    channel: str = "chat",
    session_id: str = "main",
    surface: str = "",
) -> bool:
    name = (tool_name or "").strip()
    if not name:
        return False
    ch = normalize_channel(channel)
    # Sandboxed (non-main) sessions deny network + mutating tools by default (handoff §12).
    if name in SANDBOX_DENY_TOOLS and is_sandboxed_session(session_id, channel=ch, surface=surface):
        return False
    if is_restricted_channel(ch) and name in CHANNEL_RESTRICTED_TOOLS:
        return False
    if is_restricted_channel(ch) and name not in READONLY_CHANNEL_TOOLS and not name.startswith("agent_"):
        if name in {"agent_spawn", "agent_send"}:
            return True
        return name in READONLY_CHANNEL_TOOLS
    return True


def filter_tool_schemas(
    tools: list[dict[str, Any]],
    *,
    channel: str = "chat",
    session_id: str = "main",
    surface: str = "",
) -> list[dict[str, Any]]:
    return [
        t
        for t in tools
        if is_tool_allowed(
            str(t.get("name") or ""),
            channel=channel,
            session_id=session_id,
            surface=surface,
        )
    ]


def policy_denial_payload(tool_name: str, *, channel: str, session_id: str = "main") -> dict[str, Any]:
    sandboxed = is_sandboxed_session(session_id, channel=normalize_channel(channel))
    hint = (
        "This tool is not available in sandboxed or external-channel sessions. "
        "Use Mission Control web chat for canvas and governed deploy preflights."
        if sandboxed
        else "Use Mission Control chat or operator channel for preflight/mutation tools."
    )
    return {
        "ok": False,
        "error": "tool_not_allowed_for_channel",
        "tool": tool_name,
        "channel": normalize_channel(channel),
        "session_id": session_id,
        "sandboxed": sandboxed,
        "hint": hint,
    }


def policy_snapshot(*, channel: str = "chat", session_id: str = "main", surface: str = "") -> dict[str, Any]:
    from aethos_core.execution_brain.agent_tool_catalog import list_model_facing_tool_names

    ch = normalize_channel(channel)
    tools = list_model_facing_tool_names()
    rows = []
    for name in tools:
        allowed = is_tool_allowed(name, channel=ch, session_id=session_id, surface=surface)
        restricted = name in CHANNEL_RESTRICTED_TOOLS
        rows.append(
            {
                "name": name,
                "allowed": allowed,
                "restricted_on_external_channels": restricted,
            }
        )
    return {
        "ok": True,
        "channel": ch,
        "session_id": session_id,
        "restricted_channel": is_restricted_channel(ch),
        "operator_trusted_ui": is_operator_trusted_ui_session(session_id, channel=ch, surface=surface),
        "sandboxed": is_sandboxed_session(session_id, channel=ch, surface=surface),
        "restricted_tools": sorted(CHANNEL_RESTRICTED_TOOLS),
        "readonly_channel_tools": sorted(READONLY_CHANNEL_TOOLS),
        "tools": rows,
    }


def list_channel_policy_matrix() -> dict[str, Any]:
    channels = ["chat", "telegram", "slack", "discord", "mcp"]
    return {
        "ok": True,
        "channels": [policy_snapshot(channel=ch) for ch in channels],
    }
