# SPDX-License-Identifier: Apache-2.0
"""Provider behavior memory — provider-specific runtime behavior."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.provider_truth_memory import record_provider_convergence


def recall_provider_behavior(*, provider: str = "railway", converged: bool = True) -> dict[str, Any]:
    memory = record_provider_convergence(provider=provider, converged=converged)
    return {
        **memory,
        "provider": provider,
        "summary": f"Provider behavior memory active for {provider}.",
    }
