# SPDX-License-Identifier: Apache-2.0
"""Long-term memory recall across sessions (§B5)."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.memory.long_term_store import recall_facts, remember_fact


@pytest.fixture(autouse=True)
def _vector_on(monkeypatch):
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_fact_recalled_in_second_session():
    remember_fact("Operator prefers Railway for atlas-trader deploys.", tags=["preference"])
    out = recall_facts("atlas-trader deploy preference", limit=5)
    assert out.get("ok") is True
    assert out.get("count", 0) >= 1
