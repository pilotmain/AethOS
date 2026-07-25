# SPDX-License-Identifier: Apache-2.0
"""Plugin types and governance constraints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

PLUGIN_TYPES = frozenset(
    {
        "provider_adapter",
        "intelligence_module",
        "channel_adapter",
        "operational_rule",
        "evidence_processor",
    }
)

FORBIDDEN_CAPABILITIES = frozenset(
    {
        "bypass_approval",
        "unrestricted_shell",
        "direct_secret_access",
        "autonomous_mutation",
        "auto_merge",
        "hidden_retry",
    }
)


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    plugin_type: str
    version: str
    author: str = "unknown"
    capabilities: list[str] = field(default_factory=list)
    entrypoint: str | None = None
    sandboxed: bool = True
    approval_required: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.plugin_type not in PLUGIN_TYPES:
            errors.append(f"Invalid plugin type: {self.plugin_type}")
        for cap in self.capabilities:
            if cap in FORBIDDEN_CAPABILITIES:
                errors.append(f"Forbidden capability: {cap}")
        return errors


PluginHandler = Callable[..., Any]
