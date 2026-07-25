# SPDX-License-Identifier: Apache-2.0
"""Recovery truth runtime — recovery orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.production_execution_truth.recovery_truth import assess_recovery_truth


def orchestrate_recovery_truth(*, verification: dict[str, Any] | None = None) -> dict[str, Any]:
    return assess_recovery_truth(verification=verification)
