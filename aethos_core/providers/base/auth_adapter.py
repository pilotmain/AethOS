# SPDX-License-Identifier: Apache-2.0
"""Provider auth adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aethos_core.connections.models import ProviderConnectionStatus


class AuthAdapter(ABC):
    provider: str

    @abstractmethod
    def connection_status(self) -> ProviderConnectionStatus: ...

    @abstractmethod
    def list_credentials(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def resolve_best_auth_method(self, *, operation: str = "read") -> dict[str, Any]: ...

    @abstractmethod
    def test_credential(self, credential_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def revoke_credential(self, credential_id: str) -> bool: ...
