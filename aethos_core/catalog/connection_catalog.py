# SPDX-License-Identifier: Apache-2.0
"""Connections catalog — merge provider registry, live connections, and planned entries."""

from __future__ import annotations

from typing import Any

PLANNED_PROVIDERS: list[dict[str, str]] = []

LOCAL_WORKSPACE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "register_workspace": {"read_only": True, "enabled": True, "mutation": False},
    "scan_architecture": {"read_only": True, "enabled": True, "mutation": False},
    "repo_diagnostics": {"read_only": True, "enabled": True, "mutation": False},
    "dependency_analysis": {"read_only": True, "enabled": True, "mutation": False},
    "local_test_runner": {"read_only": True, "enabled": True, "mutation": False},
}


def build_local_workspace_catalog_entry() -> dict[str, Any]:
    """Backend-ready local workspace — Engineering panel, not a vault token provider."""
    return {
        "name": "local",
        "label": "Local workspace",
        "category": "local",
        "connected": False,
        "connection_state": "backend_ready",
        "engineering_view": "local-workspaces",
        "capabilities": LOCAL_WORKSPACE_CAPABILITIES,
        "mutations_enabled": False,
        "capability_summary": _capability_summary(LOCAL_WORKSPACE_CAPABILITIES),
    }

# Channels are surfaced from the live channel registry (see build_connections_catalog),
# not a hardcoded list — adding an adapter to the registry auto-adds it to the UI.

# Channels that require an external host dependency to function. We still list them
# (honest status) but report the requirement instead of a fake "connect" button.
CHANNEL_HOST_REQUIREMENTS: dict[str, str] = {
    "signal": "requires a signal-cli daemon on the host",
    "imessage": "available on a macOS host only",
}


def _connection_state(connected_methods: dict[str, str]) -> str:
    if not connected_methods:
        return "disconnected"
    configured = [
        connected_methods.get("api_token"),
        connected_methods.get("browser_session"),
        connected_methods.get("cli_auth"),
    ]
    if any(v in ("configured", "saved") for v in configured):
        return "connected"
    if any(v not in ("missing", "not_detected", "unknown", "") for v in configured):
        return "partially_configured"
    return "disconnected"


def _capability_summary(capabilities: dict[str, dict[str, Any]]) -> dict[str, int]:
    readonly = mutation = unsupported = 0
    for cap in capabilities.values():
        if cap.get("mutation"):
            if cap.get("enabled"):
                mutation += 1
            else:
                unsupported += 1
        elif cap.get("read_only") and cap.get("enabled"):
            readonly += 1
        else:
            unsupported += 1
    return {"readonly": readonly, "mutation": mutation, "unsupported": unsupported}


def _channel_connection_state(*, name: str, configured: bool) -> str:
    """Honest per-channel state: connected, unavailable_on_this_host, or setup_needed.

    Never "coming soon" for a registered adapter — if a transport exists, the user
    can connect it (or we tell them exactly which host dependency is missing).
    """
    if configured:
        return "connected"
    if name in CHANNEL_HOST_REQUIREMENTS:
        return "unavailable_on_this_host"
    return "setup_needed"


def _build_channel_catalog(telegram_status: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Derive channel cards from the live channel registry — no hardcoded list.

    Only channels with a registered adapter are shown (honest: no fake buttons for
    transports that don't exist yet). Telegram keeps its rich runtime card.
    """
    from aethos_core.channels.channel_registry import channel_registry_payload

    connected: list[dict[str, Any]] = []
    available: list[dict[str, Any]] = []

    if telegram_status.get("configured"):
        connected.append({**telegram_status, "category": "communications", "kind": "channel"})
    else:
        available.append(
            {
                **telegram_status,
                "category": "communications",
                "kind": "channel",
                "connection_state": "setup_needed",
            }
        )

    try:
        rows = channel_registry_payload().get("channels") or []
    except Exception:
        rows = []
    for row in rows:
        name = str(row.get("name") or "")
        if name in ("web", "telegram"):
            continue
        if not row.get("adapter_registered"):
            # Planned placeholder without a real transport — don't show a fake entry.
            continue
        configured = bool(row.get("configured"))
        entry = {
            "name": name,
            "label": row.get("label") or name.title(),
            "category": "communications",
            "kind": "channel",
            "configured": configured,
            "connection_state": _channel_connection_state(name=name, configured=configured),
            "capabilities": row.get("capabilities"),
        }
        note = CHANNEL_HOST_REQUIREMENTS.get(name)
        if note:
            entry["host_requirement"] = note
        (connected if configured else available).append(entry)

    return connected, available


def build_connections_catalog() -> dict[str, Any]:
    import aethos_core.providers  # noqa: F401

    from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status
    from aethos_core.connections.service_registry import list_connections
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    live = list_connections().get("providers") or {}
    registered_names = set(ProviderRegistry.list_names())
    connected_providers: list[dict[str, Any]] = []

    for spec in ProviderRegistry.list_specs():
        conn = live.get(spec.name) or {}
        methods = conn.get("connected_methods") if isinstance(conn.get("connected_methods"), dict) else {}
        connected_providers.append(
            {
                **spec.to_public_dict(),
                "connection_state": _connection_state(methods),
                "preferred_method": conn.get("preferred_method"),
                "connected_methods": methods,
                "credentials_count": len(conn.get("credentials") or []),
                "capability_summary": _capability_summary(spec.capability_dicts()),
            }
        )

    available_providers: list[dict[str, Any]] = []
    backend_ready_providers: list[dict[str, Any]] = []
    if "local" not in registered_names:
        backend_ready_providers.append(build_local_workspace_catalog_entry())
    for planned in PLANNED_PROVIDERS:
        if planned["name"] in registered_names:
            continue
        available_providers.append(
            {
                "name": planned["name"],
                "label": planned["label"],
                "category": planned["category"],
                "connected": False,
                "connection_state": "coming_soon",
                "capabilities": {},
                "mutations_enabled": False,
                "capability_summary": {"readonly": 0, "mutation": 0, "unsupported": 0},
            }
        )

    connected_channels, available_channels = _build_channel_catalog(telegram_channel_status())

    return {
        "connected_providers": connected_providers,
        "available_providers": available_providers,
        "backend_ready_providers": backend_ready_providers,
        "connected_channels": connected_channels,
        "available_channels": available_channels,
    }
