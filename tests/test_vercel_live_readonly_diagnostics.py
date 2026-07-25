# SPDX-License-Identifier: Apache-2.0
"""Vercel live readonly diagnostics tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.provider_readonly_intent.readonly_intent_classifier import classify_vercel_readonly_intent
from aethos_core.provider_readonly_intent.readonly_provider_router import route_readonly_provider_question
from aethos_core.providers.vercel.diagnostics.build_log_analyzer import analyze_build_logs
from aethos_core.providers.vercel.diagnostics.diagnosis_composer import compose_vercel_live_diagnosis_reply
from aethos_core.providers.vercel.diagnostics.vercel_live_diagnostics import run_vercel_live_diagnostics


@pytest.fixture
def sample_evidence() -> dict:
    return {
        "ok": True,
        "operation": "live_diagnosis",
        "project_name": "lifeos",
        "project": {
            "ok": True,
            "project_name": "lifeos",
            "details": {
                "name": "lifeos",
                "framework": "nextjs",
                "repo_link": "pilotmain/lifeos",
                "production_branch": "main",
                "production_url": "lifeos.vercel.app",
            },
        },
        "deployments": {
            "ok": True,
            "deployments": [
                {
                    "id": "dpl_failed_1",
                    "state": "error",
                    "target": "production",
                    "branch": "main",
                    "commit": "abc123def456",
                    "created_at": "2026-05-20T00:00:00Z",
                    "url": "https://lifeos.vercel.app",
                    "error_message": "Command \"npm run build\" exited with 1",
                },
                {
                    "id": "dpl_ok_2",
                    "state": "ready",
                    "target": "production",
                    "branch": "main",
                    "commit": "111222333444",
                    "created_at": "2026-05-19T00:00:00Z",
                    "url": "https://lifeos.vercel.app",
                },
            ],
        },
        "latest_deployment": {
            "id": "dpl_failed_1",
            "state": "error",
            "branch": "main",
            "commit": "abc123def456",
            "created_at": "2026-05-20T00:00:00Z",
            "url": "https://lifeos.vercel.app",
            "error_message": "Command \"npm run build\" exited with 1",
        },
        "failed_deployment": {
            "id": "dpl_failed_1",
            "state": "error",
            "branch": "main",
            "commit": "abc123def456",
            "created_at": "2026-05-20T00:00:00Z",
            "url": "https://lifeos.vercel.app",
            "error_message": "Command \"npm run build\" exited with 1",
        },
        "logs": {
            "ok": True,
            "deployment_id": "dpl_failed_1",
            "log_lines": ["Error: npm run build failed", "Build failed with exit code 1"],
            "events": [{"type": "stderr", "text": "Error: npm run build failed"}],
        },
        "build_analysis": {
            "ok": True,
            "error_lines": ["Error: npm run build failed"],
            "summary": "Detected 1 build error line(s) in deployment logs.",
        },
        "runtime_analysis": {"ok": False, "runtime_lines": [], "summary": "No runtime error lines detected in API log excerpt."},
        "domain_health": {
            "ok": True,
            "summary": "1/1 checked domain(s) reachable.",
            "checks": [{"domain": "lifeos.vercel.app", "reachable": True, "status_code": 200, "summary": "HTTP 200"}],
        },
        "env_metadata": {"ok": True, "env_count": 2, "env_metadata": [{"key": "API_URL", "target": "production"}]},
        "github_correlation": {
            "ok": True,
            "available": True,
            "lines": ["GitHub workflow **CI** run #12 failed on `main`."],
            "evidence": {
                "available": True,
                "repository": "pilotmain/lifeos",
                "workflow_diagnostic": {"latest_failed_run": {"name": "CI", "run_number": 12, "head_branch": "main"}},
            },
        },
    }


def test_classifier_maps_vercel_live_operations() -> None:
    assert classify_vercel_readonly_intent("diagnose vercel deployments for lifeos").operation == "live_diagnosis"
    assert classify_vercel_readonly_intent("why did vercel deployment fail for lifeos").operation == "failed_deployment"


def test_build_log_analyzer_extracts_errors() -> None:
    result = analyze_build_logs(
        {"ok": True, "log_lines": ["Installing deps", "Error: build failed"], "events": [], "deployment_id": "d1"}
    )
    assert result["error_lines"]
    assert "build failed" in result["error_lines"][0].lower()


def test_compose_live_diagnosis_includes_required_sections(sample_evidence: dict) -> None:
    reply = compose_vercel_live_diagnosis_reply(sample_evidence, operation="live_diagnosis")
    assert reply.startswith("Vercel deployment diagnostics")
    assert "Latest deployment:" in reply
    assert "Build/runtime evidence:" in reply
    assert "Domain health:" in reply
    assert "GitHub source correlation:" in reply
    assert "Findings:" in reply
    assert "Next readonly evidence step:" in reply
    assert "No mutation has been performed." in reply


@patch("aethos_core.providers.vercel.diagnostics.vercel_live_diagnostics.collect_vercel_live_evidence")
def test_run_vercel_live_diagnostics_meta(mock_collect, sample_evidence: dict) -> None:
    mock_collect.return_value = sample_evidence
    reply, meta = run_vercel_live_diagnostics("token", project_name="lifeos", operation="live_diagnosis")
    assert "Vercel deployment diagnostics" in reply
    assert meta["vercel_live_diagnostics"] == "true"
    assert meta["github_correlation"] == "true"
    assert meta["failed_deployment"] == "true"


@patch("aethos_core.providers.vercel.diagnostics.vercel_live_diagnostics.collect_vercel_live_evidence")
def test_route_readonly_vercel_deployments_with_token(mock_collect, sample_evidence: dict) -> None:
    mock_collect.return_value = sample_evidence
    with patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={"auth_method": "api_token", "credential_id": "vercel-cred", "block_reason": None},
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="test-token",
    ):
        result = route_readonly_provider_question("can you inspect Vercel deployments for lifeos?", session_id="vercel-live")
    assert result is not None
    assert result.meta.get("readonly_provider") == "vercel"
    assert result.meta.get("vercel_live_diagnostics") == "true"
    assert "Vercel deployment guidance" not in result.reply
    assert "Latest deployment:" in result.reply
    assert "npm run build" in result.reply or "build error" in result.reply.lower()


def test_missing_token_gives_exact_blocker() -> None:
    from aethos_core.provider_readonly_intent.vercel_readonly_router import compose_vercel_readonly_blocker_reply

    with patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={"auth_method": None, "credential_id": None, "block_reason": "missing"},
    ), patch(
        "aethos_core.runtime.browser_capability.get_browser_capability_status",
        return_value={"enabled": False, "execution_ready": False, "execution_label": "Playwright runtime not ready"},
    ), patch(
        "aethos_core.runtime.browser_runtime.browser_inventory_refresh_blocked_reason",
        return_value=(True, "Playwright runtime not ready"),
    ):
        routed = compose_vercel_readonly_blocker_reply(
            "can you inspect Vercel deployments?",
            session_id="vercel-blocked-live",
        )
    assert routed is not None
    reply, intent, _meta = routed
    assert intent == "vercel_readonly_blocked"
    assert "Vercel readonly execution is blocked" in reply
    assert "VERCEL_API_TOKEN missing" in reply
    assert "Vercel inventory unavailable" in reply
    assert "Vercel deployment guidance" not in reply
