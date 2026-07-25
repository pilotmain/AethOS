# SPDX-License-Identifier: Apache-2.0
"""Production hardening doctor profiles and Phase 4 cloud inventory."""

from __future__ import annotations

import pytest


def test_safe_defaults_break_glass_warning_when_acknowledged(monkeypatch) -> None:
    monkeypatch.setenv("HOST_EXECUTOR_ENABLED", "true")
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    monkeypatch.setenv("AETHOS_OPERATOR_BREAK_GLASS_ACKNOWLEDGED", "true")
    monkeypatch.setenv("AETHOS_DOCTOR_PROFILE", "development")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.enterprise.safe_defaults import audit_safe_defaults

    audit = audit_safe_defaults()
    assert audit["ok"] is True
    assert audit["break_glass_relaxed"] is True
    assert audit["break_glass_violations"]


def test_safe_defaults_fail_in_strict_profile(monkeypatch) -> None:
    monkeypatch.setenv("HOST_EXECUTOR_ENABLED", "true")
    monkeypatch.setenv("AETHOS_DOCTOR_PROFILE", "strict")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.enterprise.safe_defaults import audit_safe_defaults

    audit = audit_safe_defaults()
    assert audit["ok"] is False
    assert audit["hard_failures"]


def test_doctor_safe_defaults_warning_not_fail_in_dev(monkeypatch) -> None:
    monkeypatch.setenv("HOST_EXECUTOR_ENABLED", "true")
    monkeypatch.setenv("AETHOS_OPERATOR_BREAK_GLASS_ACKNOWLEDGED", "true")
    monkeypatch.setenv("AETHOS_DOCTOR_PROFILE", "development")
    monkeypatch.setenv("TELEGRAM_TUNNEL_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.enterprise.doctor import run_doctor_checks

    result = run_doctor_checks(probe_api=False, probe_web=False, category="security")
    check = result["checks"][0]
    assert check["name"] == "safe_defaults"
    assert check["status"] == "WARNING"


def test_doctor_tunnel_pass_when_status_running(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_TUNNEL_ENABLED", "true")
    monkeypatch.setenv("AETHOS_DOCTOR_PROFILE", "development")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(
        "aethos_core.runtime.tunnel.tunnel_manager.tunnel_status",
        lambda: {
            "ok": True,
            "tunnel": {
                "status": "running",
                "public_url": "https://example.ngrok-free.dev",
            },
        },
    )
    from aethos_core.enterprise.doctor import run_doctor_checks

    result = run_doctor_checks(probe_api=False, probe_web=False, category="tunnel")
    check = result["checks"][0]
    assert check["name"] == "ngrok_tunnel"
    assert check["status"] == "PASS"


def test_doctor_tunnel_warning_when_not_running(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_TUNNEL_ENABLED", "true")
    monkeypatch.setenv("AETHOS_DOCTOR_PROFILE", "development")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.enterprise.doctor import run_doctor_checks

    result = run_doctor_checks(probe_api=False, probe_web=False, category="tunnel")
    check = result["checks"][0]
    assert check["name"] == "ngrok_tunnel"
    assert check["status"] in {"WARNING", "FAIL"}
    assert "aethos tunnel start" in str(check.get("fix_hint"))


def test_list_cloud_readonly_inventory_disabled() -> None:
    from aethos_core.providers.cloud.readonly_inventory import list_cloud_readonly_inventory

    out = list_cloud_readonly_inventory()
    assert out["enabled"] is False


def test_list_cloud_readonly_inventory_enabled(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_READONLY_INVENTORY_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.providers.cloud.readonly_inventory import list_cloud_readonly_inventory

    monkeypatch.setattr(
        "aethos_core.provider_skills.kubernetes.skill._kubectl_inventory",
        lambda: {"ok": False, "error": "kubectl not found.", "provider": "kubernetes"},
    )
    out = list_cloud_readonly_inventory(session_id="test")
    assert out["enabled"] is True
    assert len(out["providers"]) == 5
    k8s = next(row for row in out["providers"] if row["provider"] == "kubernetes")
    assert k8s["ok"] is False


def test_cloudflare_skill_without_token() -> None:
    from aethos_core.provider_skills.cloudflare.skill import CloudflareProviderSkill

    skill = CloudflareProviderSkill()
    payload = skill.discover(force=True)
    assert payload["ok"] is False


def test_runtime_cloud_inventory_route(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_READONLY_INVENTORY_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.get("/api/v1/runtime/cloud/inventory")
    assert response.status_code == 200
    body = response.json()
    assert body.get("enabled") is True
    assert body.get("providers")
