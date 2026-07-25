# SPDX-License-Identifier: Apache-2.0
"""Arbiter async start: POST /arbiter/sessions/start returns a session id immediately
and seeds a pollable session, so a long multi-round debate doesn't 502 a synchronous
request at the gateway (the run finishes server-side and the UI polls for it)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aethos_core.api.routes import arbiter as arb
from aethos_core.arbiter.session_store import get_session


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(arb.router, prefix="/api/v1")
    return TestClient(app)


async def _noop_run(*_args, **_kwargs):  # stands in for the real (LLM) run
    return None


def test_start_returns_id_immediately_and_seeds_pollable_session():
    with patch.object(arb, "effective_bool", lambda *_: True), patch.object(
        arb, "parse_model_pool", lambda: [{"provider": "openrouter", "model": "x"}, {"provider": "openrouter", "model": "y"}]
    ), patch.object(arb, "validate_pool", lambda _pool: {"valid": True, "errors": []}), patch.object(
        arb, "run_arbiter_session", _noop_run
    ):
        client = _client()
        r = client.post("/api/v1/arbiter/sessions/start", json={"prompt": "compare X vs Y", "debate_rounds": 2})
        assert r.status_code == 200, r.text
        body = r.json()
        sid = body["arbiter_session_id"]
        assert sid.startswith("arb-")
        assert body["status"] == "running"
        # Seeded synchronously before the worker thread runs → immediately pollable.
        assert get_session(sid) is not None


def test_start_rejects_when_disabled():
    with patch.object(arb, "effective_bool", lambda *_: False):
        client = _client()
        r = client.post("/api/v1/arbiter/sessions/start", json={"prompt": "x"})
        assert r.status_code == 503


def test_start_rejects_empty_prompt():
    with patch.object(arb, "effective_bool", lambda *_: True), patch.object(
        arb, "parse_model_pool", lambda: [{"provider": "openrouter", "model": "x"}]
    ), patch.object(arb, "validate_pool", lambda _pool: {"valid": True, "errors": []}):
        client = _client()
        r = client.post("/api/v1/arbiter/sessions/start", json={"prompt": "   "})
        assert r.status_code == 422
