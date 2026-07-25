# SPDX-License-Identifier: Apache-2.0
"""Observability dashboard aggregation."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.observability.metrics import snapshot_metrics
from aethos_core.observability.metering import get_usage_summary


def build_observability_dashboard() -> dict[str, Any]:
    """Full observability snapshot for Mission Control."""
    metrics = snapshot_metrics()
    usage = get_usage_summary()
    return {
        "ok": True,
        "metrics": metrics,
        "metering": usage,
        "metric_catalog": [
            {"name": "orchestration.latency", "purpose": "runtime health"},
            {"name": "approval.latency", "purpose": "governance health"},
            {"name": "replay.integrity", "purpose": "operational trust"},
            {"name": "browser.reliability", "purpose": "evidence quality"},
            {"name": "provider.stability", "purpose": "operational risk"},
            {"name": "signal.quality", "purpose": "fatigue prevention"},
            {"name": "execution.reliability", "purpose": "mutation trust"},
            {"name": "research.confidence", "purpose": "evidence quality"},
        ],
        "integrations": {
            "opentelemetry": "ready",
            "prometheus": "/api/v1/observability/metrics/prometheus",
            "grafana": "configure scrape target",
            "loki": "configure log shipping",
        },
        "checked_at": time(),
    }
