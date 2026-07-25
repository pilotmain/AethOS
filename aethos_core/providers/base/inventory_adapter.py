# SPDX-License-Identifier: Apache-2.0
"""Provider inventory adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class InventoryAdapter(ABC):
    provider: str

    @abstractmethod
    def build_projects_inventory(self, *, auth_context: dict[str, Any]) -> Any: ...
