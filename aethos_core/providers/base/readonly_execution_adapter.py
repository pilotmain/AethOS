# SPDX-License-Identifier: Apache-2.0
"""Read-only execution adapter contract — API-first provider operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReadonlyExecutionAdapter(ABC):
    provider: str

    @abstractmethod
    def get_deployments(self, *, project_name: str, limit: int = 20) -> dict[str, Any]: ...

    @abstractmethod
    def get_domains(self, *, project_name: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_project_details(self, *, project_name: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_deployment_logs(
        self,
        *,
        project_name: str,
        deployment_id: str | None = None,
        project_id: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]: ...
