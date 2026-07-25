# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8B.2 — deployment URL resolution tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.browser.deployment_url_resolution import (
    is_deployment_evidence_prompt,
    is_guessed_service_com_url,
    resolve_public_deployment_url,
)
from aethos_core.browser.runtime.browser_evidence_execution import execute_browser_evidence_job
from aethos_core.browser.runtime.browser_runtime import extract_url_from_request, run_deployment_evidence_capture
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store


@pytest.fixture
def browser_env(monkeypatch, tmp_path):
    root = tmp_path / "browser_artifacts"
    monkeypatch.setenv("BROWSER_ARTIFACTS_DIR", str(root))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def _seed_railway_inventory(*, name: str, url: str = "", service_id: str = "svc-1"):
    job = authority.create_job(
        title="Railway inventory",
        job_type="railway_services_inventory",
        params={
            "railway_inventory": {
                "items": [
                    {
                        "name": name,
                        "service_name": name,
                        "service_id": service_id,
                        "project_name": "main",
                        "url": url,
                    }
                ],
            },
        },
        source="test",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="ok",
        summary="ok",
        preview="ok",
        provider="railway_api",
        model="graphql",
        used_llm=False,
        fallback=False,
    )


def test_guessed_com_domain_forbidden():
    assert is_guessed_service_com_url("https://speakglobal-ai.com", "speakglobal-ai") is True
    assert is_guessed_service_com_url("https://app.up.railway.app", "speakglobal-ai") is False


def test_extract_url_never_invents_com_for_slug():
    _seed_railway_inventory(name="speakglobal-ai", url="")
    url = extract_url_from_request("capture screenshot of speakglobal-ai")
    assert url == ""
    assert "speakglobal-ai.com" not in url


def test_railway_public_url_from_inventory():
    _seed_railway_inventory(name="speakglobal-ai", url="https://speakglobal-ai-production.up.railway.app")
    resolution = resolve_public_deployment_url(provider="railway", target="speakglobal-ai")
    assert resolution.resolved is True
    assert "up.railway.app" in (resolution.public_url or "")
    assert resolution.resolution_source == "railway_service_domain"
    assert "speakglobal-ai.com" not in (resolution.public_url or "")


def test_railway_no_public_url_metadata_fallback(browser_env):
    _seed_railway_inventory(name="internal-only", url="")
    with patch(
        "aethos_core.browser.deployment_url_resolution._railway_token",
        return_value=None,
    ):
        result = run_deployment_evidence_capture(
            user_request="capture deployment evidence for internal-only",
            provider="railway",
            target="internal-only",
            session_id="dep-test",
        )
    assert result["ok"] is True
    assert result.get("metadata_only") is True
    types = {a["artifact_type"] for a in result.get("artifacts") or []}
    assert "deployment_metadata_only" in types
    assert "deployment_url_resolution" in types
    assert "browser_screenshot" not in types
    for art in result.get("artifacts") or []:
        assert "internal-only.com" not in str(art.get("source_url") or "")


@patch("aethos_core.runtime.browser_runtime.run_playwright_on_browser_thread")
def test_railway_deployment_evidence_capture_with_url(mock_thread, browser_env):
    mock_thread.side_effect = lambda fn, timeout=120.0: fn()
    _seed_railway_inventory(
        name="speakglobal-ai",
        url="https://speakglobal-ai-production.up.railway.app",
    )
    with patch(
        "aethos_core.browser.runtime.browser_capture.capture_page_evidence",
        return_value={
            "ok": True,
            "metadata": {"title": "App", "url": "https://speakglobal-ai-production.up.railway.app", "status_code": 200},
            "screenshot_bytes": b"\x89PNG\r\n",
            "dom_snapshot": {},
            "console_logs": [],
            "network_failures": [],
        },
    ):
        result = run_deployment_evidence_capture(
            user_request="capture deployment evidence for speakglobal-ai",
            provider="railway",
            target="speakglobal-ai",
        )
    assert result["ok"] is True
    assert "up.railway.app" in (result.get("url_resolution") or {}).get("public_url", "")
    assert any(a["artifact_type"] == "browser_screenshot" for a in result.get("artifacts") or [])


def test_deployment_evidence_job_execution_metadata_only(browser_env):
    _seed_railway_inventory(name="no-url-service", url="")
    job_executor.drain_queue_for_tests()
    with patch(
        "aethos_core.browser.deployment_url_resolution._railway_token",
        return_value=None,
    ), patch(
        "aethos_core.connections.credential_runtime_gate.check_provider_credential_gate",
        return_value={"ok": True, "provider": "railway", "credential_state": "validated"},
    ):
        job = authority.create_job(
            title="Deployment evidence",
            job_type="browser_capture_execution",
            params={
                "user_request": "capture deployment evidence for no-url-service",
                "operation_type": "browser_capture",
                "deployment_evidence": True,
                "capture_type": "full",
            },
            source="test",
            auto_run=False,
        )
        outcome = execute_browser_evidence_job(job)
    assert outcome["ok"] is True
    assert "metadata evidence instead" in outcome["summary"].lower()


def test_is_deployment_evidence_prompt():
    assert is_deployment_evidence_prompt("capture deployment evidence for speakglobal-ai")
    assert not is_deployment_evidence_prompt("capture screenshot of useinvoicepilot.com")
