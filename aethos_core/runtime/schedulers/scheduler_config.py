# SPDX-License-Identifier: Apache-2.0
"""Observation scheduler configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservationSchedule:
    name: str
    interval_sec: float
    enabled: bool = True


DEFAULT_SCHEDULES: tuple[ObservationSchedule, ...] = (
    ObservationSchedule("deployment_health", interval_sec=300.0),
    ObservationSchedule("workflow_failures", interval_sec=600.0),
    ObservationSchedule("dependency_cve", interval_sec=86400.0),
    ObservationSchedule("browser_evidence", interval_sec=3600.0),
    ObservationSchedule("repo_drift", interval_sec=1800.0),
    ObservationSchedule("reality_loop_cycle", interval_sec=600.0),
    ObservationSchedule("presence_cycle", interval_sec=900.0),
    # Continuous Monitor agents — tick frequently; each monitor enforces its own interval.
    ObservationSchedule("continuous_monitors", interval_sec=60.0),
    # Daily Digest — hourly tick; delivers once/day at the configured hour.
    ObservationSchedule("daily_digest", interval_sec=3600.0),
    # Proactive suggestions — refresh the proposal set periodically (gated; read-only).
    ObservationSchedule("proactive_scan", interval_sec=300.0),
)
