# SPDX-License-Identifier: Apache-2.0
"""Format Vercel inventory payloads as readable chat tables."""

from __future__ import annotations

from typing import Any

from aethos_core.chat.provider_inventory_format import format_vercel_projects_table as _format_vercel_projects_table


def format_vercel_projects_table(inventory: dict[str, Any], *, max_rows: int = 25) -> str:
    return _format_vercel_projects_table(inventory, max_rows=max_rows)
