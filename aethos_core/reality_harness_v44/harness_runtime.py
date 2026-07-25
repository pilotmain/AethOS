# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.4 runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.reality_harness_v44.scenarios import list_reality_scenarios_v44


def harness_state() -> dict[str, Any]:
    scenarios = list_reality_scenarios_v44()
    verified = [s for s in scenarios if s.get("status") == "verified"]
    avg = round(sum(s.get("coverage_pct", 0) for s in scenarios) / max(len(scenarios), 1))
    return {
        "ok": True,
        "harness_version": "4.4",
        "scenario_count": len(scenarios),
        "verified_count": len(verified),
        "average_coverage_pct": avg,
        "scenarios": scenarios,
        "summary": f"Reality harness 4.4: {len(verified)}/{len(scenarios)} scenarios verified at {avg}% average coverage.",
    }
