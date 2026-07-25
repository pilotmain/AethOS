# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8K — Enterprise readiness and productization."""

from __future__ import annotations

import pytest

from aethos_core.enterprise.actionable_errors import build_actionable_error, format_actionable_error_text
from aethos_core.enterprise.config_center import build_configuration_center
from aethos_core.enterprise.demo_mode import clear_demo_mode_for_tests, demo_status, disable_demo_mode, enable_demo_mode, is_demo_mode
from aethos_core.enterprise.doctor import run_doctor_checks
from aethos_core.enterprise.health_dashboard import build_operational_health_dashboard
from aethos_core.enterprise.safe_defaults import audit_safe_defaults
from aethos_core.enterprise.setup_wizard import build_setup_wizard


@pytest.fixture(autouse=True)
def _clean():
    clear_demo_mode_for_tests()
    yield
    clear_demo_mode_for_tests()


def test_doctor_returns_structured_checks():
    result = run_doctor_checks(probe_api=False, probe_web=False)
    assert result.get("overall") in ("PASS", "WARNING", "FAIL")
    assert result.get("checks")
    assert all(c.get("status") in ("PASS", "WARNING", "FAIL") for c in result["checks"])


def test_doctor_actionable_errors_on_failures():
    err = build_actionable_error("api_unreachable", detail="connection refused")
    text = format_actionable_error_text(err)
    assert "What failed" in text
    assert err.get("next_command")


def test_safe_defaults_off_by_default(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    monkeypatch.setenv("HOST_EXECUTOR_ENABLED", "false")
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "false")
    get_settings.cache_clear()
    audit = audit_safe_defaults()
    assert audit.get("checks", {}).get("browser_off_by_default") is True
    assert audit.get("checks", {}).get("no_unrestricted_shell") is True
    assert audit.get("autonomous_execution_blocked") is True
    get_settings.cache_clear()


def test_config_center_no_raw_secrets():
    config = build_configuration_center()
    assert config.get("no_secrets_exposed") is True
    preview = config.get("settings_preview") or {}
    assert "sk-ant" not in str(preview)
    assert config.get("env", {}).get("restart_required_hint")


def test_demo_mode_lifecycle():
    assert is_demo_mode() is False
    enable = enable_demo_mode()
    assert enable.get("enabled") is True
    assert is_demo_mode() is True
    status = demo_status()
    assert status.get("label") == "DEMO DATA"
    overlay = status.get("sample_counts") or {}
    assert overlay.get("recommendations", 0) >= 1
    disable_demo_mode()
    assert is_demo_mode() is False


def test_demo_samples_marked_demo():
    enable_demo_mode()
    from aethos_core.enterprise.demo_mode import get_demo_overlay

    overlay = get_demo_overlay()
    assert overlay.get("demo") is True
    assert overlay.get("label") == "DEMO DATA"
    for rec in overlay.get("recommendations") or []:
        assert rec.get("demo") is True


def test_health_dashboard_components():
    health = build_operational_health_dashboard()
    assert health.get("components")
    assert "scheduler" in health["components"]
    assert "reliability" in health["components"]
    assert health.get("overall") in ("healthy", "degraded", "unhealthy")


def test_setup_wizard_progress():
    wizard = build_setup_wizard()
    assert wizard.get("steps")
    assert wizard.get("total_steps", 0) >= 5
    assert 0 <= float(wizard.get("progress") or 0) <= 1


def test_doctor_vault_check():
    result = run_doctor_checks(probe_api=False, probe_web=False, category="vault")
    assert result.get("checks")
    assert result["checks"][0].get("name") == "encryption_vault"
