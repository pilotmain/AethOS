# SPDX-License-Identifier: Apache-2.0
"""Renderer purity tests."""

from __future__ import annotations

import copy

from aethos_core.response_composition.conversational_renderer import render_provider_wide_health
from aethos_core.response_composition.json_renderer import render_json_block
from aethos_core.response_composition.render_pipeline.filter_engine import apply_filter
from aethos_core.response_composition.render_pipeline.render_guard import guarded_render
from aethos_core.response_composition.render_pipeline.immutable_result_snapshot import ImmutableResultSnapshot


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


def test_no_side_effects_on_input_payload():
    payload = _payload()
    original = copy.deepcopy(payload)
    transformed = apply_filter(payload, "failed")
    render_provider_wide_health(payload=transformed, output_format="table", intro="Test.")
    render_json_block(transformed)
    assert payload == original


def test_no_memory_writes_from_renderer():
    payload = _payload()
    transformed = apply_filter(payload, "all")
    render_snapshot = ImmutableResultSnapshot.freeze(transformed)
    guarded_render(
        render_provider_wide_health,
        render_snapshot.view(),
        payload_hash=render_snapshot.payload_hash,
        output_format="executive_summary",
        intro="Summary.",
    )
    assert ImmutableResultSnapshot.freeze(payload).payload_hash == ImmutableResultSnapshot.freeze(payload).payload_hash


def test_deterministic_outputs():
    transformed = apply_filter(_payload(), "failed")
    first = render_provider_wide_health(payload=transformed, output_format="table", intro="Same.")
    second = render_provider_wide_health(payload=transformed, output_format="table", intro="Same.")
    assert first == second
