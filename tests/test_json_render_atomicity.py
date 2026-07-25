# SPDX-License-Identifier: Apache-2.0
"""JSON render atomicity tests."""

from __future__ import annotations

import json

import pytest

from aethos_core.response_composition.json_renderer import build_json_export, render_json_block
from aethos_core.response_composition.render_pipeline.render_transaction import (
    clear_render_transactions_for_tests,
    execute_render_pipeline,
)
from aethos_core.response_composition.render_pipeline.structured_output_validator import (
    extract_json_fence,
    validate_json_output,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_render_transactions_for_tests()
    yield
    clear_render_transactions_for_tests()


def _payload() -> dict:
    return {
        "services": [
            {"service": "api", "project": "demo", "environment": "production", "status": "running", "health": "healthy"},
            {"service": "worker", "project": "demo", "environment": "production", "status": "failed", "health": "failed"},
        ],
        "counts": {"total": 2, "healthy": 1, "failed": 1, "unknown": 0},
        "failures": [{"service": "worker", "project": "demo", "environment": "production", "status": "failed", "health": "failed"}],
        "unknown": [],
        "filter_mode": "all",
    }


def test_valid_json():
    block = render_json_block(_payload())
    validation = validate_json_output(f"header\n\n{block}")
    assert validation.ok is True
    assert validation.parsed["summary"]["failed"] == 1
    assert len(validation.parsed["services"]) == 2
    assert "metadata" in validation.parsed


def test_truncation_prevention_rejects_invalid_fence():
    broken = "header\n\n```json\n{\"failures\": [\n```"
    validation = validate_json_output(broken)
    assert validation.ok is False


def test_pipeline_json_validation_passes():
    body, tx = execute_render_pipeline(
        payload=_payload(),
        output_format="json",
        filter_mode="all",
        intro="JSON export.",
        from_cache=True,
    )
    assert tx.validation_status == "passed"
    raw = extract_json_fence(body)
    assert raw is not None
    parsed = json.loads(raw)
    assert parsed["metadata"]["filter"] == "none"
    assert "services" in parsed
    assert "summary" in parsed
    assert "failures" not in parsed


def test_concurrent_renderer_isolation():
    payload_a = _payload()
    payload_b = {
        "services": [{"service": "solo", "project": "x", "environment": "production", "status": "running", "health": "healthy"}],
        "counts": {"total": 1, "healthy": 1, "failed": 0, "unknown": 0},
        "failures": [],
        "unknown": [],
        "filter_mode": "all",
    }
    export_a = build_json_export(payload_a)
    export_b = build_json_export(payload_b)
    assert export_a["summary"]["total"] == 2
    assert export_b["summary"]["total"] == 1
    assert export_a["services"][0]["service"] == "api"
    assert export_b["services"][0]["service"] == "solo"


def test_render_rollback_on_invalid_output(monkeypatch):
    def broken_json(*, payload, **kwargs):
        return "oops\n\n```json\n{\"broken\": \n```"

    monkeypatch.setattr(
        "aethos_core.response_composition.render_pipeline.render_transaction.render_provider_wide_health",
        broken_json,
    )
    body, tx = execute_render_pipeline(
        payload=_payload(),
        output_format="json",
        filter_mode="all",
    )
    assert tx.validation_status.startswith("failed:")
    assert "partial JSON" in body or "Structured render failed" in body
    assert '"broken"' not in body
