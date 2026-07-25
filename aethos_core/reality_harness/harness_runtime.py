# SPDX-License-Identifier: Apache-2.0
"""Reality harness runtime — real operational scenario validation."""

from __future__ import annotations

from typing import Any

from aethos_core.reality_harness.scenarios import list_reality_scenarios


def run_reality_harness_scan(*, window_hours: int = 48) -> dict[str, Any]:
    from aethos_core.operations.reality_loop import run_reality_loop_scan

    scan = run_reality_loop_scan(window_hours=window_hours)
    scenarios = list_reality_scenarios()
    return {
        "ok": True,
        "mode": "scan",
        "scenarios": scenarios,
        "scan": scan,
        "scenario_count": len(scenarios),
        "summary": f"Reality harness scan — {len(scenarios)} validation scenarios tracked.",
    }


def run_reality_harness_cycle(*, window_hours: int = 48, source: str = "harness") -> dict[str, Any]:
    from aethos_core.operations.reality_loop import run_reality_loop_cycle

    cycle = run_reality_loop_cycle(window_hours=window_hours, source=source)
    scenarios = list_reality_scenarios()
    truth = None
    try:
        from aethos_core.operational_truth.runtime import get_operational_truth_state

        truth = get_operational_truth_state()
    except Exception:
        pass

    return {
        "ok": True,
        "mode": "cycle",
        "scenarios": scenarios,
        "cycle": cycle,
        "operational_truth": truth,
        "summary": "Production reality harness cycle completed — operational observations correlated.",
    }


def harness_state() -> dict[str, Any]:
    scenarios = list_reality_scenarios()
    avg = round(sum(s.get("coverage_pct", 0) for s in scenarios) / max(len(scenarios), 1), 1)
    return {
        "ok": True,
        "scenarios": scenarios,
        "scenario_count": len(scenarios),
        "average_coverage_pct": avg,
        "scenarios_with_gaps": sum(1 for s in scenarios if s.get("status") in ("gaps", "partial")),
        "summary": f"Reality harness — {len(scenarios)} scenarios, {avg}% average verification coverage.",
    }
