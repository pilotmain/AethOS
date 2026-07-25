# SPDX-License-Identifier: Apache-2.0
"""UI vault keys → all models; tenant-scoped deploy approvals."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.connections.validation_status import CONFIGURED, INVALID, VALIDATED
from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
    compose_greenfield_preflight_reply,
    create_railway_greenfield_preflight_job,
    RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
)


@pytest.fixture(autouse=True)
def _clear_settings():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_ui_key_all_models(monkeypatch, tmp_path):
    """Vault Anthropic key (no env) → all flagships configured + honored; stale row skipped."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "")

    from aethos_core.llm.effective_model import (
        effective_model_for_agent_tool_loop,
        resolve_effective_model,
    )
    from aethos_core.llm.model_catalog import list_available_models
    from aethos_core.llm.model_providers import resolve_model_provider_key
    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    vault = get_credential_vault()
    vault.clear_all_for_tests()
    good = vault.store_api_token(
        provider="anthropic",
        label="UI Anthropic",
        token="sk-ant-ui-good-key-123456789012",
    )
    stale = vault.store_api_token(
        provider="anthropic",
        label="Stale Anthropic",
        token="sk-ant-ui-stale-key-123456789012",
    )
    vault.mark_validation_result(good.credential_id, status=VALIDATED, ok=True)
    vault.mark_validation_result(stale.credential_id, status=CONFIGURED, ok=False)
    vault.mark_validation_result(stale.credential_id, status=INVALID, ok=False)

    assert resolve_model_provider_key("anthropic") == "sk-ant-ui-good-key-123456789012"

    anthropic_rows = [
        r
        for r in list_available_models(include_unconfigured=False)
        if r.get("provider") == "anthropic"
    ]
    ids = {r["id"] for r in anthropic_rows}
    assert "anthropic:claude-opus-4-6" in ids
    assert "anthropic:claude-sonnet-4-6" in ids
    assert "anthropic:claude-haiku-4-5" in ids
    assert all(r.get("configured") for r in anthropic_rows)

    effective = resolve_effective_model(turn_override="anthropic:claude-opus-4-6")
    assert effective.model == "claude-opus-4-6"
    tool = effective_model_for_agent_tool_loop(effective)
    assert tool is not None
    assert tool.catalog_id == "anthropic:claude-opus-4-6"


def test_deploy_approval_surfaces_tenant_wide(monkeypatch):
    """Greenfield preflight in chat session appears in tenant Approvals (not panel session id)."""
    from aethos_core.jobs.pending_job_approval_resolution import list_pending_operational_approvals
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        RailwayExecutionEnablementPolicy,
    )
    from aethos_core.runtime.jobs import job_store

    chat_session = "sess-chat-deploy-test"
    plan = {
        "repo": "pilotmain/killit",
        "branch": "main",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "killit",
        "risk_tier": "standard",
    }
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_preflight.authority.create_job",
        lambda **kwargs: job_store.create(
            title=kwargs.get("title") or "test",
            job_type=kwargs.get("job_type") or RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
            params=kwargs.get("params") or {},
            source=kwargs.get("source") or "chat",
            session_id=kwargs.get("session_id") or chat_session,
            auto_run=False,
        ),
    )

    preflight = create_railway_greenfield_preflight_job(
        user_text="deploy killit to railway",
        session_id=chat_session,
        plan=plan,
        env_report={"required_env_var_names": [], "count": 0},
        local_source={"ok": True, "workspace_name": "killit"},
        git_remote={"ok": True, "repository": "pilotmain/killit", "branch": "main"},
    )
    job_id = str(preflight.get("job_id") or "")
    assert job_id

    panel_pending = list_pending_operational_approvals(session_id="sess-5b5edur1")
    tenant_pending = list_pending_operational_approvals(session_id=None)
    assert not any(row.job_id == job_id for row in panel_pending)
    assert any(row.job_id == job_id for row in tenant_pending)

    inbox = build_approval_inbox(session_id="operator")
    inbox_ids = {str(item.get("context", {}).get("job_id") or "") for item in inbox.items}
    assert job_id in inbox_ids


def test_deployment_approval_inbox_has_execution_flags(monkeypatch):
    """Deployment inbox items expose button state for planning-only vs executable."""
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
    from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
        create_railway_greenfield_preflight_job,
    )
    from aethos_core.runtime.jobs import job_store

    chat_session = "sess-deploy-flag-test"
    plan = {
        "repo": "pilotmain/killit",
        "branch": "main",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "killit",
        "risk_tier": "standard",
    }
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_preflight.authority.create_job",
        lambda **kwargs: job_store.create(
            title=kwargs.get("title") or "test",
            job_type=kwargs.get("job_type") or RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
            params=kwargs.get("params") or {},
            source=kwargs.get("source") or "chat",
            session_id=kwargs.get("session_id") or chat_session,
            auto_run=False,
        ),
    )
    preflight = create_railway_greenfield_preflight_job(
        user_text="deploy killit to railway",
        session_id=chat_session,
        plan=plan,
        env_report={"required_env_var_names": [], "count": 0},
        local_source={"ok": True, "workspace_name": "killit"},
        git_remote={"ok": True, "repository": "pilotmain/killit", "branch": "main"},
    )
    job_id = str(preflight.get("job_id") or "")
    inbox = build_approval_inbox(session_id="operator")
    item = next(i for i in inbox.items if str(i.get("context", {}).get("job_id") or "") == job_id)
    assert item.get("execution_mode") == "operational_deployment_approve"
    assert item.get("deployment_inbox_execution_enabled") is True
    assert item.get("deployment_execution_enabled") in {True, False}
    assert item.get("deployment_execution_hint")
    assert item.get("required_phrases") == [f"approve {job_id}"]


def test_greenfield_planning_only_reply_when_execution_disabled():
    """Execution off → planning-only message; turn completes without approval wait."""
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        assess_railway_execution_enablement_policy,
    )

    enablement = assess_railway_execution_enablement_policy(
        plan={"project": "pilotos", "environment": "staging", "service_name": "killit"},
        user_text="deploy killit to railway",
    )
    preflight = {
        "preflight_id": "rgf-test",
        "job_id": "job-test123",
        "approval_path": "Mission Control → Approvals",
        "steps": ["Create service"],
        "enablement": enablement,
    }
    reply = compose_greenfield_preflight_reply(
        preflight=preflight,
        local_report="**Local**",
        git_report="**Git**",
        target_report="**Target**",
        env_report_text="**Env**",
    )
    if not enablement.allows_real_mutation():
        assert "planning only" in reply.lower()
        assert "no deploy is waiting" in reply.lower() or "planning mode" in reply.lower()
    else:
        assert "Approval: **required**" in reply
