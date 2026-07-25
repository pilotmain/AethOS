# SPDX-License-Identifier: Apache-2.0
"""Session approval scope tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.approval.session_scopes import (
    clear_session_scopes_for_tests,
    compose_session_scope_reply,
    grant_mutation_session,
    grant_readonly_railway_session,
    has_readonly_railway_scope,
    has_session_mutation_scope,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_session_scopes_for_tests()
    yield
    clear_session_scopes_for_tests()


def test_approve_readonly_railway_session():
    reply = compose_session_scope_reply("Allow readonly Railway checks this session", session_id="scope-ro")
    assert reply is not None
    assert reply[1] == "session_approval_readonly"
    assert has_readonly_railway_scope(session_id="scope-ro") is True


def test_approve_same_operation_for_session():
    grant_mutation_session(
        session_id="scope-mut",
        operation="restart",
        target_phrase="atlas-trader / production / api",
    )
    assert has_session_mutation_scope(
        session_id="scope-mut",
        provider="railway",
        operation="restart",
        project="atlas-trader",
        environment="production",
        service="api",
    ) is True
    assert has_session_mutation_scope(
        session_id="scope-mut",
        provider="railway",
        operation="restart",
        project="influencer-crm",
        environment="production",
        service="worker",
    ) is False


def test_readonly_checks_do_not_grant_mutation():
    grant_readonly_railway_session(session_id="scope-split")
    assert has_readonly_railway_scope(session_id="scope-split") is True
    assert has_session_mutation_scope(
        session_id="scope-split",
        provider="railway",
        operation="restart",
        project="atlas-trader",
        environment="production",
        service="api",
    ) is False


def test_session_scope_chat_intent():
    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "Approve Railway restarts for atlas-trader api this session", "session_id": "scope-chat"},
    )
    body = response.json()
    assert body.get("intent") == "session_approval_mutation"
    assert "scoped session approval" in body["reply"].lower()
