# SPDX-License-Identifier: Apache-2.0
"""Namespace analysis — namespace operational mapping."""

from __future__ import annotations

from typing import Any


def analyze_namespaces(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    namespaces = runtime_snapshot.get("namespaces") or []
    if not isinstance(namespaces, list):
        namespaces = []
    mapped = []
    for ns in namespaces:
        if isinstance(ns, str):
            mapped.append({"name": ns, "workloads": 0})
        elif isinstance(ns, dict):
            mapped.append({"name": ns.get("name", "default"), "workloads": ns.get("workloads", 0)})
    return {
        "namespaces": mapped,
        "namespace_count": len(mapped),
        "summary": f"Operational mapping across {len(mapped)} namespaces.",
    }
