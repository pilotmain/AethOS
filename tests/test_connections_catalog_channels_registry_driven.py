# SPDX-License-Identifier: Apache-2.0
"""§1/§2 — Connections catalog channels are registry-driven, with honest status.

No hardcoded "coming soon": every registered adapter surfaces, configured ones as
connected, unconfigured ones as setup_needed (or unavailable_on_this_host for
host-dependent transports), and planned placeholders without adapters are hidden.
"""

from __future__ import annotations

import pytest

from aethos_core.catalog.connection_catalog import (
    _build_channel_catalog,
    _channel_connection_state,
)


def test_channel_connection_state_is_honest():
    assert _channel_connection_state(name="slack", configured=True) == "connected"
    assert _channel_connection_state(name="slack", configured=False) == "setup_needed"
    assert _channel_connection_state(name="signal", configured=False) == "unavailable_on_this_host"
    assert _channel_connection_state(name="imessage", configured=False) == "unavailable_on_this_host"


def test_catalog_surfaces_all_registered_adapters_no_coming_soon():
    connected, available = _build_channel_catalog({"name": "telegram", "label": "Telegram", "configured": False})
    all_entries = connected + available
    names = {e["name"] for e in all_entries}
    # Every implemented adapter must surface — not just the old 3.
    for expected in ("slack", "discord", "email", "whatsapp", "messenger", "teams", "sms", "voice"):
        assert expected in names, f"{expected} missing from channel catalog"
    # No channel may be labelled the old fake "coming_soon".
    for entry in all_entries:
        assert entry.get("connection_state") != "coming_soon"


def test_catalog_hides_planned_placeholders_without_adapter():
    connected, available = _build_channel_catalog({"name": "telegram", "label": "Telegram", "configured": False})
    names = {e["name"] for e in connected + available}
    # Pure placeholders (no real transport) must not appear as fake entries.
    for placeholder in ("social_dm", "webhook", "desktop", "mobile"):
        assert placeholder not in names


def test_transport_ready_channels_are_not_labelled_stub():
    from aethos_core.channels.channel_registry import channel_registry_payload

    by_name = {r["name"]: r for r in channel_registry_payload()["channels"]}
    for name in ("slack", "discord", "email", "whatsapp", "messenger"):
        assert by_name[name]["status"] != "stub", name


def test_unconfigured_channels_have_capabilities_and_state():
    _connected, available = _build_channel_catalog({"name": "telegram", "label": "Telegram", "configured": False})
    slack = next((e for e in available if e["name"] == "slack"), None)
    assert slack is not None
    assert slack["connection_state"] in ("setup_needed", "connected")
    assert slack["kind"] == "channel"
    assert slack["category"] == "communications"


def test_full_catalog_includes_channel_lists():
    from aethos_core.catalog.connection_catalog import build_connections_catalog

    catalog = build_connections_catalog()
    assert "connected_channels" in catalog
    assert "available_channels" in catalog
    names = {c["name"] for c in catalog["connected_channels"] + catalog["available_channels"]}
    assert "slack" in names and "discord" in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
