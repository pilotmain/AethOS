# SPDX-License-Identifier: Apache-2.0
"""Plugin registry — governed extension catalog."""

from __future__ import annotations

import json
from typing import Any

from aethos_sdk.plugin_types import PluginManifest

_REGISTRY: dict[str, dict[str, Any]] = {}
_STORE = None


def _store_path():
    from pathlib import Path

    return Path(__file__).resolve().parents[1] / "data" / "plugins" / "registry.json"


def _ensure_builtins() -> None:
    if _REGISTRY:
        return
    builtins = [
        PluginManifest(
            plugin_id="plugin-slack-channel",
            name="Slack Channel Adapter (stub)",
            plugin_type="channel_adapter",
            version="0.1.0",
            sandboxed=True,
        ),
        PluginManifest(
            plugin_id="plugin-custom-analyzer",
            name="Custom Intelligence Module (stub)",
            plugin_type="intelligence_module",
            version="0.1.0",
            sandboxed=True,
        ),
    ]
    for m in builtins:
        _REGISTRY[m.plugin_id] = {"manifest": m.__dict__, "status": "registered", "enabled": False}


def register_plugin(manifest: PluginManifest) -> dict[str, Any]:
    from aethos_sdk.plugin_governance import validate_plugin_governance

    gov = validate_plugin_governance(manifest)
    if not gov.get("ok"):
        return {"ok": False, "errors": gov.get("errors")}
    _ensure_builtins()
    _REGISTRY[manifest.plugin_id] = {"manifest": manifest.__dict__, "status": "registered", "enabled": False}
    _persist()
    return {"ok": True, "plugin_id": manifest.plugin_id}


def list_plugins() -> list[dict[str, Any]]:
    _ensure_builtins()
    return list(_REGISTRY.values())


def get_plugin(plugin_id: str) -> dict[str, Any] | None:
    _ensure_builtins()
    return _REGISTRY.get(plugin_id)


def enable_plugin(plugin_id: str) -> dict[str, Any]:
    plugin = get_plugin(plugin_id)
    if not plugin:
        return {"ok": False, "error": "not_found"}
    plugin["enabled"] = True
    plugin["status"] = "enabled"
    _persist()
    return {"ok": True, "plugin_id": plugin_id, "approval_required": True}


def _persist() -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_REGISTRY, indent=2), encoding="utf-8")


def clear_plugins_for_tests() -> None:
    _REGISTRY.clear()
    path = _store_path()
    if path.is_file():
        path.unlink()
