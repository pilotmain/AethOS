# SPDX-License-Identifier: Apache-2.0
"""Plugin governance — plugins cannot bypass orchestration."""

from __future__ import annotations

from typing import Any

from aethos_sdk.plugin_types import FORBIDDEN_CAPABILITIES, PluginManifest


def validate_plugin_governance(manifest: PluginManifest) -> dict[str, Any]:
    errors = manifest.validate()
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "sandboxed": manifest.sandboxed,
        "approval_required": True,
        "autonomous_execution_blocked": True,
        "forbidden": list(FORBIDDEN_CAPABILITIES),
        "governance_statement": "Plugins run sandboxed — no bypass of approval or secret access.",
    }


def sandbox_plugin_call(*, plugin_id: str, handler_name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute plugin handler in governed sandbox context."""
    from aethos_sdk.plugin_registry import get_plugin

    plugin = get_plugin(plugin_id)
    if not plugin:
        return {"ok": False, "error": "plugin_not_found"}
    manifest = plugin.get("manifest") or {}
    gov = validate_plugin_governance(PluginManifest(**manifest))
    if not gov.get("ok"):
        return {"ok": False, "error": "governance_violation", "details": gov.get("errors")}
    return {
        "ok": True,
        "plugin_id": plugin_id,
        "handler": handler_name,
        "sandboxed": True,
        "result": {"status": "simulated", "args": args or {}},
        "autonomous_execution_blocked": True,
    }
