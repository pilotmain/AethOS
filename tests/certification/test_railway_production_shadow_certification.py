# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow certification (fixtures only, no live mutations)."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    bind_session_execution,
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    get_or_create_execution_journal,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_contract import (
    INCIDENT_COMMANDER_ACK_PHRASE,
    PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_shadow_contract_models import (
    FORWARD_SHADOW_PHASES,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    clear_for_tests as clear_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    clear_for_tests as clear_shadow_receipts,
    list_shadow_receipts,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_aethos_stability_contract_v1 import _railway_dry_run_lifecycle_mocks

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _shadow_cert_clean():
    reset_certification_runtime()
    clear_journal()
    clear_shadow_receipts()
    clear_shadow_journal()
    clear_execution_context()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_shadow_receipts()
    clear_shadow_journal()
    clear_execution_context()
    get_settings.cache_clear()
    reset_certification_runtime()


@contextmanager
def _production_plan_mocks(monkeypatch):
    monkeypatch.setenv("RAILWAY_PRODUCTION_SHADOW_EXECUTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    monkeypatch.setenv(
        "RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS",
        "staging,development,production",
    )
    get_settings.cache_clear()
    inspect_payload = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "branch": "main",
        "fields": {
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV"],
            "service_name_confidence": "medium",
        },
    }
    with (
        _railway_dry_run_lifecycle_mocks(monkeypatch),
        patch(
            "aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options",
            return_value=[],
        ),
        patch(
            "aethos_core.providers.railway.deployment_plan.plan_completion.inspect_github_repo_for_deployment",
            return_value=inspect_payload,
        ),
    ):
        yield


class TestProductionShadowCertification:
    def test_production_shadow_rehearsal_chain(self, monkeypatch) -> None:
        session = "prod-shadow-cert-v1"
        with _production_plan_mocks(monkeypatch):
            resolve_chat_turn(
                "run railway deployment readiness for pilotmain/aethos",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "create railway deployment plan for pilotmain/aethos in pilotos / production",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "complete the railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "confirm railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "create railway service creation preflight",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "approve railway service creation preflight",
                session_id=session,
                apply_relational_layer=False,
            )
            sim = resolve_chat_turn(
                "simulate railway service creation",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(sim, route_id="railway_service_creation_simulator")

            from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
                get_deployment_plan_context,
            )

            plan_ctx = get_deployment_plan_context(session_id=session) or {}
            journal, _ = get_or_create_execution_journal(
                plan=plan_ctx,
                session_id=session,
                initial_state="simulation_complete",
                approval={},
            )
            execution_id = str(journal["execution_id"])
            bind_session_execution(session_id=session, execution_id=execution_id)

            cert = resolve_chat_turn(
                "show railway production certification",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(cert, route_id="railway_production_shadow")
            assert cert.meta.get("production_shadow_stage") == "certification"

            phrase = (
                f"{PRODUCTION_FINAL_PHRASE}\n{PRODUCTION_QUORUM_CONFIRMATION_PHRASE}"
            )
            forward = resolve_chat_turn(
                f"simulate production railway deployment\n{phrase}",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(forward, route_id="railway_production_shadow")
            assert forward.meta.get("mutation_performed") in {None, "false"}
            assert forward.intent == "railway_production_shadow_forward"

            receipts = list_shadow_receipts(execution_id=execution_id)
            assert len(receipts) >= len(FORWARD_SHADOW_PHASES)
            assert all(r.get("mutation_performed") is False for r in receipts)

            resolve_chat_turn(
                f"acknowledge production rollback escalation\n{INCIDENT_COMMANDER_ACK_PHRASE}",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                f"show railway production rollback rehearsal quorum\n{PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE}",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "record production rollback decision shadow_rehearsal_authorized",
                session_id=session,
                apply_relational_layer=False,
            )

            rollback = resolve_chat_turn(
                f"simulate production railway rollback\n{PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE}",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(rollback, route_id="railway_production_shadow")
            assert rollback.intent == "railway_production_shadow_rollback"

            timeline_receipts = list_shadow_receipts(execution_id=execution_id)
            assert all(r.get("mutation_performed") is False for r in timeline_receipts)
