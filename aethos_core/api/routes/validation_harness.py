# SPDX-License-Identifier: Apache-2.0
"""Validation harness API — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["validation-harness"])


@router.get("/validation-harness/telegram")
def get_telegram_validation_harness_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.validation_harness.harness_runtime import harness_state

    return harness_state(session_id=session_id)


@router.get("/validation-harness/continuity")
def get_continuity_validation_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.validation_harness.continuity_stress import assess_continuity_stress
    from aethos_core.validation_harness.operational_drift_validation import assess_operational_drift

    return {
        "ok": True,
        "continuity": assess_continuity_stress(session_id=session_id),
        "operational_drift": assess_operational_drift(session_id=session_id),
    }


@router.get("/validation-harness/provider-failures")
def get_provider_failure_validation_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.validation_harness.provider_failure_validation import assess_provider_failure_realism
    from aethos_core.validation_harness.recovery_realism_validation import assess_recovery_realism

    return {
        "ok": True,
        "provider_failures": assess_provider_failure_realism(session_id=session_id),
        "recovery_realism": assess_recovery_realism(session_id=session_id),
    }
