# SPDX-License-Identifier: Apache-2.0
"""Failed filter renderer repair tests."""

from __future__ import annotations

import pytest

from aethos_core.response_composition.conversational_renderer import render_provider_wide_health
from aethos_core.response_composition.render_pipeline.filter_engine import apply_filter, canonical_failed_rows
from aethos_core.response_composition.render_pipeline.render_transaction import execute_render_pipeline
from aethos_core.response_composition.render_pipeline.render_validation import RenderValidationError


def _payload() -> dict:
    return {
        "services": [
            {"service": "pilotcore-finance-engine", "project": "pilotcore-finance-engine", "environment": "production", "status": "failed", "health": "failed"},
            {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "unknown"},
            {"service": "worker", "project": "talking-avatar-worker", "environment": "production", "status": "failed", "health": "failed"},
            {"service": "api", "project": "demo", "environment": "production", "status": "running", "health": "healthy"},
        ],
        "counts": {"total": 4, "healthy": 1, "failed": 3, "unknown": 0},
        "failures": [],
        "unknown": [],
    }


def test_failed_summary_count_lists_failed_rows():
    filtered = apply_filter(_payload(), "failed")
    body = render_provider_wide_health(payload=filtered, output_format="conversational", intro="Cached.")
    assert "Failed: **3**" in body
    assert "pilotcore-finance-engine" in body
    assert "MongoDB" in body
    assert "worker" in body


def test_filtered_services_used_when_failures_key_empty():
    rows = canonical_failed_rows(_payload())
    assert len(rows) == 3
    assert {row["service"] for row in rows} == {"pilotcore-finance-engine", "MongoDB", "worker"}


def test_render_error_if_failed_count_positive_but_no_rows():
    broken = {
        "services": [],
        "counts": {"total": 3, "healthy": 0, "failed": 3, "unknown": 0},
        "failures": [],
        "unknown": [],
        "filter_mode": "failed",
    }
    with pytest.raises(RenderValidationError):
        render_provider_wide_health(payload=broken, output_format="conversational")


def test_pipeline_repair_for_empty_failures_key():
    body, tx = execute_render_pipeline(
        payload=_payload(),
        output_format="conversational",
        filter_mode="failed",
        intro="Using cached report.",
        from_cache=True,
    )
    assert tx.validation_status == "skipped"
    assert "Failed services:" in body
    assert "MongoDB" in body
    assert "worker" in body
