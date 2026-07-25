# SPDX-License-Identifier: Apache-2.0
"""Docker container recovery — container stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.docker_runtime_truth import assess_docker_runtime_truth


def assess_docker_container_recovery() -> dict[str, Any]:
    truth = assess_docker_runtime_truth()
    return {**truth, "converged": truth.get("container_recovery_verified", False)}
