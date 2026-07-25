# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production runtime verification hardening."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
    assess_railway_production_policy,
    record_production_confirmations_from_text,
)
from aethos_core.providers.railway.execution_contract.production_shadow_executor import (
    run_production_shadow_forward,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    clear_for_tests as clear_shadow_journal,
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    clear_for_tests as clear_shadow_receipts,
)
from aethos_core.providers.railway.execution_contract.production_verification_evidence import (
    collect_shadow_verification_evidence,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    clear_for_tests as clear_verification_receipts,
    load_verification_receipt,
)
from aethos_core.providers.railway.execution_contract.production_verification_rules import (
    assess_production_verification_evidence,
)
from aethos_core.providers.railway.execution_contract.production_verification_router import (
    is_railway_production_verification_intent,
    route_railway_production_verification,
)
from aethos_core.providers.railway.execution_contract.production_verification_service import (
    run_production_shadow_runtime_verification,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_shadow_receipts()
    clear_shadow_journal()
    clear_verification_receipts()
    get_settings.cache_clear()
    yield
    clear_shadow_receipts()
    clear_shadow_journal()
    clear_verification_receipts()
    get_settings.cache_clear()


def _prod_plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "production",
        "service_name": "api",
        "branch": "main",
        "health_check_path": "/api/v1/health",
    }


def _shadow_journal_complete() -> dict:
    return {
        "execution_id": "exec-pv-119",
        "forward_shadow_completed": True,
        "phases": [
            {"phase": "trigger_deploy_shadow", "status": "shadow_rehearsal_success"},
        ],
        "shadow_deploy_context": {
            "deployment_id": "dep-1",
            "deployment_state": "success",
        },
    }


def test_verification_intents():
    assert is_railway_production_verification_intent("show railway production verification evidence")


def test_weak_signal_only_fails():
    bundle = collect_shadow_verification_evidence(
        execution_id="exec-weak",
        plan=_prod_plan(),
        shadow_journal={"execution_id": "exec-weak", "forward_shadow_completed": False},
    )
    assessment = assess_production_verification_evidence(bundle)
    assert assessment.verification_passed is False
    assert "insufficient_strong_signals" in assessment.blockers


def test_multi_signal_passes_after_forward_shadow(monkeypatch):
    _enable(monkeypatch)
    execution_id = "exec-pv-pass"
    journal = _shadow_journal_complete()
    journal["execution_id"] = execution_id
    result = run_production_shadow_runtime_verification(
        execution_id=execution_id,
        plan=_prod_plan(),
        shadow_journal=journal,
    )
    assert result.verification_passed is True
    assert result.assessment.strong_signal_count >= 2
    assert len(result.assessment.families_present) >= 3
    receipt = load_verification_receipt(execution_id=execution_id)
    assert receipt is not None
    assert receipt.get("mutation_performed") is False
    assert receipt.get("schema_version") == "production_verification_v1"


def test_incident_mode_escalation(monkeypatch):
    monkeypatch.setenv("RAILWAY_PRODUCTION_INCIDENT_MODE", "true")
    get_settings.cache_clear()
    bundle = collect_shadow_verification_evidence(
        execution_id="exec-inc",
        plan=_prod_plan(),
        shadow_journal=_shadow_journal_complete(),
    )
    assessment = assess_production_verification_evidence(bundle, incident_mode_active=True)
    assert assessment.verification_passed is False
    assert assessment.incident_escalation == "incident_commander"
    assert assessment.rollback_recommendation == "advise_incident_escalation"


def test_full_shadow_forward_runs_verification_phase(monkeypatch):
    _enable(monkeypatch)
    execution_id = "exec-shadow-pv"
    phrase = f"{PRODUCTION_FINAL_PHRASE}\n{PRODUCTION_QUORUM_CONFIRMATION_PHRASE}"
    record_production_confirmations_from_text(execution_id=execution_id, user_text=phrase)
    forward = run_production_shadow_forward(
        execution_id=execution_id,
        plan=_prod_plan(),
        user_text=phrase,
    )
    assert forward.shadow_completed is True
    journal = load_shadow_journal(execution_id=execution_id)
    assert journal is not None
    assert journal.get("production_slo_verification_passed") is True
    policy = assess_railway_production_policy(
        plan=_prod_plan(),
        execution_id=execution_id,
        journal=journal,
    )
    assert policy.slo_verification_satisfied is True


def test_evidence_route():
    routed = route_railway_production_verification(
        "show railway production verification readiness",
        session_id="pv-route",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_production_verification_readiness"
    assert meta["route_id"] == "railway_production_verification"


def _enable(monkeypatch):
    monkeypatch.setenv("RAILWAY_PRODUCTION_SHADOW_EXECUTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    get_settings.cache_clear()
