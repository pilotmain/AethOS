# SPDX-License-Identifier: Apache-2.0
"""Docker container truth — container convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.docker_container_recovery import assess_docker_container_recovery


def assess_docker_container_truth() -> dict[str, Any]:
    return assess_docker_container_recovery()
