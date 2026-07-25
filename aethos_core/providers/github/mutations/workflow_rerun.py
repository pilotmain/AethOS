# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun execution."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.operations.mutations_api import rerun_latest_workflow


def execute_workflow_rerun(
    token: str,
    *,
    repository: str,
    workflow_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return rerun_latest_workflow(
        token,
        repository=repository,
        workflow_resolution=workflow_resolution if isinstance(workflow_resolution, dict) else None,
    )
