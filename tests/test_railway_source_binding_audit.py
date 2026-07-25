# SPDX-License-Identifier: Apache-2.0
"""FIX 109B — source binding verification, audit, skipDeploys enforcement."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.execution_contract.source_binding_audit import (
    audit_connect_source_receipt,
    build_railway_source_binding_audit_report,
)
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    verify_source_binding_readonly,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
    commit_staged_changes_skip_deploy,
    validate_stage_input_source_only,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_plan()
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_plan()
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()


def _plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "aethos-api",
        "branch": "main",
    }


def test_validate_stage_input_rejects_env_writes():
    errors = validate_stage_input_source_only(
        {
            "services": {"svc-1": {"source": {"repo": "org/repo", "branch": "main"}}},
            "variables": {"SECRET": {"value": "x"}},
        }
    )
    assert errors
    assert any("variables" in err for err in errors)


def test_validate_stage_input_rejects_extra_service_keys():
    errors = validate_stage_input_source_only(
        {
            "services": {
                "svc-1": {
                    "source": {"repo": "org/repo", "branch": "main"},
                    "build": {"buildCommand": "npm run build"},
                }
            }
        }
    )
    assert errors
    assert any("source" in err for err in errors)


def test_commit_always_passes_skip_deploys_true():
    assert COMMIT_SKIP_DEPLOYS_ENFORCED is True
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.source_bind_graphql.graphql_query",
        return_value={"ok": True, "data": {}},
    ) as mock_gql:
        out = commit_staged_changes_skip_deploy("tok", environment_id="env-1")
    assert out["ok"] is True
    assert out.get("skip_deploys") is True
    variables = mock_gql.call_args[0][2]
    assert variables["skipDeploys"] is True


def test_readonly_verification_matches_plan():
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.source_bind_graphql.read_service_source_binding",
        return_value={
            "ok": True,
            "bound": True,
            "repository": "org/repo",
            "branch": "main",
        },
    ):
        result = verify_source_binding_readonly(
            token="tok",
            environment_id="env-1",
            service_id="svc-1",
            expected_repository="org/repo",
            expected_branch="main",
            journal_binding={"repository": "org/repo", "branch": "main"},
        )
    assert result.ok is True
    assert result.verified is True


def test_connect_source_receipt_audit_live_mutation():
    record_execution_receipt(
        execution_id="exec-audit",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="bound via environmentPatchCommitStaged (skipDeploys=true)",
    )
    audit = audit_connect_source_receipt(execution_id="exec-audit")
    assert audit.receipt_found is True
    assert audit.ok is True
    assert audit.is_live_mutation is True
    assert audit.detail_mentions_skip_deploys is True


def test_connect_source_receipt_audit_rejects_simulated():
    record_execution_receipt(
        execution_id="exec-sim",
        phase="connect_source",
        status="simulated_success",
        mutation_performed=False,
        detail="dry_run",
    )
    audit = audit_connect_source_receipt(execution_id="exec-sim")
    assert audit.is_simulated is True
    assert audit.ok is False


def test_source_binding_audit_report_skip_deploys_and_idempotent():
    journal = {
        "execution_id": "exec-1",
        "railway_service_id": "svc-1",
        "railway_environment_id": "env-1",
        "github_source_bound": {"repository": "org/repo", "branch": "main"},
    }
    report = build_railway_source_binding_audit_report(plan=_plan(), journal=journal, execution_id="exec-1")
    assert report.skip_deploys_enforced_in_code is True
    assert report.idempotent_replay_would_skip is True
    assert report.no_deploy_trigger_in_adapter is True


def test_show_source_binding_status_route():
    save_deployment_plan_context(session_id="s1", plan=_plan())
    routed = route_railway_execution_contract("show railway source binding status", session_id="s1")
    assert routed is not None
    body, route_id, meta = routed
    assert route_id == "railway_source_binding_status"
    assert "Source Binding Status" in body
    assert meta["mutation_performed"] == "false"
    assert meta["ready_for_env_writes"] == "false"


def test_show_source_binding_audit_route():
    save_deployment_plan_context(session_id="s1", plan=_plan())
    routed = route_railway_execution_contract("show railway source binding audit", session_id="s1")
    assert routed is not None
    body, route_id, _meta = routed
    assert route_id == "railway_source_binding_audit"
    assert "Source Binding Audit" in body
    assert "skip_deploys_enforced" in body
