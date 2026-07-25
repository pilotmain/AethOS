# SPDX-License-Identifier: Apache-2.0
"""Central provider registry — register adapters once, resolve by name."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.providers.base.capability_matrix import OperationCapability
from aethos_core.providers.base.credential_ui import CredentialUiConfig
from aethos_core.providers.base.inventory_adapter import InventoryAdapter
from aethos_core.providers.base.mutation_adapter import MutationAdapter
from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter


@dataclass
class ProviderSpec:
    name: str
    label: str
    auth_adapter: AuthAdapter
    capabilities: dict[str, OperationCapability] = field(default_factory=dict)
    mutation_adapter: MutationAdapter | None = None
    readonly_execution_factory: Callable[[str], ReadonlyExecutionAdapter | None] | None = None
    preflight_capability_metadata_fn: Callable[[str], dict[str, Any]] | None = None
    inventory_adapter_factory: Callable[[], InventoryAdapter] | None = None
    category: str = "cloud"
    credential_ui: CredentialUiConfig | None = None

    def capability_dicts(self) -> dict[str, dict[str, Any]]:
        return {op: cap.to_dict() for op, cap in self.capabilities.items()}

    def to_public_dict(self) -> dict[str, Any]:
        out = {
            "name": self.name,
            "label": self.label,
            "category": self.category,
            "connected": True,
            "capabilities": self.capability_dicts(),
            "mutations_enabled": bool(self.mutation_adapter and self.mutation_adapter.enabled),
        }
        if self.credential_ui is not None:
            out["credential_ui"] = self.credential_ui.to_dict()
        return out


class ProviderRegistry:
    _providers: dict[str, ProviderSpec] = {}

    @classmethod
    def register(cls, spec: ProviderSpec) -> None:
        cls._providers[spec.name.strip().lower()] = spec

    @classmethod
    def get(cls, name: str) -> ProviderSpec | None:
        return cls._providers.get((name or "").strip().lower())

    @classmethod
    def get_auth_adapter(cls, name: str) -> AuthAdapter | None:
        spec = cls.get(name)
        return spec.auth_adapter if spec else None

    @classmethod
    def get_operation_capability(cls, name: str, operation_type: str) -> OperationCapability | None:
        spec = cls.get(name)
        if not spec:
            return None
        return spec.capabilities.get(operation_type)

    @classmethod
    def get_inventory_adapter(cls, name: str) -> InventoryAdapter | None:
        spec = cls.get(name)
        if not spec or not spec.inventory_adapter_factory:
            return None
        return spec.inventory_adapter_factory()

    @classmethod
    def list_names(cls) -> list[str]:
        return sorted(cls._providers.keys())

    @classmethod
    def list_specs(cls) -> list[ProviderSpec]:
        return [cls._providers[k] for k in cls.list_names()]

    @classmethod
    def list_credential_managed_names(cls) -> list[str]:
        return sorted(
            spec.name
            for spec in cls.list_specs()
            if spec.credential_ui is not None and spec.credential_ui.manage_credentials
        )

    @classmethod
    def public_catalog(cls) -> list[dict[str, Any]]:
        return [spec.to_public_dict() for spec in cls.list_specs()]

    @classmethod
    def clear_for_tests(cls) -> None:
        cls._providers.clear()
