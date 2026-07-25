# SPDX-License-Identifier: Apache-2.0
"""UI greenfield configure_env groups must target NEXT_PUBLIC_API_BASE, not API secrets."""

from __future__ import annotations

from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    ENV_CONFIGURE_GROUP_UI_RUNTIME,
    resolve_env_configure_groups,
)
from aethos_core.providers.railway.execution_contract.env_configure_verification import (
    verify_env_configure_readonly,
)


def test_ui_plan_uses_ui_runtime_env_group() -> None:
    plan = {
        "deploy_component": "ui",
        "service_name": "aethos-ui",
        "environment": "staging",
        "project": "pilotos",
        "repo": "pilotmain/AethOS",
    }
    groups = resolve_env_configure_groups(plan)
    assert len(groups) == 1
    assert groups[0][0] == ENV_CONFIGURE_GROUP_UI_RUNTIME
    assert groups[0][1] == ("NEXT_PUBLIC_API_BASE",)


def test_deploy_readiness_checks_ui_group_not_api_secrets(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_TRIGGER_DEPLOY_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_REQUIRE_FINAL_PHRASE", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    plan = {
        "deploy_component": "ui",
        "service_name": "aethos-ui",
        "environment": "staging",
        "project": "pilotos",
        "repo": "pilotmain/AethOS",
    }
    journal = {
        "execution_id": "exec-ui-test",
        "railway_service_id": "svc-ui",
        "railway_environment_id": "env-staging",
        "rollback_journal": {"phases": []},
        "env_configure_verification": {
            "ok": True,
            "verified": True,
            "names_observed": ["NEXT_PUBLIC_API_BASE"],
            "minimum_secret_names_required": ["NEXT_PUBLIC_API_BASE"],
            "minimum_secrets_present": True,
        },
    }

    from aethos_core.providers.railway.execution_contract import execution_receipt_status
    from aethos_core.providers.railway.execution_contract.execution_real_mutation_support import (
        record_real_phase_receipt,
    )

    for phase in ("create_service", "connect_source"):
        record_real_phase_receipt(
            execution_id="exec-ui-test",
            phase=phase,
            status=execution_receipt_status.STATUS_MUTATION_SUCCESS,
            mutation_performed=True,
            detail="test",
        )
    record_real_phase_receipt(
        execution_id="exec-ui-test",
        phase="configure_env",
        status=execution_receipt_status.STATUS_MUTATION_SUCCESS,
        mutation_performed=True,
        detail="ui env configured",
        receipt_group=ENV_CONFIGURE_GROUP_UI_RUNTIME,
        env_var_names=["NEXT_PUBLIC_API_BASE"],
    )

    readiness = assess_deploy_trigger_readiness(plan=plan, journal=journal, execution_id="exec-ui-test")
    assert "configure_env_live_required" not in readiness.blockers


def test_find_phase_group_receipt_returns_latest_receipt() -> None:
    from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
        STATUS_MUTATION_FAILURE,
        STATUS_MUTATION_SUCCESS,
        forward_live_configure_env_group_recorded,
    )
    from aethos_core.providers.railway.execution_contract.execution_receipts import (
        clear_for_tests,
        find_phase_group_receipt,
        record_execution_receipt,
    )

    clear_for_tests()
    execution_id = "rexec-receipt-order-test"
    record_execution_receipt(
        execution_id=execution_id,
        phase="configure_env",
        status=STATUS_MUTATION_FAILURE,
        mutation_performed=False,
        receipt_group="ui_runtime_vars",
        env_var_names=["NEXT_PUBLIC_API_BASE"],
    )
    record_execution_receipt(
        execution_id=execution_id,
        phase="configure_env",
        status=STATUS_MUTATION_SUCCESS,
        mutation_performed=True,
        receipt_group="ui_runtime_vars",
        env_var_names=["NEXT_PUBLIC_API_BASE"],
    )
    receipt = find_phase_group_receipt(
        execution_id=execution_id,
        phase="configure_env",
        receipt_group="ui_runtime_vars",
    )
    assert receipt is not None
    assert receipt.get("status") == STATUS_MUTATION_SUCCESS
    assert forward_live_configure_env_group_recorded(receipt) is True


def test_verify_env_readonly_uses_plan_required_names(monkeypatch) -> None:
    def fake_read(token, *, environment_id, service_id):
        _ = token, environment_id, service_id
        return {"ok": True, "names": ["NEXT_PUBLIC_API_BASE"]}

    monkeypatch.setattr(
        "aethos_core.providers.railway.execution_contract.env_configure_verification.read_service_env_var_names",
        fake_read,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.execution_contract.env_configure_verification.resolve_railway_mutation_credentials",
        lambda: ("tok", "test", None),
    )
    plan = {"deploy_component": "ui", "service_name": "aethos-ui", "environment": "staging"}
    result = verify_env_configure_readonly(
        environment_id="env-1",
        service_id="svc-1",
        plan=plan,
    )
    assert result.verified is True
    assert result.minimum_secret_names_required == ("NEXT_PUBLIC_API_BASE",)
