# SPDX-License-Identifier: Apache-2.0
"""Reliability harness runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.reliability_harness.scenarios import list_reliability_scenarios


def harness_state() -> dict[str, Any]:
    scenarios = list_reliability_scenarios()
    verified = [s for s in scenarios if s.get("status") == "verified"]
    avg = round(sum(s.get("coverage_pct", 0) for s in scenarios) / max(len(scenarios), 1))
    return {
        "ok": True,
        "harness_version": "3.0",
        "scenario_count": len(scenarios),
        "verified_count": len(verified),
        "average_coverage_pct": avg,
        "scenarios": scenarios,
        "summary": f"Reliability harness 3.0: {len(verified)}/{len(scenarios)} scenarios verified at {avg}% average coverage.",
    }
