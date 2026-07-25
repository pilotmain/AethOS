# SPDX-License-Identifier: Apache-2.0
"""FIX 112B — env configure verification, audit guards, deploy trigger readiness."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.env_configure_audit import (
    build_railway_env_configure_audit_report,
)
from aethos_core.providers.railway.execution_contract.env_configure_verification import (
    verify_env_configure_readonly,
)
from aethos_core.providers.railway.execution_contract.env_configure_status import (
    assess_railway_env_configure_status,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    SourceBindingVerification,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()


def _plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "api",
        "branch": "main",
    }


def _journal_configured() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-112b",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
            "env_configure_rollback_plan": {"rollback_plan_ready": True},
            "env_configure_groups": {
                "minimum_secrets": {
                    "recorded": True,
                    "env_names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
                    "version_fingerprint": "fp1",
                    "mutation_performed": True,
                }
            },
            "env_vars_configured": {
                "groups": {
                    "minimum_secrets": {
                        "env_names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
                    }
                }
            },
        }
    )
    record_execution_receipt(
        execution_id="exec-112b",
        phase="create_service",
        status="mutation_success",
        mutation_performed=True,
        detail="created",
    )
    record_execution_receipt(
        execution_id="exec-112b",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="skipDeploys=true",
    )
    record_execution_receipt(
        execution_id="exec-112b",
        phase="configure_env",
        status="mutation_success",
        mutation_performed=True,
        detail="group minimum_secrets configured",
        receipt_group="minimum_secrets",
        env_var_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )
    return journal


@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.read_service_env_var_names",
    return_value={
        "ok": True,
        "names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
        "detail": "names only",
    },
)
@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.resolve_railway_mutation_credentials",
    return_value=("token", "env", ""),
)
def test_verify_env_names_only(_mock_cred, _mock_read):
    result = verify_env_configure_readonly(
        environment_id="env-staging",
        service_id="svc-1",
    )
    assert result.ok is True
    assert result.verified is True
    assert result.minimum_secrets_present is True
    assert "ANTHROPIC_API_KEY" in result.names_observed
    assert result.detail
    assert "value" not in result.to_dict().keys()


@patch(
    "aethos_core.providers.railway.execution_contract.source_binding_status.verify_source_binding_readonly",
    return_value=SourceBindingVerification(
        ok=True,
        verified=True,
        repository_observed="org/repo",
        branch_observed="main",
        detail="ok",
    ),
)
@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.read_service_env_var_names",
    return_value={
        "ok": True,
        "names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
        "detail": "names only",
    },
)
@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.resolve_railway_mutation_credentials",
    return_value=("token", "env", ""),
)
def test_deploy_trigger_not_ready_until_flag(_mock_cred, _mock_read, _mock_bind):
    journal = _journal_configured()
    readiness = assess_deploy_trigger_readiness(
        journal=journal,
        plan=_plan(),
        execution_id="exec-112b",
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert readiness.create_service_live_success is True
    assert readiness.connect_source_live_success is True
    assert readiness.configure_env_live_success is True
    assert readiness.env_names_verified is True
    assert readiness.deploy_trigger_enabled is False
    assert readiness.ready_for_deploy_trigger is False
    assert "deploy_trigger_disabled" in readiness.blockers


@patch(
    "aethos_core.providers.railway.execution_contract.source_binding_status.verify_source_binding_readonly",
    return_value=SourceBindingVerification(ok=True, verified=True, detail="ok"),
)
@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.read_service_env_var_names",
    return_value={"ok": True, "names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"], "detail": "ok"},
)
@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.resolve_railway_mutation_credentials",
    return_value=("token", "env", ""),
)
def test_status_shows_ready_for_deploy_trigger_false(_mock_cred, _mock_read, _mock_bind):
    status = assess_railway_env_configure_status(
        journal=_journal_configured(),
        plan=_plan(),
        execution_id="exec-112b",
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert status.env_names_verified is True
    assert status.ready_for_deploy_trigger is False
    assert status.rollback_contract_visible is True


def test_audit_blocks_chat_secrets_in_user_text():
    report = build_railway_env_configure_audit_report(
        journal=_journal_configured(),
        plan=_plan(),
        execution_id="exec-112b",
        user_text="set env variable ANTHROPIC_API_KEY=sk-leak",
    )
    assert report.ok is False
    assert "chat_secrets_in_user_text" in report.blockers


@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.read_service_env_var_names",
    return_value={"ok": True, "names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"], "detail": "ok"},
)
@patch(
    "aethos_core.providers.railway.execution_contract.env_configure_verification.resolve_railway_mutation_credentials",
    return_value=("token", "env", ""),
)
def test_audit_idempotent_proof(_mock_cred, _mock_read):
    report = build_railway_env_configure_audit_report(
        journal=_journal_configured(),
        plan=_plan(),
        execution_id="exec-112b",
    )
    assert report.idempotent_proofs
    assert report.idempotent_proofs[0].would_skip_on_replay is True
    assert report.rollback_contract_visible is True


def test_verification_route():
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        clear_for_tests as clear_plan,
        save_deployment_plan_context,
    )
    from aethos_core.providers.railway.execution_contract.execution_context import (
        bind_session_execution,
    )
    from aethos_core.providers.railway.execution_contract.execution_journal import (
        save_execution_journal,
    )

    clear_plan()
    save_deployment_plan_context(session_id="s-112b", plan=_plan())
    journal = _journal_configured()
    save_execution_journal(journal)
    bind_session_execution(session_id="s-112b", execution_id="exec-112b")

    with patch(
        "aethos_core.providers.railway.execution_contract.env_configure_verification.read_service_env_var_names",
        return_value={"ok": True, "names": ["ANTHROPIC_API_KEY"], "detail": "ok"},
    ), patch(
        "aethos_core.providers.railway.execution_contract.env_configure_verification.resolve_railway_mutation_credentials",
        return_value=("token", "env", ""),
    ):
        route = route_railway_execution_contract(
            "show railway env configure verification",
            session_id="s-112b",
        )
    assert route is not None
    assert "names_observed" in route[0] or "Read-Only" in route[0]
    assert "sk-" not in route[0]
