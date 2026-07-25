# SPDX-License-Identifier: Apache-2.0
"""§6 — provider resilience: transient retry, live models, arbiter partial failure."""

from __future__ import annotations

import httpx
import pytest

from aethos_core.arbiter.consensus_engine import compute_consensus
from aethos_core.arbiter.models import CritiqueScore, ModelResponse
from aethos_core.config import get_settings
from aethos_core.llm.model_providers import clear_live_model_cache_for_tests, live_model_rows
from aethos_core.provider import completion as completion_mod


@pytest.fixture(autouse=True)
def _clean_settings(monkeypatch):
    get_settings.cache_clear()
    clear_live_model_cache_for_tests()
    yield
    get_settings.cache_clear()
    clear_live_model_cache_for_tests()


def test_transient_retry_recovers_on_second_attempt(monkeypatch):
    """Simulated one-shot timeout retries and succeeds on the same provider call."""
    monkeypatch.setenv("PROVIDER_LLM_TRANSIENT_RETRIES", "1")
    get_settings.cache_clear()
    attempts = 0

    class _FakeClient:
        def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise httpx.TimeoutException("simulated blip")
            req = httpx.Request(method, url)
            return httpx.Response(200, json={"ok": True}, request=req)

    monkeypatch.setattr(completion_mod, "_get_provider_http_client", lambda: _FakeClient())
    resp = completion_mod._http_request_with_transient_retry("GET", "https://api.anthropic.com/v1/models")
    assert resp.status_code == 200
    assert attempts == 2


def _ok_response(method: str, url: str) -> httpx.Response:
    return httpx.Response(200, json={"ok": True}, request=httpx.Request(method, url))


def test_connection_error_recovers_with_default_retries(monkeypatch):
    """A valid key hitting a stale-socket / connection blip recovers on its own.

    Reproduces the reported 'Anthropic temporarily unavailable (timeout or connection
    error)' on a working key — now the request is retried on a fresh socket and succeeds.
    """
    monkeypatch.setattr(completion_mod.time, "sleep", lambda *_a, **_k: None)
    get_settings.cache_clear()
    attempts = 0

    class _FakeClient:
        def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts <= 3:  # three connection blips in a row
                raise httpx.ConnectError("connection reset by peer")
            return _ok_response(method, url)

    monkeypatch.setattr(completion_mod, "_get_provider_http_client", lambda: _FakeClient())
    resp = completion_mod._http_request_with_transient_retry("POST", "https://api.anthropic.com/v1/messages")
    assert resp.status_code == 200
    assert attempts == 4  # recovered without surfacing a failure


def test_connection_errors_get_extra_attempts_beyond_base(monkeypatch):
    """Connection errors get extra retries on top of the standard transient budget."""
    monkeypatch.setenv("PROVIDER_LLM_TRANSIENT_RETRIES", "1")  # base = 2 attempts
    monkeypatch.setenv("PROVIDER_LLM_CONNECTION_ERROR_EXTRA_RETRIES", "2")  # +2 => 4 attempts
    monkeypatch.setattr(completion_mod.time, "sleep", lambda *_a, **_k: None)
    get_settings.cache_clear()
    attempts = 0

    class _FakeClient:
        def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts <= 3:
                raise httpx.RemoteProtocolError("server disconnected without sending a response")
            return _ok_response(method, url)

    monkeypatch.setattr(completion_mod, "_get_provider_http_client", lambda: _FakeClient())
    resp = completion_mod._http_request_with_transient_retry("POST", "https://openrouter.ai/api/v1/chat/completions")
    assert resp.status_code == 200
    assert attempts == 4


def test_auth_failure_is_not_retried(monkeypatch):
    """A real auth error (401) must fail fast — no retry storm on a genuine bad key."""
    monkeypatch.setattr(completion_mod.time, "sleep", lambda *_a, **_k: None)
    get_settings.cache_clear()
    attempts = 0

    class _FakeClient:
        def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            req = httpx.Request(method, url)
            resp = httpx.Response(401, json={"error": "invalid api key"}, request=req)
            raise httpx.HTTPStatusError("401", request=req, response=resp)

    monkeypatch.setattr(completion_mod, "_get_provider_http_client", lambda: _FakeClient())
    with pytest.raises(httpx.HTTPStatusError):
        completion_mod._http_request_with_transient_retry("POST", "https://api.anthropic.com/v1/messages")
    assert attempts == 1


