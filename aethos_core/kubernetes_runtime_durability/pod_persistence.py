# SPDX-License-Identifier: Apache-2.0
"""Pod persistence — pod recovery persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.pod_recovery_resilience import assess_pod_recovery_resilience


def assess_pod_persistence() -> dict[str, Any]:
    return assess_pod_recovery_resilience()
