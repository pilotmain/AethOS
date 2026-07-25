# SPDX-License-Identifier: Apache-2.0
"""Filter integrity when failures key is stale or empty."""

from __future__ import annotations

from aethos_core.response_composition.render_pipeline.filter_engine import apply_filter
from aethos_core.response_composition.render_pipeline.render_transaction import execute_render_pipeline


def test_show_only_failed_with_empty_failures_key_and_status_failed_rows():
    payload = {
        "services": [
            {"service": "pilotcore-finance-engine", "project": "pfe", "environment": "production", "status": "failed", "health": "failed"},
            {"service": "MongoDB", "project": "sales", "environment": "production", "status": "failed", "health": "unknown"},
            {"service": "worker", "project": "demo", "environment": "production", "status": "failed", "health": "failed"},
            {"service": "api", "project": "demo", "environment": "production", "status": "running", "health": "healthy"},
        ],
        "counts": {"total": 4, "healthy": 1, "failed": 3, "unknown": 0},
        "failures": [],
        "unknown": [],
    }
    filtered = apply_filter(payload, "failed")
    assert len(filtered["services"]) == 3
    assert filtered["counts"]["failed"] == 3

    body, tx = execute_render_pipeline(
        payload=payload,
        output_format="conversational",
        filter_mode="failed",
        intro="Using cached report.",
        from_cache=True,
    )
    assert tx.validation_status == "skipped"
    assert "Failed: **3**" in body
    for name in ("pilotcore-finance-engine", "MongoDB", "worker"):
        assert name in body
    assert "api" not in body.split("Failed services:")[-1]
