# SPDX-License-Identifier: Apache-2.0
"""CORS must allow credentialed localhost UI origins in local dev."""

from __future__ import annotations

from aethos_core.api.main import _cors_allowed_origins


def test_local_dev_cors_includes_localhost_3000(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    origins = _cors_allowed_origins()
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "*" not in origins
    get_settings.cache_clear()
