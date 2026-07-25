# SPDX-License-Identifier: Apache-2.0
"""Runtime metrics — enterprise operational measurement."""

from __future__ import annotations

import threading
from time import time
from typing import Any

_lock = threading.Lock()
_counters: dict[str, float] = {}
_histograms: dict[str, list[float]] = {}


def increment(metric: str, value: float = 1.0) -> None:
    with _lock:
        _counters[metric] = _counters.get(metric, 0.0) + value


def observe(metric: str, value: float) -> None:
    with _lock:
        _histograms.setdefault(metric, []).append(value)
        if len(_histograms[metric]) > 500:
            _histograms[metric] = _histograms[metric][-500:]


def snapshot_metrics() -> dict[str, Any]:
    """Collect all runtime metrics."""
    _collect_runtime_metrics()
    with _lock:
        hist_summary = {}
        for k, vals in _histograms.items():
            if vals:
                hist_summary[k] = {"count": len(vals), "avg": round(sum(vals) / len(vals), 4), "last": vals[-1]}
        return {
            "counters": dict(_counters),
            "histograms": hist_summary,
            "collected_at": time(),
        }


def prometheus_text() -> str:
    """Prometheus exposition format."""
    snap = snapshot_metrics()
    lines = ["# AethOS runtime metrics"]
    for name, val in (snap.get("counters") or {}).items():
        safe = name.replace(".", "_").replace("-", "_")
        lines.append(f"aethos_{safe} {val}")
    for name, info in (snap.get("histograms") or {}).items():
        safe = name.replace(".", "_").replace("-", "_")
        lines.append(f"aethos_{safe}_avg {info.get('avg', 0)}")
    return "\n".join(lines) + "\n"


def _collect_runtime_metrics() -> None:
    try:
        from aethos_core.runtime.schedulers.observation_scheduler import scheduler_status

        st = scheduler_status()
        increment("scheduler.running", 0)
        with _lock:
            _counters["scheduler.running"] = 1.0 if st.get("running") else 0.0
            _counters["scheduler.errors"] = float((st.get("stats") or {}).get("errors") or 0)
    except Exception:
        pass
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        rel = assess_operational_reliability()
        score = float((rel.get("scores") or {}).get("global_reliability_score") or 0)
        observe("reliability.global_score", score)
    except Exception:
        pass
    try:
        from aethos_core.runtime.distributed.queue_backend import get_queue_backend

        observe("queue.depth", float(get_queue_backend().depth()))
    except Exception:
        pass


def clear_metrics_for_tests() -> None:
    with _lock:
        _counters.clear()
        _histograms.clear()
