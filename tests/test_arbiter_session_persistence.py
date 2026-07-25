# SPDX-License-Identifier: Apache-2.0
"""Arbiter sessions persist across restarts/deploys so the Mission Control → Arbiter panel
keeps its per-model breakdown. In-memory is just a cache; terminal sessions go to the durable
tenant store. Non-terminal (e.g. 'dispatching') sessions are NOT persisted — an interrupted run
must not leave a stale row.
"""

from __future__ import annotations

import pytest

from aethos_core.arbiter.models import ArbiterSession, ArbiterStatus, ConsensusResult, ModelResponse


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("TENANT_DATA_DIR", str(tmp_path / "td"))
    from aethos_core.tenancy import tenant_data_store as tds

    tds.reset_for_tests()
    from aethos_core.arbiter import session_store as ss

    ss._sessions.clear()
    yield ss
    ss._sessions.clear()
    tds.reset_for_tests()


def _completed_session(sid="arb-keep"):
    return ArbiterSession(
        session_id=sid,
        tenant_id="default",
        prompt="is localStorage safe for JWTs?",
        status=ArbiterStatus.NO_CONSENSUS,
        model_pool=[{"provider": "anthropic", "model_id": "claude", "label": "Claude"}],
        responses=[
            ModelResponse(response_id="r1", provider="anthropic", model_id="claude", model_label="Claude", text="No."),
            ModelResponse(response_id="r2", provider="openrouter", model_id="openai/gpt-4o-mini", model_label="GPT", text="Use cookies."),
        ],
        consensus=ConsensusResult(
            winning_response_id="r1", winning_model_id="claude", winning_model_label="Claude",
            winning_text="No.", agreement_score=0.5, consensus_reached=False, consensus_threshold=0.6,
            total_models=2, responding_models=2, agreeing_models=1, dissenting_model_ids=["openai/gpt-4o-mini"],
            round_count=1, summary="Split decision.",
        ),
        rounds_completed=1,
    )


def test_completed_session_survives_restart(store):
    store.put_session(_completed_session("arb-keep"))
    store._sessions.clear()  # simulate restart/deploy: in-memory gone

    got = store.get_session("arb-keep")
    assert got is not None, "completed session must be retrievable after restart"
    assert got.status == ArbiterStatus.NO_CONSENSUS
    assert len(got.responses) == 2  # full per-model detail preserved
    assert got.consensus is not None and got.consensus.winning_model_label == "Claude"
    assert any(d["session_id"] == "arb-keep" for d in store.list_sessions())


def test_nonterminal_session_not_persisted(store):
    store.put_session(ArbiterSession(session_id="arb-stuck", tenant_id="default", status=ArbiterStatus.DISPATCHING))
    store._sessions.clear()  # restart mid-run
    assert store.get_session("arb-stuck") is None  # no stale 'dispatching' row survives
