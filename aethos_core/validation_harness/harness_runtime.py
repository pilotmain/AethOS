# SPDX-License-Identifier: Apache-2.0
"""Telegram long-session validation harness runtime — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

from aethos_core.validation_harness.continuity_stress import assess_continuity_stress
from aethos_core.validation_harness.notification_fatigue_validation import assess_notification_fatigue
from aethos_core.validation_harness.parallel_thread_validation import assess_parallel_threads
from aethos_core.validation_harness.provider_failure_validation import assess_provider_failure_realism
from aethos_core.validation_harness.recovery_realism_validation import assess_recovery_realism
from aethos_core.validation_harness.runtime_truth_validation import assess_runtime_truth
from aethos_core.validation_harness.telegram_session_harness import list_telegram_scenarios


def harness_state(*, session_id: str = "default") -> dict[str, Any]:
    scenarios = list_telegram_scenarios()
    verified = [s for s in scenarios if s.get("status") == "verified"]
    avg = round(sum(s.get("coverage_pct", 0) for s in scenarios) / max(len(scenarios), 1))
    live_checks = {
        "continuity": assess_continuity_stress(session_id=session_id),
        "parallel_threads": assess_parallel_threads(session_id=session_id),
        "provider_failures": assess_provider_failure_realism(session_id=session_id),
        "notification_fatigue": assess_notification_fatigue(session_id=session_id),
        "recovery_realism": assess_recovery_realism(session_id=session_id),
        "runtime_truth": assess_runtime_truth(session_id=session_id),
    }
    return {
        "ok": True,
        "phase": "11.8.0",
        "harness_version": "11.8.0",
        "scenario_count": len(scenarios),
        "verified_count": len(verified),
        "average_coverage_pct": avg,
        "scenarios": scenarios,
        "live_checks": live_checks,
        "summary": (
            f"Telegram long-session validation harness: {len(verified)}/{len(scenarios)} scenarios verified "
            f"at {avg}% average coverage."
        ),
    }
