# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    record_confirmation,
)
from aethos_core.providers.railway.execution_contract.production_incident_command import (
    INCIDENT_COMMANDER_ACCEPTANCE_PHRASE,
    close_production_incident,
    is_production_incident_command_intent,
    open_production_incident,
    record_incident_decision,
)
from aethos_core.providers.railway.execution_contract.production_incident_command_contract import (
    AUTONOMOUS_INCIDENT_MUTATION_PERMITTED,
    AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED,
)
from aethos_core.providers.railway.execution_contract.production_incident_command_store import (
    clear_for_tests,
    load_incident_for_execution,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    clear_for_tests as clear_shadow,
    get_or_create_shadow_journal,
    save_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    clear_for_tests as clear_verification,
    save_verification_receipt,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_for_tests()
    clear_shadow()
    clear_verification()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_shadow()
    clear_verification()
    get_settings.cache_clear()


def _seed(execution_id: str) -> None:
    record_confirmation(execution_id=execution_id, kind="production_final_phrase")
    record_confirmation(execution_id=execution_id, kind="production_quorum_confirmation")
    record_confirmation(execution_id=execution_id, kind="production_quorum_confirmation")
    sj, _ = get_or_create_shadow_journal(
        execution_id=execution_id,
        plan={"environment": "production", "project": "pilotos", "service": "aethos-api"},
    )
    sj["forward_shadow_completed"] = True
    save_shadow_journal(sj)
    save_verification_receipt(
        {
            "execution_id": execution_id,
            "status": "verification_failed",
            "assessment": {
                "verification_passed": False,
                "rollback_recommendation": "advise_manual_review",
            },
            "evidence": {},
        }
    )


def test_incident_intents():
    assert is_production_incident_command_intent("open railway production incident")
    assert is_production_incident_command_intent("show railway incident briefing")


def test_safety_constants():
    assert AUTONOMOUS_INCIDENT_MUTATION_PERMITTED is False
    assert AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED is False


def test_create_incident_and_briefing():
    execution_id = "exec-inc-123"
    _seed(execution_id)
    result = open_production_incident(
        execution_id=execution_id,
        plan={"environment": "production", "project": "pilotos", "service": "aethos-api"},
    )
    assert result.ok
    incident = result.incident
    assert incident["mutation_performed"] is False
    assert incident["incident_id"].startswith("rpic-")
    assert incident["rollback_recommendation"] == "advise_manual_review"

    loaded = load_incident_for_execution(execution_id=execution_id)
    assert loaded is not None
    assert len(loaded.get("events") or []) >= 1


def test_commander_phrase_required():
    execution_id = "exec-inc-cmd"
    _seed(execution_id)
    open_production_incident(execution_id=execution_id, plan={"environment": "production"})
    from aethos_core.providers.railway.execution_contract.production_incident_command import (
        assign_incident_commander,
    )

    bad = assign_incident_commander(execution_id=execution_id, user_text="assign commander")
    assert not bad.ok
    assert "incident_commander_phrase_required" in bad.blockers

    good = assign_incident_commander(
        execution_id=execution_id,
        user_text=f"assign\n{INCIDENT_COMMANDER_ACCEPTANCE_PHRASE}",
    )
    assert good.ok
    assert good.incident.get("commander") == "incident_commander"


def test_customer_draft_hides_secrets():
    execution_id = "exec-inc-draft"
    _seed(execution_id)
    open_production_incident(
        execution_id=execution_id,
        plan={"environment": "production", "project": "pilotos", "service": "aethos-api"},
    )
    from aethos_core.providers.railway.execution_contract.production_incident_command_renderer import (
        build_incident_context_bundle,
        render_customer_update_draft,
    )
    from aethos_core.providers.railway.execution_contract.production_incident_command_store import (
        load_incident_for_execution,
    )

    incident = load_incident_for_execution(execution_id=execution_id) or {}
    bundle = build_incident_context_bundle(execution_id=execution_id)
    draft = render_customer_update_draft(incident, bundle=bundle)
    assert "traceback (" not in draft.lower()
    assert "api_key" not in draft.lower()
    assert "no raw stack traces" in draft.lower()
    assert "investigating" in draft.lower()


def test_incident_mode_blocks_rollout_advance(monkeypatch):
    execution_id = "exec-inc-rollout"
    _seed(execution_id)
    monkeypatch.setenv("RAILWAY_PRODUCTION_INCIDENT_MODE", "true")
    monkeypatch.setenv("RAILWAY_PRODUCTION_SHADOW_EXECUTION", "true")
    get_settings.cache_clear()
    open_production_incident(execution_id=execution_id, plan={"environment": "production"})
    from aethos_core.providers.railway.execution_contract.production_rollout_gate import (
        assess_rollout_stage_gate,
    )
    from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
        get_or_create_rollout_journal,
    )

    get_or_create_rollout_journal(execution_id=execution_id, plan={"environment": "production"})
    gate = assess_rollout_stage_gate(
        execution_id=execution_id,
        stage="shadow",
        plan={"environment": "production"},
        require_advance_phrase=False,
    )
    assert not gate.ready_to_advance
    assert any("incident" in b for b in gate.blockers)


def test_timeline_audit_events():
    execution_id = "exec-inc-audit"
    _seed(execution_id)
    open_production_incident(execution_id=execution_id, plan={"environment": "production"})
    record_incident_decision(
        execution_id=execution_id,
        decision="begin_triage",
    )
    incident = load_incident_for_execution(execution_id=execution_id)
    assert incident is not None
    events = incident.get("events") or []
    assert any(e.get("mutation_performed") is False for e in events)
    close_production_incident(execution_id=execution_id)
    closed = load_incident_for_execution(execution_id=execution_id)
    assert closed is None or str(closed.get("status")) == "closed"
