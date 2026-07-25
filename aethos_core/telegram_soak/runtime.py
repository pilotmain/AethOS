# SPDX-License-Identifier: Apache-2.0
"""Telegram soak runtime aggregate — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.telegram_soak.continuity_drift import assess_continuity_drift
from aethos_core.telegram_soak.contradiction_capture import capture_contradictions
from aethos_core.telegram_soak.notification_pressure import assess_notification_pressure
from aethos_core.telegram_soak.operational_fatigue import assess_operational_fatigue
from aethos_core.telegram_soak.provider_truth_replay import build_provider_truth_replay
from aethos_core.telegram_soak.session_truth_ledger import summarize_ledger
from aethos_core.telegram_soak.soak_scenarios import list_soak_scenarios


def assess_telegram_soak_runtime(*, session_id: str = "default", channel: str = "telegram") -> dict[str, Any]:
    ledger = summarize_ledger(session_id=session_id)
    drift = assess_continuity_drift(session_id=session_id)
    pressure = assess_notification_pressure(session_id=session_id)
    contradictions = capture_contradictions(session_id=session_id)
    fatigue = assess_operational_fatigue(session_id=session_id)
    replay = build_provider_truth_replay(session_id=session_id)
    qualified = (
        drift.get("qualified", True)
        and pressure.get("qualified", True)
        and contradictions.get("qualified", True)
        and fatigue.get("qualified", True)
    )
    return {
        "ok": True,
        "phase": "11.8.2",
        "channel": channel,
        "session_id": session_id,
        "scenarios": list_soak_scenarios(),
        "ledger": ledger,
        "continuity_drift": drift,
        "notification_pressure": pressure,
        "contradictions": contradictions,
        "operational_fatigue": fatigue,
        "provider_truth_replay": replay,
        "converged": qualified or ledger.get("entry_count", 0) == 0,
        "summary": (
            "Telegram soak validation active — truth ledger, realism scoring, and continuity drift enabled."
        ),
        "principle": "Operational trust is earned through sustained realism under imperfect conditions.",
    }
