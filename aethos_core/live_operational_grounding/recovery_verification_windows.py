# SPDX-License-Identifier: Apache-2.0
"""Recovery verification windows — sustained recovery checks over time."""

from __future__ import annotations

from time import time
from typing import Any

# Window boundaries in minutes from operation start.
_WINDOWS: tuple[tuple[str, float, float | None], ...] = (
    ("immediate", 0.0, 5.0),
    ("five_minute", 5.0, 15.0),
    ("fifteen_minute", 15.0, 60.0),
    ("delayed_followup", 60.0, None),
)


def _elapsed_minutes(*, started_at: float | None) -> float | None:
    if not started_at:
        return None
    return max(0.0, (time() - float(started_at)) / 60.0)


def assess_recovery_verification_windows(
    *,
    session_id: str = "default",
    operation_started_at: float | None = None,
    provider_converged: bool = False,
) -> dict[str, Any]:
    """Track recovery verification phases — avoid premature stabilization claims."""
    started_at = operation_started_at
    if started_at is None:
        try:
            from aethos_core.operational_context_memory.context_store import recall_operational_context

            stored = recall_operational_context(session_id=session_id)
            started_at = stored.get("last_operation_at") or stored.get("updated_at")
        except Exception:
            started_at = None

    elapsed = _elapsed_minutes(started_at=started_at)
    current_window = "unknown"
    completed: list[str] = []
    pending: list[str] = []

    for window_id, start_min, end_min in _WINDOWS:
        label = window_id.replace("_", " ")
        if elapsed is None:
            pending.append(label)
            continue
        if elapsed >= start_min:
            completed.append(label)
            if end_min is None or elapsed < end_min:
                current_window = window_id
        else:
            pending.append(label)

    # Fully proven only after fifteen-minute window AND provider convergence.
    fully_proven = (
        provider_converged
        and elapsed is not None
        and elapsed >= 15.0
        and current_window in {"fifteen_minute", "delayed_followup"}
    )
    stabilizing = not fully_proven

    next_check = pending[0] if pending else "sustained convergence monitoring"

    return {
        "operation_started_at": started_at,
        "elapsed_minutes": round(elapsed, 1) if elapsed is not None else None,
        "current_window": current_window,
        "completed_windows": completed,
        "pending_windows": pending,
        "next_verification": next_check,
        "fully_proven": fully_proven,
        "stabilizing": stabilizing,
        "premature_stable_blocked": not fully_proven,
        "summary": (
            f"Recovery in `{current_window}` window — stabilizing, not fully proven."
            if stabilizing
            else "Sustained verification windows complete — recovery may be fully proven."
        ),
    }
