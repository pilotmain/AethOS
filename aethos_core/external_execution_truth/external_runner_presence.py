# SPDX-License-Identifier: Apache-2.0
"""External runner presence truth — Phase 11.8.1."""

from __future__ import annotations

from typing import Any

from aethos_core.external_execution_truth.execution_store import list_execution_meta
from aethos_core.external_execution_truth.trigger_dispatch_truth import resolve_runner_mode, trigger_settings


def assess_external_runner_presence(*, session_id: str | None = None) -> dict[str, Any]:
    settings = trigger_settings()
    mode = resolve_runner_mode()
    meta_rows = list_execution_meta(session_id=session_id)
    external_active = sum(1 for m in meta_rows if m.get("runner_mode") == "external" and not m.get("last_callback_at"))
    awaiting = sum(1 for m in meta_rows if str(m.get("dispatch_status") or "") == "awaiting_callback")
    return {
        "runner_mode": mode,
        "trigger_enabled": settings["enabled"],
        "external_dispatch_active": external_active,
        "awaiting_callback_count": awaiting,
        "summary": _summary(mode, external_active, awaiting),
    }


def _summary(mode: str, external_active: int, awaiting: int) -> str:
    if mode == "embedded":
        return "Embedded durable runner — local execution truth."
    if mode == "external":
        if awaiting:
            return f"External Trigger.dev runner — {awaiting} job(s) awaiting callback confirmation."
        return "External Trigger.dev runner — dispatch path active."
    return "Degraded mode — external runner unavailable; embedded fallback with honest lifecycle state."
