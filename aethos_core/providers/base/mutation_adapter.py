# SPDX-License-Identifier: Apache-2.0
"""Mutation adapter contract — disabled until Phase 9.4+."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MutationNotEnabledError(RuntimeError):
    pass


class MutationAdapter(ABC):
    provider: str
    enabled: bool = False

    @abstractmethod
    def supported_mutations(self) -> list[str]: ...

    def assert_enabled(self) -> None:
        if not self.enabled:
            raise MutationNotEnabledError(
                f"Mutations are not enabled for provider `{self.provider}` (Phase 9.4+)."
            )

    @abstractmethod
    def dry_run(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def execute(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]: ...
