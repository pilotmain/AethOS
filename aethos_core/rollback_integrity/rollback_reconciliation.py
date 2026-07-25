# SPDX-License-Identifier: Apache-2.0
"""Rollback reconciliation — verify actual rollback state."""

from __future__ import annotations

from typing import Any

from aethos_core.reconciliation.rollback_consistency import assess_rollback_consistency


def reconcile_rollback(*, provider_result: dict[str, Any] | None = None, readonly_artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    return assess_rollback_consistency(
        provider_result=provider_result or {"summary": "rollback restored"},
        readonly_artifact=readonly_artifact or {},
    )
