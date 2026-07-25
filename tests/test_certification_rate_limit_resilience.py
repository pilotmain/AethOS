# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98G — certification and runtime Railway rate-limit resilience."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from aethos_core.operational_planner.adapters.railway_wide_health import (
    collect_railway_service_health_rows,
    compose_railway_provider_wide_health_reply,
)
from aethos_core.operational_planner.adapters.railway_wide_health_cache import (
    clear_cache_for_tests,
    load_cached_railway_health_rows,
    save_cached_railway_health_rows,
)
from aethos_core.operational_planner.adapters.railway_wide_health_certification import (
    certification_fixture_rows,
    is_certification_mode,
)


def setup_function() -> None:
    clear_cache_for_tests()
    os.environ.pop("AETHOS_CERTIFICATION_MODE", None)


def test_certification_mode_uses_railway_fixture(monkeypatch) -> None:
    monkeypatch.setenv("AETHOS_CERTIFICATION_MODE", "true")
    assert is_certification_mode() is True
    rows, error = collect_railway_service_health_rows()
    assert error is None
    assert len(rows) == 3
    assert any(r.get("service") == "MongoDB" and r.get("health") == "failed" for r in rows)


def test_certification_compose_uses_fixture_without_live_api(monkeypatch) -> None:
    monkeypatch.setenv("AETHOS_CERTIFICATION_MODE", "true")

    def _fail_live():
        raise AssertionError("live Railway API must not be called in certification mode")

    with patch("aethos_core.providers.railway.discovery.discover_railway_inventory", side_effect=_fail_live):
        body, intent, meta = compose_railway_provider_wide_health_reply(session_id="cert-98g")
    assert "MongoDB" in body or "failed" in body.lower()
    assert intent is not None
    assert meta.get("provider") == "railway"


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
def test_rate_limit_falls_back_to_cached_snapshot(mock_discover) -> None:
    save_cached_railway_health_rows(certification_fixture_rows())
    mock_discover.return_value = type(
        "Inv",
        (),
        {"error": "Rate limit exceeded, please try again in 120 seconds", "projects": []},
    )()
    rows, error = collect_railway_service_health_rows()
    assert rows
    assert error is not None
    assert str(error).startswith("cached_due_to_rate_limit")
    body, intent, meta = compose_railway_provider_wide_health_reply(session_id="rate-cache")
    assert "cached_due_to_rate_limit" in body
    assert "MongoDB" in body
    assert meta.get("source") == "cached_due_to_rate_limit"
    assert intent != "railway_provider_wide_health_unavailable"


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
def test_rate_limit_without_cache_gives_bounded_blocker(mock_discover) -> None:
    clear_cache_for_tests()
    mock_discover.return_value = type(
        "Inv",
        (),
        {"error": "Rate limit exceeded, please try again in 90 seconds", "projects": []},
    )()
    rows, error = collect_railway_service_health_rows()
    assert not rows
    assert "rate limit" in str(error).lower()
    body, intent, _meta = compose_railway_provider_wide_health_reply(session_id="rate-blocked")
    assert intent == "railway_provider_wide_health_rate_limited"
    assert "rate-limited" in body.lower()
    assert "Try again after" in body
    assert "No mutation has been performed" in body
    assert "mutation preflight" not in body.lower()


@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
def test_successful_collect_updates_cache(mock_discover) -> None:
    service = type("Svc", (), {"name": "api", "id": "s1", "status": "online", "latest_deployment": None})()
    env = type("Env", (), {"name": "production", "services": [service]})()
    project = type("Proj", (), {"name": "pilotos", "environments": [env]})()
    mock_discover.return_value = type("Inv", (), {"error": None, "projects": [project]})()
    rows, error = collect_railway_service_health_rows()
    assert rows
    assert error is None
    cached, _at = load_cached_railway_health_rows()
    assert cached
    assert cached[0].get("service") == "api"
