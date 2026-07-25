# SPDX-License-Identifier: Apache-2.0
"""Readonly inventory fetchers — re-export from execution brain registry."""

from aethos_core.execution_brain.provider_inventory_registry import (
    CUSTOM_INVENTORY_FETCHERS,
    HTTP_INVENTORY_SPECS,
    TOKEN_INVENTORY_FETCHERS,
    fetch_provider_inventory,
    fetch_render_inventory,
)

__all__ = [
    "CUSTOM_INVENTORY_FETCHERS",
    "HTTP_INVENTORY_SPECS",
    "TOKEN_INVENTORY_FETCHERS",
    "fetch_provider_inventory",
    "fetch_render_inventory",
]
