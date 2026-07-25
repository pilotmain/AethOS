# SPDX-License-Identifier: Apache-2.0
"""Recovery decay — delayed degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.rollback_integrity.rollback_decay import assess_rollback_decay


def assess_recovery_decay(*, stable: bool = True) -> dict[str, Any]:
    return assess_rollback_decay(stable=stable)
