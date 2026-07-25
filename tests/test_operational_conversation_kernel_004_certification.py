# SPDX-License-Identifier: Apache-2.0
"""KERNEL_004 certification — observability, gaps, smoke runner, Wave 2 deletion."""

from __future__ import annotations

import importlib

import pytest

from aethos_core.observability.kernel_observability import (
    KERNEL_COUNTER_NAMES,
    KernelTurnObservation,
    all_kernel_metrics_emitted,
    kernel_metrics_snapshot,
    record_kernel_turn,
)
from aethos_core.observability.metrics import clear_metrics_for_tests
from aethos_core.operational_session.kernel_gap_registry import gap_registry_summary, high_severity_open_gaps
from aethos_core.operational_session.router_retirement import wave_1_retirement_stats


@pytest.fixture(autouse=True)
def _clean_metrics():
    clear_metrics_for_tests()
    yield
    clear_metrics_for_tests()


def test_no_high_severity_open_kernel_gaps():
    assert high_severity_open_gaps() == []
    summary = gap_registry_summary()
    assert summary["meets_no_high_open_requirement"] is True


def test_kernel_metrics_emitted_on_turn():
    record_kernel_turn(KernelTurnObservation(ok=True, intent="operational_kernel_fetch_logs", subject_resolved=True))
    record_kernel_turn(
        KernelTurnObservation(ok=False, intent="operational_kernel_needs_target", subject_resolved=False, tool_failed=True)
    )
    snap = kernel_metrics_snapshot()
    for name in KERNEL_COUNTER_NAMES:
        assert name in snap["kernel_counters"]


def test_wave_2_physical_deletion_threshold():
    stats = wave_1_retirement_stats()
    assert stats["wave_2_deleted"] >= 5
    assert stats["deletion_percent"] >= 50.0


def test_deleted_router_modules_absent():
    for module in (
        "aethos_core.chat.railway_named_service_log_router",
        "aethos_core.chat.multi_provider_health_router",
        "aethos_core.operational_target_resolution.routing",
    ):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(module)


def test_kernel_smoke_runner_passes():
    from aethos_core.cli.kernel_smoke_runner import run_kernel_smoke

    bundle = run_kernel_smoke(json_out=False)
    assert bundle["status"] == "PASS"
    assert bundle["pass_rate"] >= 95.0
