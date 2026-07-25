# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent


def _load_local_module(name: str):
    path = _TESTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"aethos_local_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load test helper: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_job_utils = _load_local_module("job_test_utils")
drain_job_executor = _job_utils.drain_job_executor


@pytest.fixture(autouse=True)
def _isolate_job_executor():
    """Prevent background executor threads from leaking across tests."""
    from aethos_core.runtime.job_executor import job_executor

    job_executor.stop()
    job_executor.drain_queue_for_tests()
    yield
    job_executor.stop()
    job_executor.drain_queue_for_tests()
    drain_job_executor()


@pytest.fixture(autouse=True)
def _open_chat_api_for_tests(monkeypatch):
    """Local .env may enable multi-tenant auth; most tests expect open /api/v1/chat."""
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _solo_execution_default_disabled(monkeypatch):
    """Tests opt in to solo execution via _enable_solo or explicit env."""
    monkeypatch.setenv("AETHOS_SOLO_EXECUTION_MODE", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _mutation_flags_default_disabled(monkeypatch):
    """Tests opt in to mutation execution via mutation_enabled fixture or explicit env."""
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "false")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _compose_runtime_guard_test_mode():
    """Reset compose guard state and enforce test runtime mode during pytest."""
    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guard import (
        clear_compose_runtime_guard_for_tests,
    )
    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_store import (
        clear_compose_runtime_guardrails_records_for_tests,
    )

    clear_compose_runtime_guard_for_tests()
    clear_compose_runtime_guardrails_records_for_tests()
    yield
    clear_compose_runtime_guard_for_tests()
    clear_compose_runtime_guardrails_records_for_tests()
