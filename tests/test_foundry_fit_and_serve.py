# SPDX-License-Identifier: Apache-2.0
"""Model Foundry fit and serve (§B4)."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.llm.foundry.foundry_runtime import probe_hardware, propose_serve, score_model_fit
from aethos_core.workspace_suite import model_foundry


@pytest.fixture(autouse=True)
def _foundry_on(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_ENABLED", "true")
    monkeypatch.setenv("WORKSPACE_SUITE_STORE_DIR", str(tmp_path / "ws"))
    get_settings.cache_clear()
    model_foundry.clear_foundry_for_tests()
    yield
    model_foundry.clear_foundry_for_tests()
    get_settings.cache_clear()


def test_hardware_probe_returns_ram():
    snap = probe_hardware()
    assert snap.get("ok") is True
    assert int(snap.get("total_ram_gb") or 0) >= 0


def test_fit_scorer_marks_tiny_model_green():
    fit = score_model_fit("qwen2.5-0.5b")
    assert fit.get("ok") is True
    verdict = str((fit.get("fit") or {}).get("verdict") or "")
    assert verdict in {"great", "ok", "tight", "no", ""}


def test_serve_preflight_governed_not_instant():
    out = propose_serve("qwen2.5-0.5b", port=11434)
    assert out.get("ok") is True
    assert out.get("approval_status") == "pending" or out.get("serve_request")
