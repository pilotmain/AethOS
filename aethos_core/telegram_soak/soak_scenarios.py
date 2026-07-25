# SPDX-License-Identifier: Apache-2.0
"""Canonical soak scenarios — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

CANONICAL_SOAK_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "delayed_railway_recovery",
        "name": "Delayed Railway recovery follow-up",
        "flow": "A",
        "steps": [
            {"text": "Restart Railway", "simulate_delay_sec": 0},
            {"text": "Did it hold?", "simulate_delay_sec": 0, "backdate_job_sec": 3600},
            {"text": "Has runtime stabilized?", "simulate_delay_sec": 0},
        ],
    },
    {
        "id": "parallel_investigation_drift",
        "name": "Parallel investigation drift",
        "flow": "B",
        "steps": [
            {"text": "Check replay issue", "simulate_delay_sec": 0},
            {"text": "Restart Railway", "simulate_delay_sec": 0},
            {"text": "Check GitHub rerun", "simulate_delay_sec": 0},
            {"text": "Did the replay stabilize?", "simulate_delay_sec": 0},
        ],
    },
    {
        "id": "stale_callback_missing_webhook",
        "name": "Stale callback / missing webhook",
        "flow": "D",
        "steps": [
            {"text": "create two agents, one development one qa, assign them skills", "simulate_delay_sec": 0},
            {"text": "Any updates on the QA agent?", "simulate_delay_sec": 0, "awaiting_external_callback": True},
        ],
    },
    {
        "id": "retry_storm",
        "name": "Retry storm",
        "flow": "E",
        "steps": [
            {"text": "What jobs are running?", "simulate_delay_sec": 0, "inject_retries": 3},
            {"text": "Any updates on verification?", "simulate_delay_sec": 0, "inject_retries": 2},
        ],
    },
    {
        "id": "agent_continuity",
        "name": "Agent continuity",
        "flow": "C",
        "steps": [
            {"text": "create two agents, one development one qa", "simulate_delay_sec": 0},
            {"text": "What did the QA agent conclude?", "simulate_delay_sec": 1},
            {"text": "Any updates?", "simulate_delay_sec": 1},
        ],
    },
]


def list_soak_scenarios() -> list[dict[str, Any]]:
    return [dict(s) for s in CANONICAL_SOAK_SCENARIOS]


def get_soak_scenario(scenario_id: str) -> dict[str, Any] | None:
    for scenario in CANONICAL_SOAK_SCENARIOS:
        if scenario["id"] == scenario_id:
            return dict(scenario)
    return None