def test_rate_limit_429_is_retried(monkeypatch):
    """A 429 is retried within the same provider before cross-provider failover."""
    monkeypatch.setenv("PROVIDER_LLM_TRANSIENT_RETRIES", "3")
    monkeypatch.setattr(completion_mod.time, "sleep", lambda *_a, **_k: None)
    get_settings.cache_clear()
    attempts = 0

    class _FakeClient:
        def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            req = httpx.Request(method, url)
            if attempts < 3:
                resp = httpx.Response(429, json={"error": "rate limited"}, request=req)
                raise httpx.HTTPStatusError("429", request=req, response=resp)
            return _ok_response(method, url)

    monkeypatch.setattr(completion_mod, "_get_provider_http_client", lambda: _FakeClient())
    resp = completion_mod._http_request_with_transient_retry("POST", "https://api.anthropic.com/v1/messages")
    assert resp.status_code == 200
    assert attempts == 3


def test_timeout_config_short_connect_full_read(monkeypatch):
    """Connect/pool fail fast (clean retry); read keeps the full generation budget."""
    monkeypatch.setenv("PROVIDER_LLM_TIMEOUT_SEC", "45")
    monkeypatch.setenv("PROVIDER_LLM_CONNECT_TIMEOUT_SEC", "10")
    get_settings.cache_clear()
    cfg = completion_mod._provider_timeout_config()
    assert cfg.connect == 10.0
    assert cfg.read == 45.0
    assert cfg.write == 45.0
    assert cfg.pool == 10.0


def test_is_connection_error_classification():
    assert completion_mod._is_connection_error(httpx.ConnectError("x")) is True
    assert completion_mod._is_connection_error(httpx.ConnectTimeout("x")) is True
    assert completion_mod._is_connection_error(httpx.PoolTimeout("x")) is True
    assert completion_mod._is_connection_error(httpx.RemoteProtocolError("x")) is True
    # A plain read timeout means the server got the request — not a "connection" error.
    assert completion_mod._is_connection_error(httpx.ReadTimeout("x")) is False
    # An HTTP status error carries a response — never a connection error.
    req = httpx.Request("POST", "https://example.com")
    status_exc = httpx.HTTPStatusError("500", request=req, response=httpx.Response(500, request=req))
    assert completion_mod._is_connection_error(status_exc) is False


def test_transient_message_says_key_is_fine():
    """The surfaced transient message must not blame the user's API key."""
    msg = completion_mod.format_provider_http_error(
        httpx.ConnectError("blip"),
        provider_label="Anthropic",
        model="claude-opus-4-8",
        provider="anthropic",
    )
    assert "key is fine" in msg.lower()
    assert "transient" in msg.lower()


def test_grounded_chat_reply_accepts_channel():
    """Regression: the no-provider fallback passes channel= — the passthrough must accept it."""
    from aethos_core.conversation.polish_compat import try_grounded_chat_reply

    # Must not raise TypeError regardless of return value.
    result = try_grounded_chat_reply("hello", session_id="diag", channel="chat")
    assert result is None or isinstance(result, tuple)


def test_transient_message_does_not_push_second_provider(monkeypatch):
    """Normal single-model chat: a transient blip must not nag about a second provider."""
    msg = completion_mod.format_provider_http_error(
        httpx.ConnectError("blip"),
        provider_label="Anthropic",
        model="claude-opus-4-8",
        provider="anthropic",
    )
    assert "second provider" not in msg.lower()
    assert "failover" not in msg.lower()
    assert "key is fine" in msg.lower()


def test_single_provider_failure_text_no_second_provider_push():
    text = completion_mod._all_providers_failed_text(
        [("Anthropic · Opus", "no key configured")],
        providers_tried={"anthropic"},
    )
    assert "add a second provider" not in text.lower()
    assert "no key configured" in text.lower()


def test_anthropic_tool_loop_not_routed_through_registry(monkeypatch):
    """Regression: Anthropic is also a connections-catalog provider, but must use the native
    messages API in the tool loop — never the OpenAI-compatible registry path (which would
    POST to a relative '/chat/completions' and raise UnsupportedProtocol)."""
    monkeypatch.setattr("aethos_core.llm.model_providers.is_registry_provider", lambda p: True)
    called = {"native": False, "registry": False}

    def _native(**kwargs):
        called["native"] = True
        return completion_mod.ToolLoopResult(text="ok", provider="anthropic", model="m", used_llm=True)

    def _registry(**kwargs):
        called["registry"] = True
        return completion_mod.ToolLoopResult(text="WRONG", provider="anthropic", model="m", used_llm=True)

    monkeypatch.setattr(completion_mod, "run_anthropic_tool_loop", _native)
    monkeypatch.setattr(completion_mod, "run_registry_provider_tool_loop", _registry)
    for provider in ("anthropic", "claude"):
        called["native"] = called["registry"] = False
        completion_mod._run_tool_loop_one_attempt(
            provider, "claude-opus-4-8",
            system="s", user_message="u", tools=[], tool_executor=lambda n, i: "ok",
            max_iterations=1, max_tool_streak=1,
        )
        assert called["native"] is True
        assert called["registry"] is False


