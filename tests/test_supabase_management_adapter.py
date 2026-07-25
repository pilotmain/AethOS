# SPDX-License-Identifier: Apache-2.0
"""Supabase Management API adapter — gating, token guard, and parsing (handoff §3)."""

from __future__ import annotations

from typing import Any

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.supabase import management_adapter as m


class _FakeResp:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class _FakeClient:
    def __init__(self, resp: _FakeResp) -> None:
        self._resp = resp
        self.calls: list[tuple[str, str]] = []

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, *a: Any) -> None:
        return None

    def get(self, url: str, headers: dict[str, str] | None = None) -> _FakeResp:
        self.calls.append(("GET", url))
        return self._resp

    def post(self, url: str, headers: dict[str, str] | None = None, json: Any = None) -> _FakeResp:
        self.calls.append(("POST", url))
        return self._resp


@pytest.fixture(autouse=True)
def _enable(monkeypatch):
    monkeypatch.setenv("PROVISIONING_ORCHESTRATION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _patch_http(monkeypatch, resp: _FakeResp) -> None:
    monkeypatch.setattr(m, "resolve_access_token", lambda: "sbp_test_token")
    monkeypatch.setattr(m.httpx, "Client", lambda *a, **k: _FakeClient(resp))


def test_list_projects_gated_when_flag_off(monkeypatch):
    monkeypatch.setenv("PROVISIONING_ORCHESTRATION_ENABLED", "false")
    get_settings.cache_clear()
    out = m.list_projects()
    assert out["ok"] is False
    assert out["error"] == "provisioning_disabled"


def test_list_projects_requires_token(monkeypatch):
    monkeypatch.setattr(m, "resolve_access_token", lambda: "")
    out = m.list_projects()
    assert out["ok"] is False
    assert out["error"] == "no_management_token"


def test_list_projects_parses_account_wide(monkeypatch):
    _patch_http(
        monkeypatch,
        _FakeResp(200, [
            {"id": "abc123", "name": "killit", "region": "us-east-1", "organization_id": "org1"},
            {"id": "def456", "name": "side-project", "region": "eu-west-1"},
        ]),
    )
    out = m.list_projects()
    assert out["ok"] is True
    assert out["count"] == 2
    assert out["projects"][0]["ref"] == "abc123"
    assert out["projects"][0]["url"] == "https://abc123.supabase.co"


def test_get_project_keys_separates_service_role(monkeypatch):
    _patch_http(
        monkeypatch,
        _FakeResp(200, [
            {"name": "anon", "api_key": "anon-key-value"},
            {"name": "service_role", "api_key": "service-role-secret"},
        ]),
    )
    out = m.get_project_keys("abc123")
    assert out["ok"] is True
    assert out["url"] == "https://abc123.supabase.co"
    assert out["anon_key"] == "anon-key-value"
    assert out["service_role_key"] == "service-role-secret"
    assert out["has_service_role"] is True


def test_get_project_keys_requires_ref(monkeypatch):
    monkeypatch.setattr(m, "resolve_access_token", lambda: "sbp_test_token")
    out = m.get_project_keys("")
    assert out["ok"] is False
    assert out["error"] == "missing_ref"


def test_rejected_token_is_honest(monkeypatch):
    _patch_http(monkeypatch, _FakeResp(401, {}))
    out = m.list_projects()
    assert out["ok"] is False
    assert out["error"] == "rejected"
    assert out["http_status"] == 401


def test_create_project_posts_and_parses(monkeypatch):
    _patch_http(monkeypatch, _FakeResp(201, {"id": "new789", "name": "fresh", "status": "COMING_UP"}))
    out = m.create_project(name="fresh", organization_id="org1", region="us-east-1", db_pass="x" * 16)
    assert out["ok"] is True
    assert out["ref"] == "new789"
    assert out["url"] == "https://new789.supabase.co"


# ---- §4: management source wiring into governed env-completion collection ----

from aethos_core.provider_e2e_orchestration.env_completion import supabase_browser_phase as bp

_ALL_NAMES = ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]


