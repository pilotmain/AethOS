# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def mem_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()


def test_chat_correction_ignores_label(mem_env):
    out = resolve_handler("cdn is not a project", session_id="default")
    assert out is not None
    reply, intent, _meta = out
    assert intent == "vercel_memory_correction"
    assert "cdn" in reply
    assert "ignore" in reply.lower()
