# SPDX-License-Identifier: Apache-2.0
"""Governance memory — historical governance outcomes."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.reliability.paths import governance_memory_root


def _path():
    return governance_memory_root() / "outcomes.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"outcomes": [], "validation_successes": 0, "deployment_failures": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"outcomes": [], "validation_successes": 0, "deployment_failures": []}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_governance_outcome(*, kind: str, detail: str, success: bool = False) -> None:
    data = _load()
    outcomes = list(data.get("outcomes") or [])
    outcomes.insert(0, {"at": time(), "kind": kind, "detail": detail[:200], "success": success})
    data["outcomes"] = outcomes[:100]
    if kind == "validation" and success:
        data["validation_successes"] = int(data.get("validation_successes") or 0) + 1
    if kind == "deployment_failure":
        failures = list(data.get("deployment_failures") or [])
        failures.insert(0, {"at": time(), "detail": detail[:200]})
        data["deployment_failures"] = failures[:50]
    _save(data)


def governance_memory_snapshot() -> dict[str, Any]:
    data = _load()
    return {
        "recent_outcomes": (data.get("outcomes") or [])[:10],
        "validation_successes": int(data.get("validation_successes") or 0),
        "recent_deployment_failures": (data.get("deployment_failures") or [])[:10],
    }


def clear_governance_memory_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