def _stub_adapter(monkeypatch, **overrides):
    defaults = {
        "management_enabled": lambda: True,
        "has_management_token": lambda: True,
        "list_projects": lambda: {"ok": True, "projects": [{"ref": "abc123"}], "count": 1},
        "get_project_keys": lambda ref: {
            "ok": True,
            "ref": ref,
            "url": f"https://{ref}.supabase.co",
            "anon_key": "anon-val",
            "service_role_key": "service-secret",
            "has_service_role": True,
        },
        "create_project": lambda **k: {"ok": True, "ref": "new789", "name": k.get("name"), "url": "https://new789.supabase.co"},
    }
    defaults.update(overrides)
    for name, fn in defaults.items():
        monkeypatch.setattr(m, name, fn)


def test_management_source_gated_when_disabled(monkeypatch):
    _stub_adapter(monkeypatch, management_enabled=lambda: False)
    values, trace = bp.resolve_supabase_env_via_management(params={}, requested_names=_ALL_NAMES)
    assert values == {}
    assert trace["reason"] == "provisioning_disabled"


def test_management_source_requires_token(monkeypatch):
    _stub_adapter(monkeypatch, has_management_token=lambda: False)
    values, trace = bp.resolve_supabase_env_via_management(params={}, requested_names=_ALL_NAMES)
    assert values == {}
    assert trace["reason"] == "no_management_token"


def test_management_source_resolves_selected_project(monkeypatch):
    _stub_adapter(monkeypatch)
    values, trace = bp.resolve_supabase_env_via_management(
        params={"supabase_project_ref": "abc123"},
        requested_names=_ALL_NAMES,
    )
    assert values["NEXT_PUBLIC_SUPABASE_URL"] == "https://abc123.supabase.co"
    assert values["NEXT_PUBLIC_SUPABASE_ANON_KEY"] == "anon-val"
    assert values["SUPABASE_SERVICE_ROLE_KEY"] == "service-secret"
    assert trace["ok"] is True
    # Trace never carries secret values.
    assert "service-secret" not in str(trace)


def test_management_source_skips_service_role_when_not_requested(monkeypatch):
    _stub_adapter(monkeypatch)
    values, _ = bp.resolve_supabase_env_via_management(
        params={"supabase_project_ref": "abc123"},
        requested_names=["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
    )
    assert "SUPABASE_SERVICE_ROLE_KEY" not in values


def test_management_source_needs_selection_when_many_projects(monkeypatch):
    _stub_adapter(
        monkeypatch,
        list_projects=lambda: {"ok": True, "projects": [{"ref": "a"}, {"ref": "b"}], "count": 2},
    )
    values, trace = bp.resolve_supabase_env_via_management(params={}, requested_names=_ALL_NAMES)
    assert values == {}
    assert trace["reason"] == "project_not_selected"


def test_management_source_auto_selects_single_project(monkeypatch):
    _stub_adapter(monkeypatch)
    values, trace = bp.resolve_supabase_env_via_management(params={}, requested_names=_ALL_NAMES)
    assert trace["auto_selected_ref"] == "abc123"
    assert values["NEXT_PUBLIC_SUPABASE_URL"] == "https://abc123.supabase.co"


def test_management_source_creates_project_when_requested(monkeypatch):
    _stub_adapter(monkeypatch)
    values, trace = bp.resolve_supabase_env_via_management(
        params={"supabase_create_project": {"name": "fresh", "organization_id": "org1"}},
        requested_names=_ALL_NAMES,
    )
    assert trace["created_project"]["ref"] == "new789"
    assert trace["ref"] == "new789"
    assert values["NEXT_PUBLIC_SUPABASE_URL"] == "https://new789.supabase.co"


def test_submitted_values_win_over_management(monkeypatch):
    _stub_adapter(monkeypatch)
    params = {
        "submitted_env_values": {"NEXT_PUBLIC_SUPABASE_URL": "https://manual.supabase.co"},
        "supabase_project_ref": "abc123",
        "missing_env_names": _ALL_NAMES,
    }
    collected, trace = bp.collect_supabase_values_from_sources(
        plan={}, params={**params, "browser_extraction_enabled": False}
    )
    assert collected["NEXT_PUBLIC_SUPABASE_URL"] == "https://manual.supabase.co"
    assert collected["NEXT_PUBLIC_SUPABASE_ANON_KEY"] == "anon-val"
    assert "submitted_params" in trace["sources"]
    assert "management_api" in trace["sources"]
