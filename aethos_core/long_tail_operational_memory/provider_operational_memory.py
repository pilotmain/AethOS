# SPDX-License-Identifier: Apache-2.0
"""Provider operational memory — provider behaviors."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.provider_truth_memory import record_provider_convergence


def recall_provider_operational_memory(*, provider: str = "railway", converged: bool = True) -> dict[str, Any]:
    return record_provider_convergence(provider=provider, converged=converged)
