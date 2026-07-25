# SPDX-License-Identifier: Apache-2.0
"""Operational rechecks — scheduled runtime validation."""

from __future__ import annotations

from typing import Any

_RECHECK_LOG: list[dict[str, Any]] = []


def schedule_operational_recheck(*, surface: str, passed: bool) -> dict[str, Any]:
    entry = {"surface": surface, "passed": passed}
    _RECHECK_LOG.append(entry)
    if len(_RECHECK_LOG) > 100:
        del _RECHECK_LOG[:-100]
    passed_count = sum(1 for e in _RECHECK_LOG if e["passed"])
    return {
        "recheck_count": len(_RECHECK_LOG),
        "passed_count": passed_count,
        "latest": entry,
        "summary": f"Scheduled runtime validation: {passed_count}/{len(_RECHECK_LOG)} rechecks passing.",
    }
