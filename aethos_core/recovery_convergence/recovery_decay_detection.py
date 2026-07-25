# SPDX-License-Identifier: Apache-2.0
"""Recovery decay detection — post-recovery degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_truth_convergence.recovery_decay import assess_recovery_decay


def detect_recovery_decay(*, stable: bool = True) -> dict[str, Any]:
    decay = assess_recovery_decay(stable=stable)
    return {**decay, "stable": decay.get("post_rollback_stable", stable)}
