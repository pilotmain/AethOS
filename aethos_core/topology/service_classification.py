# SPDX-License-Identifier: Apache-2.0
"""Service classification — critical vs supporting systems."""

from __future__ import annotations

from typing import Any

_CRITICAL_DEFAULTS = frozenset({"api", "postgres", "redis", "ingress", "worker"})


def classify_services(*, graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph.get("nodes") or []
    names = [n.get("id") for n in nodes if isinstance(n, dict)]
    critical = [n for n in names if n in _CRITICAL_DEFAULTS or str(n).startswith("api")]
    supporting = [n for n in names if n not in critical]
    return {
        "critical": critical,
        "supporting": supporting,
        "summary": f"{len(critical)} critical, {len(supporting)} supporting services.",
    }
