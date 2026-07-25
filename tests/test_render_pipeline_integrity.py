# SPDX-License-Identifier: Apache-2.0
"""Render pipeline integrity tests."""

from __future__ import annotations

import copy

import pytest

from aethos_core.response_composition.render_pipeline.filter_engine import apply_filter, extract_failed_rows
from aethos_core.response_composition.render_pipeline.immutable_result_snapshot import (
    ImmutableResultSnapshot,
    ImmutableSnapshotError,
)
from aethos_core.response_composition.render_pipeline.render_guard import guarded_render
from aethos_core.response_composition.render_pipeline.render_transaction import (
    clear_render_transactions_for_tests,
    execute_render_pipeline,
)
from aethos_core.response_composition.conversational_renderer import render_provider_wide_health


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
            {"service": "MongoDB", "project": "sales", "environment": "production", "status": "failed", "health": "unknown"},
        ],
        "counts": {"total": 3, "healthy": 1, "failed": 2, "unknown": 0},
        "failures": [],
        "unknown": [],
    }


def test_renderer_immutability():
    snapshot = ImmutableResultSnapshot.freeze(_payload())
    original = copy.deepcopy(snapshot.payload)

    def mutating_renderer(*, payload, **kwargs):
        payload["counts"] = {"total": 0}
        return "bad"

    with pytest.raises(ImmutableSnapshotError):
        guarded_render(
            mutating_renderer,
            snapshot.view(),
            payload_hash=snapshot.payload_hash,
        )

    assert snapshot.payload == original


def test_failed_only_filtering_with_empty_failures_key():
    filtered = apply_filter(_payload(), "failed")
    names = {row["service"] for row in filtered["services"]}
    assert names == {"worker", "MongoDB"}
    assert filtered["counts"]["failed"] == 2
    assert filtered["counts"]["total"] == 2


def test_failed_only_filtering_status_failed_health_unknown():
    assert len(extract_failed_rows(_payload())) == 2


def test_grouped_filtering():
    body, _tx = execute_render_pipeline(
        payload=_payload(),
        output_format="grouped",
        filter_mode="failed",
        intro="Filtered grouped view.",
    )
    assert "### demo" in body
    assert "worker" in body
    assert "api" not in body.split("### demo")[-1] if "### demo" in body else True


def test_summary_recomputation_on_filter():
    filtered = apply_filter(_payload(), "failed")
    assert filtered["counts"]["total"] == filtered["counts"]["failed"]


def test_no_payload_mutation_after_pipeline():
    payload = _payload()
    original = copy.deepcopy(payload)
    execute_render_pipeline(payload=payload, output_format="conversational", filter_mode="failed")
    assert payload == original


def test_failed_only_render_lists_services():
    body, tx = execute_render_pipeline(
        payload=_payload(),
        output_format="conversational",
        filter_mode="failed",
        intro="Using cached report.",
        from_cache=True,
    )
    assert tx.validation_status == "skipped"
    assert "Failed services:" in body
    assert "worker" in body
    assert "MongoDB" in body
    assert "Failed: **2**" in body
