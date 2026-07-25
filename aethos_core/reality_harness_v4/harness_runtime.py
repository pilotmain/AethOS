# SPDX-License-Identifier: Apache-2.0
"""Reality Harness 4.0 runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.reality_harness_v4.scenarios import list_reality_scenarios_v4


def harness_state() -> dict[str, Any]:
    scenarios = list_reality_scenarios_v4()
    verified = [s for s in scenarios if s.get("status") == "verified"]
    avg = round(sum(s.get("coverage_pct", 0) for s in scenarios) / max(len(scenarios), 1))
    return {
        "ok": True,
        "harness_version": "4.0",
        "scenario_count": len(scenarios),
        "verified_count": len(verified),
        "average_coverage_pct": avg,
        "scenarios": scenarios,
        "summary": f"Reality harness 4.0: {len(verified)}/{len(scenarios)} scenarios verified at {avg}% average coverage.",
    }
