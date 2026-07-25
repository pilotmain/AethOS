# SPDX-License-Identifier: Apache-2.0
"""Operational pattern memory — recurring deployment, CI, and evidence failures."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root

_PATTERN_FILE = "operational_patterns.json"
_WINDOW_SEC = 7 * 86400


def _path():
    return agent_artifacts_root() / _PATTERN_FILE


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"patterns": {}, "events": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"patterns": {}, "events": []}


def _save(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_operational_event(
    *,
    category: str,
    detail: str,
    plan_id: str | None = None,
    provider: str | None = None,
) -> None:
    """Record an operational signal for recurring pattern detection."""
    data = _load()
    now = time()
    row = {
        "at": now,
        "category": category,
        "detail": detail[:240],
        "plan_id": plan_id,
        "provider": provider,
    }
    events = list(data.get("events") or [])
    events.insert(0, row)
    data["events"] = events[:300]
    patterns = dict(data.get("patterns") or {})
    key = f"{category}:{provider or 'any'}"
    entry = patterns.get(key) or {"category": category, "provider": provider, "count": 0, "last_at": now, "samples": []}
    entry["count"] = int(entry.get("count") or 0) + 1
    entry["last_at"] = now
    samples = list(entry.get("samples") or [])
    samples.insert(0, detail[:120])
    entry["samples"] = samples[:5]
    patterns[key] = entry
    data["patterns"] = patterns
    data["updated_at"] = now
    _save(data)


def record_coordination_patterns(*, merged: dict[str, Any], plan_id: str) -> list[str]:
    """Extract and persist patterns from a coordination merge — returns surfaced lines."""
    surfaced: list[str] = []
    prov = merged.get("deployment_intelligence") or {}
    if prov.get("restart_count", 0) >= 2:
        record_operational_event(
            category="deployment_instability",
            detail=f"{prov['restart_count']} failed/restart signals",
            plan_id=plan_id,
            provider=str(prov.get("provider") or "railway"),
        )
    for gap in (merged.get("confidence") or {}).get("gaps") or []:
        lower = str(gap).lower()
        if "browser" in lower:
            record_operational_event(category="browser_evidence_failure", detail=gap, plan_id=plan_id)
        if "credential" in lower:
            record_operational_event(category="provider_auth_failure", detail=gap, plan_id=plan_id, provider="railway")
    for f in merged.get("failures") or []:
        if f.get("error") == "runtime_budget_exceeded":
            record_operational_event(category="orchestration_timeout", detail="runtime budget exceeded", plan_id=plan_id)
    return get_recurring_patterns()


def get_recurring_patterns(*, window_sec: int = _WINDOW_SEC) -> list[str]:
    """Surface recurring operational patterns within the time window."""
    data = _load()
    now = time()
    patterns = data.get("patterns") or {}
    lines: list[str] = []
    for key, entry in patterns.items():
        if now - float(entry.get("last_at") or 0) > window_sec:
            continue
        count = int(entry.get("count") or 0)
        if count < 2:
            continue
        cat = entry.get("category") or key
        prov = entry.get("provider")
        label = _category_label(cat)
        suffix = f" ({prov})" if prov and prov != "any" else ""
        lines.append(f"Observed {count} {label} signal(s) in 7 days{suffix}.")
    return lines[:8]


def get_operational_patterns_memory() -> dict[str, Any]:
    return _load()


def clear_operational_patterns_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()


def _category_label(category: str) -> str:
    labels = {
        "deployment_instability": "deployment instability",
        "browser_evidence_failure": "browser evidence failure",
        "provider_auth_failure": "provider auth failure",
        "orchestration_timeout": "orchestration timeout",
        "flaky_workflow": "flaky workflow",
        "dependency_churn": "dependency churn",
        "mutation_retry": "mutation retry",
    }
    return labels.get(category, category.replace("_", " "))
