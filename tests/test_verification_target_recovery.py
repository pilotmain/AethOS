# SPDX-License-Identifier: Apache-2.0
"""Verification target recovery tests."""

from __future__ import annotations

import pytest

from aethos_core.operation_lifecycle.lifecycle_resolver import _service_phrase_from_text
from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
from aethos_core.operations.mutations.lifecycle_authority import EXECUTION_COMPLETED_STATE
from aethos_core.post_mutation_verification.verification_intent_router import (
    extract_explicit_path_target,
    is_intent_word,
    reset_pending_verification_for_tests,
    resolve_verification_target,
    route_post_mutation_verification,
    store_pending_verification_request,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()
    yield
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()


def _seed_execution_job(*, session_id: str = "default") -> None:
    pf = authority.create_job(
        title="Restart MongoDB",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "target": {
                "service_name": "MongoDB",
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
            },
            "preflight_match_key": "railway:restart:mongodb",
            "mutation_execution_approved": True,
            "is_current": True,
        },
        session_id=session_id,
        auto_run=False,
    )
    exec_job = authority.create_job(
        title="Restart MongoDB execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "MongoDB",
            "executed": True,
            "execution_state": "execution_completed",
            "verification_state": "verification_running",
            "canonical_lifecycle_state": EXECUTION_COMPLETED_STATE,
            "preflight_match_key": "railway:restart:mongodb",
            "provider_evidence_bundle": {"log_summary": "application startup complete"},
        },
        session_id=session_id,
        auto_run=False,
    )
    pf_job = job_store.get(pf.id)
    if pf_job:
        pf_job.params["mutation_execution_job_id"] = exec_job.id
    job_store.complete_with_result(
        exec_job.id,
        full_result="done",
        summary="done",
        preview="done",
        provider="mutation_execution",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )


@pytest.mark.parametrize(
    "word",
    ["changed", "restart", "health", "logs", "started", "application", "recover", "hold", "status"],
)
def test_intent_words_are_not_service_names(word: str) -> None:
    assert is_intent_word(word)
    phrase = _service_phrase_from_text(f"verify {word}")
    assert phrase is None or phrase.lower() != word.lower()


def test_recent_lifecycle_target_wins_when_no_target_specified() -> None:
    _seed_execution_job()
    target = resolve_verification_target("verify health", session_id="default")
    assert target is not None
    assert target.service == "MongoDB"
    assert "pilotcore-sales-engine" in target.target_path


def test_explicit_path_target_continues_pending_verification() -> None:
    _seed_execution_job()
    store_pending_verification_request(
        session_id="default",
        intent="startup_log_check",
        original_text="can you check top 5 logs to see if application started?",
    )
    reply = route_post_mutation_verification(
        "pilotcore-sales-engine/production/MongoDB",
        session_id="default",
    )
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "post_mutation_startup_log_check"
    assert "MongoDB" in body
    assert "Startup marker:" in body


def test_extract_explicit_path_target() -> None:
    target = extract_explicit_path_target("pilotcore-sales-engine/production/MongoDB")
    assert target is not None
    assert target.service == "MongoDB"
    assert target.project == "pilotcore-sales-engine"
