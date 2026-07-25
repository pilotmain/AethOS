# SPDX-License-Identifier: Apache-2.0
"""Generic provider connection adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aethos_core.connections.auth_labels import (
    AUTH_METHOD_LABELS,
    auth_method_label,
    auth_method_label_for_provider,
    auth_source_phrase,
    normalize_auth_method,
    provider_auth_source_phrase,
)
from aethos_core.connections.models import AuthMethod, ProviderConnectionStatus
from aethos_core.providers.base.auth_adapter import AuthAdapter as BaseAuthAdapter
from aethos_core.providers.base.inventory_adapter import InventoryAdapter as BaseInventoryAdapter

# Re-export provider-neutral contracts for legacy imports.
AuthAdapter = BaseAuthAdapter
InventoryAdapter = BaseInventoryAdapter

# Re-export auth label helpers for backward compatibility.
__all__ = [
    "AUTH_METHOD_LABELS",
    "AuthAdapter",
    "InventoryAdapter",
    "OperationAdapter",
    "auth_method_label",
    "auth_method_label_for_provider",
    "auth_source_phrase",
    "format_auth_method_for_user",
    "github_inspection_completion_message",
    "github_inspection_progress_message",
    "normalize_auth_method",
    "provider_auth_source_phrase",
    "railway_inspection_completion_message",
    "railway_inspection_progress_message",
    "vercel_inspection_completion_message",
    "vercel_inspection_progress_message",
]


def vercel_inspection_progress_message(method: str | None) -> str:
    return f"Running read-only Vercel inspection with {auth_source_phrase(method)}…"


def vercel_inspection_completion_message(method: str | None) -> str:
    key = normalize_auth_method(method)
    if key == "api_token":
        return (
            "Inspection used your saved Vercel API token "
            "(not browser automation or generative access)."
        )
    if key == "browser":
        return "Inspection used your saved browser session (not generative access)."
    if key == "cli":
        return "Inspection used Vercel CLI authentication (not generative access)."
    return "Inspection completed (not generative access)."


def railway_inspection_progress_message(method: str | None) -> str:
    return f"Running read-only Railway inventory with {provider_auth_source_phrase('railway', method)}…"


def railway_inspection_completion_message(method: str | None) -> str:
    return (
        f"Inventory used your {provider_auth_source_phrase('railway', method)} "
        "(not generative access)."
    )


def github_inspection_progress_message(method: str | None) -> str:
    return f"Running read-only GitHub inventory with {provider_auth_source_phrase('github', method)}…"


def github_inspection_completion_message(method: str | None) -> str:
    return (
        f"Inventory used your {provider_auth_source_phrase('github', method)} "
        "(not generative access)."
    )


def format_auth_method_for_user(params: dict[str, object] | None) -> str:
    """Resolve auth label from job params — prefers explicit label, then method."""
    if not params:
        return auth_method_label(None)
    label = params.get("auth_method_label")
    if isinstance(label, str) and label.strip():
        return label.strip()
    method = params.get("auth_method")
    if isinstance(method, str):
        return auth_method_label(method)
    return auth_method_label(None)


class OperationAdapter(ABC):
    provider: str

    @abstractmethod
    def supported_readonly_operations(self) -> list[str]: ...
