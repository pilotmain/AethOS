# SPDX-License-Identifier: Apache-2.0
"""§8 observability export — SLO evaluation, error sink fallback, telemetry status."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.observability import metrics, telemetry


@pytest.fixture(autouse=True)
def clean_metrics(monkeypatch):
    metrics.clear_metrics_for_tests()
    monkeypatch.setenv("SLO_CHAT_LATENCY_MS", "1000")
    monkeypatch.setenv("SLO_MUTATION_SUCCESS_RATE", "0.9")
    get_settings.cache_clear()
    yield
    metrics.clear_metrics_for_tests()
    get_settings.cache_clear()


def test_slo_ok_with_no_traffic():
    result = telemetry.evaluate_slos()
    assert result["ok"] is True
    assert {r["slo"] for r in result["slos"]} == {"chat_latency_ms_avg", "mutation_success_rate"}


def test_chat_latency_breach_is_warning():
    telemetry.record_chat_latency_ms(5000.0)
    result = telemetry.evaluate_slos()
    chat = next(r for r in result["slos"] if r["slo"] == "chat_latency_ms_avg")
    assert chat["ok"] is False and chat["severity"] == "warning"
    assert result["ok"] is False


def test_mutation_success_rate_breach_is_critical():
    telemetry.record_mutation_result(True)
    telemetry.record_mutation_result(False)
    telemetry.record_mutation_result(False)
    result = telemetry.evaluate_slos()
    mut = next(r for r in result["slos"] if r["slo"] == "mutation_success_rate")
    assert mut["ok"] is False and mut["severity"] == "critical"
    assert abs(mut["actual"] - (1 / 3)) < 0.01


def test_capture_exception_falls_back_to_log():
    # No sentry configured → must not raise.
    telemetry.capture_exception(ValueError("boom"), where="unit-test")


def test_telemetry_status_shape():
    st = telemetry.telemetry_status()
    assert "otel_active" in st and "error_sink_active" in st
