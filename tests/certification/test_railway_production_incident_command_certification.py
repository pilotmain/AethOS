# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_incident_command_contract import (
    INCIDENT_COMMANDER_ACCEPTANCE_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_incident_command_store import (
    clear_for_tests as clear_incidents,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_railway_production_verification_certification import (
    SESSION,
    TestProductionVerificationCertification,
    _bootstrap_production_plan,
)

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_incidents()
    get_settings.cache_clear()
    yield
    clear_incidents()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestProductionIncidentCommandCertification:
    def test_incident_command_workflow(self, monkeypatch) -> None:
        _bootstrap_production_plan(monkeypatch, SESSION)
        TestProductionVerificationCertification().test_verification_evidence_after_shadow_forward(
            monkeypatch
        )

        opened = resolve_chat_turn(
            "open railway production incident",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(opened, route_id="railway_production_incident_command")
        assert opened.intent == "railway_production_incident_opened"
        assert opened.meta.get("mutation_performed") in {None, "false"}

        briefing = resolve_chat_turn(
            "show railway incident briefing",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(briefing, route_id="railway_production_incident_command")
        assert "Incident Briefing" in briefing.reply
        assert "No production mutation has been performed" in briefing.reply

        commander = resolve_chat_turn(
            f"assign railway incident commander\n{INCIDENT_COMMANDER_ACCEPTANCE_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(commander, route_id="railway_production_incident_command")

        decision = resolve_chat_turn(
            "record railway incident decision begin_triage",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(decision, route_id="railway_production_incident_command")

        draft = resolve_chat_turn(
            "show railway incident customer update draft",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(draft, route_id="railway_production_incident_command")
        assert "traceback (" not in draft.reply.lower()
        assert "no raw stack traces" in draft.reply.lower()

        timeline = resolve_chat_turn(
            "show railway production incident timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(timeline, route_id="railway_production_incident_command")
        assert "mutation_performed" in timeline.reply

        rollback = resolve_chat_turn(
            "show railway incident rollback recommendation",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(rollback, route_id="railway_production_incident_command")
