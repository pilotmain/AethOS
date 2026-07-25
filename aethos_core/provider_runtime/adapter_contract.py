# SPDX-License-Identifier: Apache-2.0
"""Universal provider capability adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProviderCapabilityAdapter(ABC):
    provider: str

    @abstractmethod
    def fetch_logs(self, *, target: dict[str, Any], limit: int = 20) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_events(self, *, target: dict[str, Any], limit: int = 20) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_health(self, *, target: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def classify_failure(self, *, logs: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
        return {"ok": False, "error": "not_implemented"}

    def verify_restart(self, *, target: dict[str, Any]) -> dict[str, Any]:
        return {"ok": False, "error": "not_implemented"}


def adapter_for_provider(provider: str) -> ProviderCapabilityAdapter | None:
    if provider == "railway":
        from aethos_core.provider_runtime.railway_adapter import RailwayCapabilityAdapter

        return RailwayCapabilityAdapter()
    return None
