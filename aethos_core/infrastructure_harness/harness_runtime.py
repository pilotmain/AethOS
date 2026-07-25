# SPDX-License-Identifier: Apache-2.0
"""Infrastructure harness runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_harness.scenarios import list_infrastructure_scenarios


def harness_state() -> dict[str, Any]:
    scenarios = list_infrastructure_scenarios()
    verified = [s for s in scenarios if s.get("status") == "verified"]
    avg_coverage = round(sum(s.get("coverage_pct", 0) for s in scenarios) / max(len(scenarios), 1))
    return {
        "ok": True,
        "harness_version": "1.0",
        "scenario_count": len(scenarios),
        "verified_count": len(verified),
        "average_coverage_pct": avg_coverage,
        "scenarios": scenarios,
        "summary": f"Infrastructure harness: {len(verified)}/{len(scenarios)} scenarios verified at {avg_coverage}% average coverage.",
    }
