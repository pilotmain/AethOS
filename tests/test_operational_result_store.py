# SPDX-License-Identifier: Apache-2.0
"""Operational result store persistence tests."""

from __future__ import annotations

import pytest

from aethos_core.operational_planner.provider_wide_health_store import (
    clear_provider_wide_health_for_tests,
    get_provider_wide_health_report,
    save_provider_wide_health_report,
)
from aethos_core.response_composition.operational_result_store import (
    get_latest_operational_result,
    record_render_history,
)
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _rows() -> list[dict]:
    return [
        {"service": "api", "project": "demo", "environment": "production", "status": "running", "health": "healthy"},
        {"service": "worker", "project": "demo", "environment": "production", "status": "failed", "health": "failed"},
    ]


def test_provider_wide_report_recall_via_legacy_store():
    save_provider_wide_health_report(
        session_id="store-recall",
        provider="railway",
        rows=_rows(),
        summary={"total": 2, "healthy": 1, "failed": 1, "unknown": 0},
    )
    cached = get_provider_wide_health_report(session_id="store-recall", provider="railway")
    assert cached is not None
    assert len(cached["rows"]) == 2
    assert cached["summary"]["failed"] == 1


def test_active_operational_result_retrieval():
    store_provider_wide_health_result(
        session_id="store-active",
        provider="railway",
        payload={
            "services": _rows(),
            "counts": {"total": 2, "healthy": 1, "failed": 1, "unknown": 0},
            "failures": [_rows()[1]],
            "unknown": [],
        },
        summary={"total": 2, "healthy": 1, "failed": 1, "unknown": 0},
    )
    result = get_latest_operational_result(session_id="store-active")
    assert result is not None
    assert result.operation_type == "provider_wide_health"
    assert result.provider == "railway"
    assert result.scope == "provider_wide"
    assert len(result.result_payload["services"]) == 2


def test_render_history_persistence():
    store_provider_wide_health_result(
        session_id="store-history",
        provider="railway",
        payload={"services": _rows(), "counts": {"total": 2}, "failures": [], "unknown": []},
        summary={"total": 2},
    )
    record_render_history(session_id="store-history", output_format="table", filter_mode="all")
    record_render_history(session_id="store-history", output_format="json", filter_mode="failed")

    result = get_latest_operational_result(session_id="store-history")
    assert result is not None
    assert len(result.render_history) == 2
    assert result.render_history[0]["output_format"] == "table"
    assert result.render_history[1]["filter_mode"] == "failed"