def test_registry_tool_loop_rejects_empty_base_url(monkeypatch):
    """Defense: never POST to a relative URL when a provider isn't OpenAI-compatible."""
    class _Spec:
        tool_capable = True
        openai_compatible = False
        base_url = ""
        label = "Anthropic"

    monkeypatch.setattr("aethos_core.llm.model_providers.model_provider_spec", lambda p: _Spec())
    out = completion_mod.run_registry_provider_tool_loop(
        provider="anthropic", system="s", user_message="u", tools=[],
        tool_executor=lambda n, i: "ok", model="claude-opus-4-8",
    )
    assert out is None


def test_unsupported_protocol_is_not_retryable_or_transient():
    exc = httpx.UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol.")
    assert completion_mod._is_config_url_error(exc) is True
    assert completion_mod._retryable_http_error(exc) is False
    msg = completion_mod.format_provider_http_error(
        exc, provider_label="Anthropic", model="claude-opus-4-8", provider="anthropic"
    )
    assert "misrouted internally" in msg.lower()
    assert "timeout" not in msg.lower()
    assert "key is fine" not in msg.lower()


def test_live_model_list_from_cache(monkeypatch):
    """Adding a provider key surfaces fetched models in the catalog rows."""
    from aethos_core.llm.model_providers import _set_live_cache

    clear_live_model_cache_for_tests()
    _set_live_cache(
        "openai",
        [
            ("gpt-4o", "OpenAI · GPT-4o"),
            ("gpt-4o-mini", "OpenAI · GPT-4o mini"),
        ],
    )
    rows, source = live_model_rows("openai")
    assert source == "live"
    assert ("gpt-4o", "OpenAI · GPT-4o") in rows


def test_stale_model_id_rejected_with_supported_hint(monkeypatch):
    """A retired model id is rejected when not in live/fallback lists."""
    from aethos_core.llm.effective_model import ModelSelectionUnavailable, _resolve_explicit_selection
    from aethos_core.llm.model_providers import _set_live_cache

    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    get_settings.cache_clear()
    _set_live_cache("anthropic", [("claude-sonnet-4-6", "Claude Sonnet 4.6")])

    with pytest.raises(ModelSelectionUnavailable) as exc:
        _resolve_explicit_selection("anthropic:claude-sonnet-4-20250514", source="turn")
    assert "not supported" in str(exc.value.reason).lower() or "not recognized" in str(exc.value.reason).lower()


def test_arbiter_partial_failure_still_returns_consensus():
    """One model times out — consensus still returned from responders."""
    ok = ModelResponse(
        response_id="resp-a",
        provider="anthropic",
        model_id="claude-sonnet-4-6",
        model_label="Claude Sonnet 4.6",
        text="Answer A",
        used_llm=True,
    )
    ok_b = ModelResponse(
        response_id="resp-b",
        provider="openai",
        model_id="gpt-4o",
        model_label="GPT-4o",
        text="Answer B",
        used_llm=True,
    )
    failed = ModelResponse.error_response(
        "openrouter", "openai/gpt-4.1-mini", "OpenRouter mini", "timeout after 45s"
    )
    critiques = [
        CritiqueScore(
            critic_model_id="claude-sonnet-4-6",
            target_response_id="resp-a",
            accuracy_score=0.9,
            completeness_score=0.9,
            reasoning_score=0.9,
            overall_score=0.9,
            critique_text="good",
            recommended=True,
        ),
        CritiqueScore(
            critic_model_id="gpt-4o",
            target_response_id="resp-a",
            accuracy_score=0.85,
            completeness_score=0.85,
            reasoning_score=0.85,
            overall_score=0.85,
            critique_text="good",
            recommended=True,
        ),
    ]
    result = compute_consensus([ok, failed, ok_b], critiques, threshold=0.5)
    assert result.winning_text == "Answer A"
    assert result.responding_models == 2
    assert "failed" in result.summary.lower()
    assert "OpenRouter mini" in result.summary
