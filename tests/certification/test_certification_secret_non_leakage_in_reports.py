# SPDX-License-Identifier: Apache-2.0
"""P0.5 — certification: report composers must not leak injected secrets."""

from __future__ import annotations

_FAKE_SECRET = "vercel_super_secret_token_abcdefghijklmnopqrstuvwxyz123456"
_FAKE_BEARER = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.secret.payload"


def test_solo_final_report_does_not_leak_secrets() -> None:
    from aethos_core.solo_execution.solo_final_report import (
        compose_solo_chat_reply,
        compose_solo_greenfield_final_report,
    )

    journal = {
        "railway_deployment_id": "dep-1",
        "deployment_url": f"https://example.com/?token={_FAKE_SECRET}",
        "runtime_verification": {"verified": True, "detail": _FAKE_BEARER},
        "deploy_trigger_metadata": {"deployment_status": "SUCCESS"},
    }
    env_report = {"required_env_var_names": ["API_TOKEN"], "resolved_sources": {"API_TOKEN": _FAKE_SECRET}}
    plan = {"project": "p", "environment": "staging", "service_name": "svc", "repo": "org/repo", "branch": "main"}

    chat = compose_solo_chat_reply(
        plan=plan,
        git_remote={"repository": "org/repo", "branch": "main"},
        journal=journal,
        env_report=env_report,
        execution_status="completed",
        blocker_detail=_FAKE_SECRET,
    )
    report = compose_solo_greenfield_final_report(
        plan=plan,
        git_remote={"repository": "org/repo", "branch": "main"},
        journal=journal,
        env_report=env_report,
        execution_status="completed",
        logs_summary=_FAKE_BEARER,
    )
    for blob in (chat, report):
        assert _FAKE_SECRET not in blob
        assert _FAKE_BEARER not in blob


def test_provider_e2e_final_report_does_not_leak_secrets() -> None:
    from aethos_core.provider_e2e_orchestration.final_report import compose_provider_e2e_final_report

    evidence = {
        "env_applied_names": ["API_TOKEN"],
        "deployment_id": "dep-xyz",
        "deployment_url": f"https://app.example/?key={_FAKE_SECRET}",
        "verification": {"ok": True, "url": "https://health.example", "status_code": 200},
        "errors": [f"upstream rejected token {_FAKE_SECRET}"],
    }
    report = compose_provider_e2e_final_report(
        provider="railway",
        evidence=evidence,
        execution_status="completed",
        completion_advisory_text=_FAKE_BEARER,
    )
    assert _FAKE_SECRET not in report
    assert _FAKE_BEARER not in report
