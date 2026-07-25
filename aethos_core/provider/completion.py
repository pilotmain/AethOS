# SPDX-License-Identifier: Apache-2.0
"""Quality-first provider completion (sync MVP)."""

from __future__ import annotations

import logging
import random
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

import httpx

from aethos_core.config import get_settings

if TYPE_CHECKING:
    from aethos_core.llm.effective_model import EffectiveModel

_log = logging.getLogger("aethos.completion")


def _resolved_anthropic_api_key() -> str:
    from aethos_core.llm.model_providers import resolve_anthropic_api_key

    return resolve_anthropic_api_key().strip()


def _resolved_openrouter_api_key() -> str:
    # .env first (operator/default tenant), then the per-tenant vault — same precedence
    # as every other provider. Without the vault fallback, a UI-added (vault-stored)
    # OpenRouter key validates on the card but is invisible to chat and the arbiter.
    env_key = str(getattr(get_settings(), "openrouter_api_key", "") or "").strip()
    if env_key:
        return env_key
    try:
        from aethos_core.llm.model_providers import resolve_model_provider_key

        return resolve_model_provider_key("openrouter")
    except Exception:
        return ""


def _openrouter_configured() -> bool:
    return bool(_resolved_openrouter_api_key())


def _record_model_ms(elapsed_ms: int) -> None:
    """Best-effort: attribute LLM HTTP wall-time to the current turn (§C5)."""
    try:
        from aethos_core.chat.route_timing import add_model_ms

        add_model_ms(elapsed_ms)
    except Exception:  # noqa: BLE001
        pass


@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str
    used_llm: bool = True
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    failover: bool = False
    failover_notice: str | None = None


@dataclass
class ToolLoopResult:
    text: str
    provider: str
    model: str
    used_llm: bool = True
    tool_calls: int = 0
    iterations: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    loop_outcome: str = "answered"


def _anthropic_usage(data: dict[str, Any]) -> tuple[int, int]:
    usage = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        return (0, 0)
    return (int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0))


def _anthropic_cache_usage(data: dict[str, Any]) -> tuple[int, int]:
    """(cache_read_input_tokens, cache_creation_input_tokens) for §1/§3."""
    usage = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        return (0, 0)
    return (
        int(usage.get("cache_read_input_tokens") or 0),
        int(usage.get("cache_creation_input_tokens") or 0),
    )


# §1 — Anthropic prompt caching. Marking a content block with cache_control caches
# the prefix up to and including that block; repeat turns re-read it cheaply.
def _prompt_cache_breakpoint() -> dict[str, Any] | None:
    """Return the cache_control marker (None when caching is disabled)."""
    s = get_settings()
    if not getattr(s, "prompt_cache_enabled", True):
        return None
    marker: dict[str, Any] = {"type": "ephemeral"}
    if str(getattr(s, "prompt_cache_retention", "short") or "short").lower() == "long":
        marker["ttl"] = "1h"
    return marker


def _prompt_cache_headers(base: dict[str, str]) -> dict[str, str]:
    """Add the extended-TTL beta header when long retention is requested."""
    marker = _prompt_cache_breakpoint()
    if marker is not None and marker.get("ttl") == "1h":
        headers = dict(base)
        headers["anthropic-beta"] = "extended-cache-ttl-2025-04-11"
        return headers
    return base


def _cacheable_system(system: str) -> Any:
    """System prompt as a cacheable content block when caching is on; else the raw string."""
    marker = _prompt_cache_breakpoint()
    text = system or ""
    if marker is None or not text.strip():
        return system
    return [{"type": "text", "text": text, "cache_control": marker}]


def _cacheable_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark the last tool with cache_control so the whole tool catalog is cached."""
    marker = _prompt_cache_breakpoint()
    if marker is None or not tools:
        return tools
    cached = [dict(t) for t in tools]
    cached[-1] = {**cached[-1], "cache_control": marker}
    return cached


# §9 — model failover. On a retryable provider failure, fall back to the next
# configured model so a rate limit or outage doesn't drop the turn.
def _is_config_url_error(exc: BaseException) -> bool:
    """A malformed/relative request URL or unsupported scheme — a wiring bug, not a network
    blip. Must never be retried or disguised as a transient outage."""
    invalid_url = getattr(httpx, "InvalidURL", ())
    return isinstance(exc, (httpx.UnsupportedProtocol, invalid_url))


def _retryable_http_error(exc: httpx.HTTPError) -> bool:
    """True for transient failures worth retrying on the next model within one provider."""
    resp = getattr(exc, "response", None)
    if resp is not None:
        status = getattr(resp, "status_code", 0)
        return status == 429 or 500 <= int(status or 0) < 600
    if _is_config_url_error(exc):
        return False
    return isinstance(exc, (httpx.TimeoutException, httpx.TransportError))


def _is_connection_error(exc: httpx.HTTPError) -> bool:
    """True when no usable response was received — the request never reached/finished at
    the model, so retrying (on a fresh socket) is always safe and almost always recovers.

    Covers the common 'valid key, transient connection error' cases: a stale pooled
    keepalive socket the provider already closed (RemoteProtocolError/ReadError), a DNS/TLS
    or reset blip (ConnectError/NetworkError), a slow connect (ConnectTimeout) and pool
    exhaustion (PoolTimeout). A plain ReadTimeout (model received the request but was slow)
    is retryable too, but is handled by the standard budget rather than the extra one.
    """
    if getattr(exc, "response", None) is not None:
        return False
    return isinstance(
        exc,
        (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.PoolTimeout,
            httpx.NetworkError,
            httpx.ProtocolError,
        ),
    )


def _provider_display_label(provider: str) -> str:
    from aethos_core.llm.model_providers import model_provider_spec

    spec = model_provider_spec(provider)
    if spec is not None:
        return spec.label
    return {
        "openrouter": "OpenRouter",
        "anthropic": "Anthropic",
        "local": "Local runtime",
    }.get((provider or "").strip().lower(), provider)


def format_provider_http_error(
    exc: httpx.HTTPError,
    *,
    provider_label: str,
    model: str,
    provider: str | None = None,
) -> str:
    """Map provider HTTP failures to honest, actionable operator messages."""
    resp = getattr(exc, "response", None)
    if resp is not None:
        status = int(getattr(resp, "status_code", 0) or 0)
        if status == 404:
            supported_hint = ""
            if provider:
                try:
                    from aethos_core.llm.model_providers import supported_model_ids_for_provider

                    ids = supported_model_ids_for_provider(provider)
                    if ids:
                        preview = ", ".join(ids[:8])
                        if len(ids) > 8:
                            preview += ", …"
                        supported_hint = f" Models your key supports: {preview}."
                except Exception:  # noqa: BLE001
                    pass
            return (
                f"{provider_label} returned 404 (model not found for your API key) — "
                f"the key in use can't access `{model}`. "
                "Check the key in Mission Control → Advanced settings → Credentials, or pick a model your key supports."
                f"{supported_hint}"
            )
        from aethos_core.llm.model_error_classifier import classify_status

        return classify_status(status, provider_label=provider_label)["message"]
    if _is_config_url_error(exc):
        # Internal routing/wiring bug (e.g. relative URL / unsupported scheme) — be honest so
        # it isn't mistaken for a provider outage or a credential problem.
        return (
            f"{provider_label} request was misrouted internally (provider endpoint not "
            "configured for this path). This is an AethOS routing bug, not your API key — "
            "please report it."
        )
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        # Normal single-model chat: a transient network blip is not a credential problem and
        # is not a reason to push a second provider (that's a failover/arbiter concern). Be
        # honest and short — your key is fine, just retry.
        return (
            f"{provider_label} didn't respond just now (transient network timeout/connection blip after "
            "automatic retries) — your API key is fine. Please send the message again."
        )
    from aethos_core.llm.model_error_classifier import classify_text

    return classify_text(str(exc), provider_label=provider_label)["message"]


def _provider_http_timeout() -> float:
    """Wall-clock cap per provider HTTP attempt so failover is fast on hangs."""
    return max(5.0, float(getattr(get_settings(), "provider_llm_timeout_sec", 45.0) or 45.0))


def _provider_timeout_config() -> httpx.Timeout:
    """Granular timeout: short connect (fail fast → retry on a fresh socket) + full read
    budget so a slow-but-working generation is never cut off."""
    total = _provider_http_timeout()
    connect = max(2.0, min(float(getattr(get_settings(), "provider_llm_connect_timeout_sec", 10.0) or 10.0), total))
    return httpx.Timeout(total, connect=connect, read=total, write=total, pool=connect)


def _provider_transient_retries() -> int:
    return max(0, min(6, int(getattr(get_settings(), "provider_llm_transient_retries", 4) or 4)))


def _provider_connection_error_extra_retries() -> int:
    return max(0, min(4, int(getattr(get_settings(), "provider_llm_connection_error_extra_retries", 2) or 2)))


def _provider_retry_backoff_sec() -> float:
    return max(0.1, float(getattr(get_settings(), "provider_llm_retry_backoff_sec", 0.75) or 0.75))


def _provider_keepalive_expiry_sec() -> float:
    return max(1.0, float(getattr(get_settings(), "provider_llm_keepalive_expiry_sec", 20.0) or 20.0))


_HTTP_CLIENT_LOCK = threading.Lock()
_HTTP_CLIENT: httpx.Client | None = None


def _get_provider_http_client() -> httpx.Client:
    """Shared httpx client with keepalive — avoids repeated TLS handshakes on blips.

    keepalive_expiry is bounded so we don't reuse a socket the provider has already closed
    after the app sat idle (the classic 'connection error on a valid key' cause).
    """
    global _HTTP_CLIENT
    with _HTTP_CLIENT_LOCK:
        if _HTTP_CLIENT is None:
            _HTTP_CLIENT = httpx.Client(
                limits=httpx.Limits(
                    max_keepalive_connections=24,
                    max_connections=48,
                    keepalive_expiry=_provider_keepalive_expiry_sec(),
                ),
            )
        return _HTTP_CLIENT


def _http_request_with_transient_retry(method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Retry transient timeouts/connection/429/5xx on the same provider before failing.

    A valid key must survive a transient blip. Connection-level failures (no response from
    the model) get extra attempts and a near-instant first retry on a fresh socket; all
    retries use exponential backoff with jitter and a hard per-sleep cap. Non-retryable
    failures (401/403/404 and other 4xx) raise immediately so real errors stay fast.
    """
    client = _get_provider_http_client()
    timeout = kwargs.pop("timeout", None) or _provider_timeout_config()
    base_attempts = 1 + _provider_transient_retries()
    max_attempts = base_attempts
    last_exc: httpx.HTTPError | None = None
    attempt = 0
    while attempt < max_attempts:
        try:
            response = client.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:
            last_exc = exc
            if not _retryable_http_error(exc):
                raise
            conn_err = _is_connection_error(exc)
            if conn_err:
                # The model never answered — safe to keep trying a fresh connection.
                max_attempts = max(max_attempts, base_attempts + _provider_connection_error_extra_retries())
            if attempt >= max_attempts - 1:
                raise
            base = _provider_retry_backoff_sec()
            if conn_err and attempt == 0:
                backoff = 0.0  # a fresh socket usually succeeds immediately
            else:
                backoff = min(base * (2 ** attempt), 8.0) + random.uniform(0.0, base * 0.5)
            if backoff > 0:
                time.sleep(backoff)
            attempt += 1
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("http_request_with_transient_retry: no response")


def _other_model_providers_configured(exclude_provider: str) -> bool:
    """True when another model provider (besides exclude) has credentials configured."""
    exclude = (exclude_provider or "").strip().lower()
    from aethos_core.llm.model_providers import configured_model_providers, model_provider_configured

    if exclude not in ("openrouter",) and _openrouter_configured():
        return True
    if exclude not in ("anthropic", "claude") and model_provider_configured("anthropic"):
        return True
    for spec in configured_model_providers():
        if spec.id != exclude:
            return True
    if exclude != "local" and _local_llm_ready():
        return True
    return False


def _failover_model_chain(primary: str) -> list[str]:
    """Ordered model chain: primary first, then the configured fallbacks."""
    chain = [primary]
    s = get_settings()
    if getattr(s, "model_failover_enabled", False):
        for candidate in str(getattr(s, "model_failover_chain", "") or "").split(","):
            candidate = candidate.strip()
            if candidate and candidate not in chain:
                chain.append(candidate)
    return chain


# §3/§5 — cross-provider failover. The ordered chain is: the user's selected model
# first, then one model per *other* configured provider (never multiple models on the
# same provider). Bounded by MODEL_FAILOVER_MAX_ATTEMPTS.
def provider_failover_chain(provider: str, model: str, label: str) -> list[tuple[str, str, str]]:
    """Ordered (provider, model, label) attempts honoring the user's selection first."""
    s = get_settings()
    attempts: list[tuple[str, str, str]] = [(provider, model, label)]
    if not getattr(s, "model_failover_enabled", False):
        return attempts
    seen_providers: set[str] = {(provider or "").strip().lower()}

    def _add_provider(prov: str, mdl: str, lbl: str) -> None:
        prov_key = (prov or "").strip().lower()
        if not mdl or prov_key in seen_providers:
            return
        seen_providers.add(prov_key)
        attempts.append((prov, mdl, lbl))

    from aethos_core.llm.model_catalog import _served_foundry_rows, default_catalog_entry
    from aethos_core.llm.model_providers import (
        configured_model_providers,
        model_provider_configured,
        model_provider_rows,
    )

    if model_provider_configured("anthropic"):
        a = default_catalog_entry(provider="anthropic")
        if a is not None:
            _add_provider("anthropic", str(a["model"]), str(a["label"]))
    if model_provider_configured("openrouter") or _openrouter_configured():
        o = default_catalog_entry(provider="openrouter")
        if o is not None:
            _add_provider("openrouter", str(o["model"]), str(o["label"]))
    for mp in configured_model_providers():
        rows = model_provider_rows(mp)
        if rows:
            _add_provider(mp.id, rows[0][0], rows[0][1])
    for model_id, lbl, _endpoint in _served_foundry_rows():
        _add_provider("local", model_id, lbl)
    if _local_llm_ready():
        m = str(getattr(s, "local_llm_default_model", "") or "llama3.2")
        _add_provider("local", m, f"Local · {m}")

    cap = max(1, int(getattr(s, "model_failover_max_attempts", 3) or 3))
    return attempts[:cap]


def _short_failure_reason(text: str) -> str:
    low = str(text or "").lower()
    if "404" in low or "model not found" in low:
        return "model not found (404)"
    if "429" in low or "rate limit" in low:
        return "rate-limited (429)"
    if "timeout" in low or "timed out" in low:
        return "timed out"
    if "401" in low or "403" in low or "api key" in low or "key rejected" in low or "auth failed" in low:
        return "auth failed"
    if "not configured" in low or "no key" in low:
        return "no key configured"
    if "5" in low and ("server error" in low or "internal" in low):
        return "server error (5xx)"
    return "unavailable"


def _tool_loop_hard_failure(result: ToolLoopResult | None) -> bool:
    """True when a tool-loop attempt failed and the chain should try the next provider."""
    if result is None:
        return True
    if result.loop_outcome == "error_degraded":
        return True
    if not result.used_llm and result.tool_calls == 0:
        return True
    return False


def _build_failover_notice(failed: list[tuple[str, str]], answered_label: str) -> str:
    """One honest line: what failed and what actually answered."""
    if not failed:
        return ""
    parts = "; ".join(f"{lbl} {reason}" for lbl, reason in failed)
    return f"_{parts}; continued on {answered_label}._"


def _all_providers_failed_text(
    failed: list[tuple[str, str]],
    providers_tried: set[str],
) -> str:
    reasons = "; ".join(f"{lbl} {reason}" for lbl, reason in failed)
    if len(providers_tried) <= 1:
        # Single-provider chat — don't push a second provider (failover/arbiter concern only).
        # Name the real reason so a missing/invalid key is never disguised as a generic outage.
        return (
            f"Couldn't complete the turn: {reasons}. "
            "Retry shortly, or check the provider key in Mission Control → Advanced settings → Credentials."
        )
    return (
        f"All configured providers failed: {reasons}. "
        "Retry shortly or check provider keys in Mission Control → Advanced settings → Credentials."
    )


def _complete_one_attempt(
    user_text: str,
    *,
    provider: str,
    model: str,
    include_identity: bool,
    system_overlay: str | None,
) -> ProviderResult:
    """Run a single provider attempt (no failover) for the failover chain."""
    s = get_settings()
    if provider == "openrouter":
        api_key = _resolved_openrouter_api_key()
        if api_key:
            return _openrouter_complete(user_text, api_key, model)
        return ProviderResult(text="OpenRouter not configured.", provider="openrouter", model=model, used_llm=False)
    if provider == "local":
        served_base = _served_local_base_url(model)
        base_url = served_base or (str(getattr(s, "local_llm_base_url", "") or "") if _local_llm_ready() else "")
        if base_url:
            return _local_llm_complete(
                user_text,
                base_url=base_url,
                model=model,
                api_key=str(getattr(s, "local_llm_api_key", "") or ""),
                include_identity=include_identity,
                system_overlay=system_overlay,
            )
        return ProviderResult(text="Local runtime not available.", provider="local", model=model, used_llm=False)
    if provider in ("anthropic", "claude") and _resolved_anthropic_api_key():
        return _anthropic_complete(
            user_text,
            _resolved_anthropic_api_key(),
            model,
            include_identity=include_identity,
            system_overlay=system_overlay,
        )
    from aethos_core.llm.model_providers import is_registry_provider

    if is_registry_provider(provider):
        return _registry_provider_complete(user_text, provider=provider, model=model)
    return ProviderResult(text=f"Provider {provider} not configured.", provider=provider, model=model, used_llm=False)


def _openai_usage(data: dict[str, Any]) -> tuple[int, int]:
    usage = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        return (0, 0)
    return (int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0))


def provider_configured() -> bool:
    s = get_settings()
    # A governed + served local model is self-sufficient: an operator who approved
    # and served it should be able to chat with it regardless of the Anthropic gate.
    if _served_foundry_model_available():
        return True
    if not s.use_real_llm:
        return False
    if s.active_provider == "anthropic" and _resolved_anthropic_api_key():
        return True
    if s.active_provider == "openrouter" and str(getattr(s, "openrouter_api_key", "") or "").strip():
        return True
    if s.active_provider in ("anthropic", "claude") and _resolved_anthropic_api_key():
        return True
    if s.active_provider == "local" and _local_llm_ready():
        return True
    # §2 — any configured model-API provider makes the runtime usable. This also
    # covers a session model override picking a configured provider.
    from aethos_core.llm.model_providers import configured_model_providers

    if configured_model_providers():
        return True
    return False


def _local_llm_ready() -> bool:
    s = get_settings()
    return bool(getattr(s, "local_llm_enabled", False) and str(getattr(s, "local_llm_base_url", "") or "").strip())


def _served_foundry_model_available() -> bool:
    """True when at least one governed Model Foundry model is currently served."""
    try:
        from aethos_core.workspace_suite.model_foundry import list_served_models

        return bool(list_served_models())
    except Exception:
        return False


def _served_local_base_url(model: str) -> str:
    """OpenAI-compatible base URL for a served Foundry model, else empty."""
    try:
        from aethos_core.workspace_suite.model_foundry import served_model_endpoint

        endpoint = served_model_endpoint(model)
        if not endpoint:
            return ""
        root = endpoint.rstrip("/")
        if root.endswith("/v1") or root.endswith("/chat/completions"):
            return root
        return f"{root}/v1"
    except Exception:
        return ""


def generative_fallback(user_text: str, *, session_id: str = "default") -> ProviderResult:
    from aethos_core.chat.deterministic import (
        GENERIC_FALLBACK_MARKER,
        provider_setup_footer,
        try_partial_template,
    )
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_hard_preemption,
    )

    hard = route_workflow_discovery_hard_preemption(user_text, session_id=session_id)
    if hard is not None:
        reply, _intent, _meta = hard
        return ProviderResult(text=reply, provider="github", model="workflow_discovery", used_llm=False)

    partial = try_partial_template(user_text, session_id=session_id)
    preview = (user_text or "").strip()[:240]
    if partial:
        body = (
            "I can answer this better once generative intelligence is configured, but here is the safe operational answer:\n\n"
            f"{partial}\n\n"
            f"{provider_setup_footer()}"
        )
    else:
        body = (
            "I can answer this better once generative intelligence is configured. "
            "For now, tell me what you'd like to work through — governed operational responses remain fully available.\n\n"
            f"Your message: _{preview}_\n\n"
            f"{provider_setup_footer()}"
        )
    assert GENERIC_FALLBACK_MARKER not in body
    return ProviderResult(text=body, provider="none", model="template", used_llm=False)


def complete_chat(
    user_text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    include_identity: bool = True,
    system_overlay: str | None = None,
    model_override: str | None = None,
) -> ProviderResult:
    """Lane B — single-shot provider completion."""
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts
    from aethos_core.llm.effective_model import (
        EffectiveModel,
        ModelSelectionUnavailable,
        model_unavailable_reply,
        resolve_effective_model,
    )

    load_identity_contracts()

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        enforce_workflow_discovery_absolute_lane,
    )
    from aethos_core.chat.lane_hydration import maybe_hydrate_lane_contexts

    maybe_hydrate_lane_contexts(text=user_text, session_id=session_id)
    absolute = enforce_workflow_discovery_absolute_lane(user_text, session_id=session_id)
    if absolute is not None:
        reply, _intent, _meta = absolute
        return ProviderResult(text=reply, provider="github", model="workflow_discovery", used_llm=False)

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_hard_preemption,
    )

    hard = route_workflow_discovery_hard_preemption(user_text, session_id=session_id)
    if hard is not None:
        reply, _intent, _meta = hard
        return ProviderResult(text=reply, provider="github", model="workflow_discovery", used_llm=False)

    from aethos_core.tenancy.tenant_metering import check_llm_token_quota

    quota_ok, retry_after = check_llm_token_quota()
    if not quota_ok:
        mins = max(1, retry_after // 60)
        return ProviderResult(
            text=(
                f"Daily LLM token quota reached for your account. "
                f"Try again in about {mins} minute{'s' if mins != 1 else ''}, or contact the operator."
            ),
            provider="none",
            model="quota",
            used_llm=False,
        )

    if not provider_configured():
        from aethos_core.conversation.polish_compat import try_grounded_chat_reply

        grounded = try_grounded_chat_reply(user_text, session_id=session_id, channel=channel)
        if grounded is not None:
            body, _, _ = grounded
            return ProviderResult(text=body, provider="grounding", model="continuity", used_llm=False)
        return generative_fallback(user_text, session_id=session_id)

    try:
        effective = resolve_effective_model(
            session_id=session_id, turn_override=model_override, prompt=user_text
        )
    except ModelSelectionUnavailable as exc:
        return ProviderResult(
            text=model_unavailable_reply(exc.catalog_id, exc.reason),
            provider="none",
            model=exc.catalog_id,
            used_llm=False,
        )
    context_block = _build_grounding_context_block(session_id=session_id, channel=channel)
    augmented = f"{context_block}\n\n{user_text}" if context_block else user_text
    result = _complete_with_failover(
        augmented,
        effective,
        include_identity=include_identity,
        system_overlay=system_overlay,
        session_id=session_id,
    )
    record_completion_usage(result, session_id=session_id)
    return result


def _complete_with_failover(
    user_text: str,
    effective: "EffectiveModel",
    *,
    include_identity: bool,
    system_overlay: str | None,
    session_id: str,
) -> ProviderResult:
    """Run the selected model, then honestly fail over across configured providers.

    Honors the user's pick first. On a provider failure (429/5xx/auth/timeout) it
    continues on the next provider — or local — and labels the swap (never silent).
    Bounded by MODEL_FAILOVER_MAX_ATTEMPTS; if the whole chain fails, returns one
    clear error rather than looping.
    """
    attempts = provider_failover_chain(effective.provider, effective.model, effective.label)
    if len(attempts) <= 1 and not getattr(get_settings(), "model_failover_enabled", False):
        # No configured fallbacks — keep the original single-path behavior.
        return _complete_with_effective_model(
            user_text, effective, include_identity=include_identity, system_overlay=system_overlay
        )

    failed: list[tuple[str, str]] = []
    providers_tried: set[str] = set()
    for idx, (prov, model, label) in enumerate(attempts):
        providers_tried.add(prov)
        res = _complete_one_attempt(
            user_text,
            provider=prov,
            model=model,
            include_identity=include_identity,
            system_overlay=system_overlay,
        )
        if res.used_llm:
            if idx > 0:
                res.failover = True
                res.failover_notice = _build_failover_notice(failed, label)
                if res.failover_notice:
                    res.text = f"{res.failover_notice}\n\n{res.text}"
            return res
        # Record any attempt that consumed tokens (defensive — error paths are 0).
        if res.input_tokens or res.output_tokens:
            record_completion_usage(res, session_id=session_id)
        failed.append((label, _short_failure_reason(res.text)))

    reasons = _all_providers_failed_text(failed, providers_tried)
    return ProviderResult(
        text=reasons,
        provider=effective.provider,
        model=effective.model,
        used_llm=False,
        failover=True,
        failover_notice=reasons,
    )


def record_completion_usage(result: "ProviderResult | ToolLoopResult", *, session_id: str) -> None:
    """Record real per-turn token usage + cost for an LLM completion."""
    try:
        if not getattr(result, "used_llm", False):
            return
        in_tok = int(getattr(result, "input_tokens", 0) or 0)
        out_tok = int(getattr(result, "output_tokens", 0) or 0)
        if not (in_tok or out_tok):
            return
        from aethos_core.observability.metering import record_turn_usage

        record_turn_usage(
            session_id=session_id,
            model=getattr(result, "model", None),
            input_tokens=in_tok,
            output_tokens=out_tok,
            provider=getattr(result, "provider", None),
            cache_read_tokens=int(getattr(result, "cache_read_tokens", 0) or 0),
            cache_creation_tokens=int(getattr(result, "cache_creation_tokens", 0) or 0),
        )
    except Exception:
        # Metering must never break a chat turn.
        pass


def _complete_with_effective_model(
    user_text: str,
    effective: "EffectiveModel",
    *,
    include_identity: bool = True,
    system_overlay: str | None = None,
) -> ProviderResult:
    s = get_settings()
    if effective.provider == "openrouter":
        api_key = str(getattr(s, "openrouter_api_key", "") or "").strip()
        if api_key:
            return _openrouter_complete(user_text, api_key, effective.model)
    if effective.provider == "local":
        served_base = _served_local_base_url(effective.model)
        base_url = served_base or (
            str(getattr(s, "local_llm_base_url", "") or "") if _local_llm_ready() else ""
        )
        if base_url:
            return _local_llm_complete(
                user_text,
                base_url=base_url,
                model=effective.model,
                api_key=str(getattr(s, "local_llm_api_key", "") or ""),
                include_identity=include_identity,
                system_overlay=system_overlay,
            )
    if effective.provider == "anthropic" and _resolved_anthropic_api_key():
        return _anthropic_complete(
            user_text,
            _resolved_anthropic_api_key(),
            effective.model,
            include_identity=include_identity,
            system_overlay=system_overlay,
        )
    from aethos_core.llm.model_providers import is_registry_provider, model_provider_configured

    if is_registry_provider(effective.provider) and model_provider_configured(effective.provider):
        return _registry_provider_complete(user_text, provider=effective.provider, model=effective.model)
    if s.active_provider == "openrouter" and str(getattr(s, "openrouter_api_key", "") or "").strip():
        return _openrouter_complete(
            user_text,
            str(getattr(s, "openrouter_api_key", "") or ""),
            str(getattr(s, "openrouter_model", "openrouter/auto")),
        )
    if _resolved_anthropic_api_key():
        return _anthropic_complete(
            user_text,
            _resolved_anthropic_api_key(),
            s.anthropic_model,
            include_identity=include_identity,
            system_overlay=system_overlay,
        )
    return generative_fallback(user_text)


def _persona_context_lines() -> list[str]:
    """Rapport context — address the operator by name and match their tone."""
    try:
        from aethos_core.config import get_settings

        if not getattr(get_settings(), "aethos_onboarding_enabled", True):
            return []
        from aethos_core.onboarding.operator_persona import get_persona

        persona = get_persona()
        name = (persona.get("name") or "").strip()
        if not name:
            return []
        tone = str(persona.get("tone") or "warm")
        goals = [g for g in (persona.get("goals") or []) if g]
        lines = [f"Operator: {name} — address them by name naturally; preferred tone: {tone}."]
        if goals:
            lines.append(f"Their stated goals: {', '.join(goals[:3])}.")
        return lines
    except Exception:
        return []


def _build_grounding_context_block(*, session_id: str, channel: str) -> str:
    persona_lines = _persona_context_lines()
    conversation_lines: list[str] = []
    try:
        from aethos_core.chat.conversation_context import compose_conversation_llm_context

        conv = compose_conversation_llm_context(session_id)
        if conv:
            conversation_lines = [conv]
    except Exception:
        pass
    try:
        from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge

        bridge = build_operational_context_bridge(session_id=session_id, channel=channel)
        if not bridge.get("has_memory"):
            return "\n".join(persona_lines + conversation_lines)
        subject = bridge.get("primary_subject") or "active operational thread"
        investigations = bridge.get("active_investigations") or []
        unresolved = bridge.get("unresolved_issues") or []
        lines = [
            "Operational continuity context (use this — do not ask for clarification unless truly unknown):",
            f"- Active subject: {subject}",
        ]
        if investigations:
            lines.append(f"- Active investigations: {', '.join(investigations[:3])}")
        if unresolved:
            lines.append(f"- Open concerns: {', '.join(unresolved[:3])}")
        lines.append("- Respond as a continuously operationally aware partner, not a generic assistant.")
        return "\n".join(persona_lines + conversation_lines + lines)
    except Exception:
        return "\n".join(persona_lines + conversation_lines)


def _anthropic_complete(
    user_text: str,
    api_key: str,
    model: str,
    *,
    include_identity: bool = True,
    system_overlay: str | None = None,
) -> ProviderResult:
    from aethos_core.aethos_identity.identity_contract_loader import build_identity_system_persona_block
    from aethos_core.identity.operational_voice import LLM_SYSTEM_PERSONA

    identity_block = build_identity_system_persona_block() if include_identity else ""
    system = LLM_SYSTEM_PERSONA
    if identity_block:
        system = f"{LLM_SYSTEM_PERSONA}\n\n{identity_block}"
    if system_overlay and system_overlay.strip():
        system = f"{system}\n\n{system_overlay.strip()}"
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": _cacheable_system(system),
        "messages": [{"role": "user", "content": user_text}],
    }
    headers = _prompt_cache_headers(
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    answered_model = model
    try:
        r = _http_request_with_transient_retry(
            "POST",
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
        )
        data = r.json()
    except httpx.HTTPError as exc:
        label = _provider_display_label("anthropic")
        return ProviderResult(
            text=format_provider_http_error(exc, provider_label=label, model=model, provider="anthropic"),
            provider="anthropic",
            model=model,
            used_llm=False,
        )
    model = answered_model

    parts: list[str] = []
    for block in data.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    text = "".join(parts).strip() or "Provider returned an empty response."
    in_tok, out_tok = _anthropic_usage(data)
    cache_read, cache_creation = _anthropic_cache_usage(data)
    return ProviderResult(
        text=text,
        provider="anthropic",
        model=model,
        used_llm=True,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_creation,
    )


MAX_TOOL_RESULT_CHARS = 12_000


def _truncate_tool_result(text: str, *, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    raw = str(text or "")
    if len(raw) <= max_chars:
        return raw
    suffix = "\n\n...[tool result truncated for speed; narrow the request for full detail]..."
    return raw[: max(0, max_chars - len(suffix))] + suffix


def _short_thought(text: str, limit: int = 180) -> str:
    """One-line, secret-free condensation of model reasoning for narration."""
    from aethos_core.security.secret_redaction import redact_text

    one_line = " ".join(str(text or "").split())
    if len(one_line) > limit:
        one_line = one_line[: limit - 1] + "…"
    return redact_text(one_line)


def _run_tool_loop_one_attempt(
    provider: str,
    model: str,
    *,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    max_iterations: int,
    max_tool_streak: int,
    channel: str = "chat",
) -> ToolLoopResult | None:
    """Single-provider agent tool loop attempt (no cross-provider failover)."""
    from aethos_core.llm.model_providers import is_registry_provider

    if provider == "local":
        return run_local_tool_loop(
            system=system,
            user_message=user_message,
            tools=tools,
            tool_executor=tool_executor,
            model=model,
            max_iterations=max_iterations,
            max_tool_streak=max_tool_streak,
        )
    if provider == "openrouter":
        return run_openrouter_tool_loop(
            system=system,
            user_message=user_message,
            tools=tools,
            tool_executor=tool_executor,
            model=model,
            max_iterations=max_iterations,
            max_tool_streak=max_tool_streak,
        )
    # Native Anthropic MUST be checked before the registry path: Anthropic is also a
    # connections-catalog ("registry") provider, but its spec is not OpenAI-compatible and
    # has no base_url, so routing it through the OpenAI-compatible registry tool loop would
    # POST to a relative "/chat/completions" (UnsupportedProtocol). Use the messages API.
    if provider in ("anthropic", "claude"):
        return run_anthropic_tool_loop(
            system=system,
            user_message=user_message,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=max_iterations,
            max_tool_streak=max_tool_streak,
            channel=channel,
            model=model,
        )
    if is_registry_provider(provider):
        return run_registry_provider_tool_loop(
            provider=provider,
            system=system,
            user_message=user_message,
            tools=tools,
            tool_executor=tool_executor,
            model=model,
            max_iterations=max_iterations,
            max_tool_streak=max_tool_streak,
        )
    return None


def run_tool_loop_with_provider_failover(
    effective: "EffectiveModel",
    *,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    max_iterations: int = 8,
    max_tool_streak: int = 20,
    channel: str = "chat",
) -> ToolLoopResult | None:
    """Run the agent tool loop on the selected model, then fail over across providers.

    Honors the user's selection first. On a hard provider failure (404/401/5xx/timeout)
    continues on the next configured provider. Only when every attempt fails returns
    one error naming each provider tried and the real reason.
    """
    attempts = provider_failover_chain(effective.provider, effective.model, effective.label)
    if len(attempts) <= 1:
        return _run_tool_loop_one_attempt(
            effective.provider,
            effective.model,
            system=system,
            user_message=user_message,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=max_iterations,
            max_tool_streak=max_tool_streak,
            channel=channel,
        )

    failed: list[tuple[str, str]] = []
    providers_tried: set[str] = set()
    for idx, (prov, model, label) in enumerate(attempts):
        providers_tried.add(prov)
        loop_out = _run_tool_loop_one_attempt(
            prov,
            model,
            system=system,
            user_message=user_message,
            tools=tools,
            tool_executor=tool_executor,
            max_iterations=max_iterations,
            max_tool_streak=max_tool_streak,
            channel=channel,
        )
        if _tool_loop_hard_failure(loop_out):
            reason = "no key configured"
            if loop_out is not None:
                reason = _short_failure_reason(loop_out.text)
            failed.append((label, reason))
            continue
        if idx > 0 and failed:
            notice = _build_failover_notice(failed, label)
            if notice:
                loop_out.text = f"{notice}\n\n{loop_out.text}"
        return loop_out

    return ToolLoopResult(
        text=_all_providers_failed_text(failed, providers_tried),
        provider=effective.provider,
        model=effective.model,
        used_llm=False,
        loop_outcome="error_degraded",
    )


def run_anthropic_tool_loop(
    *,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    max_iterations: int = 8,
    max_tool_streak: int = 20,
    channel: str = "chat",
    model: str | None = None,
) -> ToolLoopResult | None:
    """Inner agent loop — Anthropic messages API with tool_use blocks."""
    from aethos_core.agents.runtime.tool_call_repair import (
        allowed_names_from_tools,
        classify_loop_outcome,
        parse_tool_arguments,
        repair_result_text,
        validate_tool_call,
        ToolCallRepairBudget,
    )
    from aethos_core.execution_brain.agent_context_compaction import (
        compact_messages_for_tool_loop,
        should_compact_messages,
    )
    from aethos_core.execution_brain.agent_tool_loop_detection import ToolLoopDetector, stuck_tool_result
    from aethos_core.execution_brain.agent_tool_policy import filter_tool_schemas

    s = get_settings()
    api_key = _resolved_anthropic_api_key()
    if not s.use_real_llm or not api_key:
        return None
    resolved_model = (model or s.anthropic_model).strip() or s.anthropic_model
    headers = _prompt_cache_headers(
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    scoped_tools = _cacheable_tools(filter_tool_schemas(tools, channel=channel))
    allowed_tool_names = allowed_names_from_tools(scoped_tools)
    cacheable_system = _cacheable_system(system)
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    tool_calls = 0
    streak = 0
    step_seq = 0
    agg_in = 0
    agg_out = 0
    agg_cache_read = 0
    agg_cache_creation = 0
    detector = ToolLoopDetector() if s.agent_tool_loop_detection_enabled else None
    repair_budget = ToolCallRepairBudget()
    # §1 — live progress narration (read-only; no-op when no sink/flag off).
    from aethos_core.execution_brain.agent_tool_executor import (
        emit_progress,
        humanize_tool_action,
        humanize_tool_result,
    )

    for iteration in range(1, max_iterations + 1):
        if s.agent_context_compaction_enabled and should_compact_messages(messages):
            messages = compact_messages_for_tool_loop(messages, api_key=api_key, model=resolved_model)

        payload = {
            "model": resolved_model,
            "max_tokens": 2048,
            "system": cacheable_system,
            "tools": scoped_tools,
            "messages": messages,
        }
        from time import perf_counter as _pc

        _model_t0 = _pc()
        try:
            response = _http_request_with_transient_retry(
                "POST",
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
            )
            data = response.json()
        except httpx.HTTPError as exc:
            _record_model_ms(int((_pc() - _model_t0) * 1000))
            label = _provider_display_label("anthropic")
            return ToolLoopResult(
                text=format_provider_http_error(exc, provider_label=label, model=resolved_model, provider="anthropic"),
                provider="anthropic",
                model=resolved_model,
                used_llm=False,
                tool_calls=tool_calls,
                iterations=iteration,
                input_tokens=agg_in,
                output_tokens=agg_out,
                cache_read_tokens=agg_cache_read,
                cache_creation_tokens=agg_cache_creation,
                loop_outcome="error_degraded",
            )

        _record_model_ms(int((_pc() - _model_t0) * 1000))
        _it, _ot = _anthropic_usage(data)
        _cr, _cc = _anthropic_cache_usage(data)
        agg_in += _it
        agg_out += _ot
        agg_cache_read += _cr
        agg_cache_creation += _cc
        content_blocks = data.get("content") or []
        stop_reason = str(data.get("stop_reason") or "")
        assistant_content: list[dict[str, Any]] = []
        text_parts: list[str] = []
        pending_tools: list[dict[str, Any]] = []

        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                text_parts.append(str(block.get("text") or ""))
                assistant_content.append({"type": "text", "text": str(block.get("text") or "")})
            elif btype == "tool_use":
                pending_tools.append(block)
                assistant_content.append(block)

        if pending_tools:
            reasoning = "".join(text_parts).strip()
            if reasoning:
                emit_progress({"type": "thought", "text": _short_thought(reasoning)})
            streak += len(pending_tools)
            if streak > max_tool_streak:
                return ToolLoopResult(
                    text=(
                        "Agent runtime stopped: tool loop limit reached. "
                        "Try a narrower question or disable agent runtime."
                    ),
                    provider="anthropic",
                    model=resolved_model,
                    used_llm=True,
                    tool_calls=tool_calls,
                    iterations=iteration,
                    input_tokens=agg_in,
                    output_tokens=agg_out,
                    cache_read_tokens=agg_cache_read,
                    cache_creation_tokens=agg_cache_creation,
                )
            messages.append({"role": "assistant", "content": assistant_content})
            tool_result_blocks: list[dict[str, Any]] = []
            for tool_block in pending_tools:
                tool_name = str(tool_block.get("name") or "")
                tool_id = str(tool_block.get("id") or "")
                tool_input = tool_block.get("input") if isinstance(tool_block.get("input"), dict) else {}
                parse_hint: str | None = None
                if not isinstance(tool_block.get("input"), dict):
                    tool_input, parse_hint = parse_tool_arguments(tool_block.get("input"))
                repair_hint = parse_hint or validate_tool_call(
                    tool_name, dict(tool_input), allowed_names=allowed_tool_names
                )
                step_seq += 1
                step_id = f"step-{step_seq}"
                emit_progress(
                    {
                        "type": "step",
                        "id": step_id,
                        "tool": tool_name,
                        "action": humanize_tool_action(tool_name, dict(tool_input)),
                        "status": "running",
                    }
                )
                if repair_hint:
                    if repair_budget.allow_repair():
                        repair_budget.record_repair()
                        result_text = repair_result_text(repair_hint, exhausted=repair_budget.exhausted)
                    else:
                        result_text = repair_result_text(
                            "Too many malformed tool calls — answer in plain text.",
                            exhausted=True,
                        )
                elif detector is not None:
                    stuck, reason = detector.check_before(tool_name, dict(tool_input))
                    if stuck:
                        result_text = stuck_tool_result(tool_name, reason)
                    else:
                        result_text = _truncate_tool_result(tool_executor(tool_name, dict(tool_input)))
                        detector.record(tool_name, dict(tool_input))
                else:
                    result_text = _truncate_tool_result(tool_executor(tool_name, dict(tool_input)))
                _step_status, _step_summary = humanize_tool_result(tool_name, result_text)
                emit_progress(
                    {
                        "type": "step",
                        "id": step_id,
                        "tool": tool_name,
                        "status": _step_status,
                        "summary": _step_summary,
                    }
                )
                tool_calls += 1
                tool_result_blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_text,
                    }
                )
            messages.append({"role": "user", "content": tool_result_blocks})
            continue

        final_text = "".join(text_parts).strip()
        if not final_text:
            final_text = "Agent runtime returned an empty response."
        return ToolLoopResult(
            text=final_text,
            provider="anthropic",
            model=resolved_model,
            used_llm=True,
            tool_calls=tool_calls,
            iterations=iteration,
            input_tokens=agg_in,
            output_tokens=agg_out,
            cache_read_tokens=agg_cache_read,
            cache_creation_tokens=agg_cache_creation,
            loop_outcome=classify_loop_outcome(final_text, tool_calls=tool_calls),
        )

    return ToolLoopResult(
        text="Agent runtime stopped: maximum iterations reached.",
        provider="anthropic",
        model=resolved_model,
        used_llm=True,
        tool_calls=tool_calls,
        iterations=max_iterations,
        input_tokens=agg_in,
        output_tokens=agg_out,
        cache_read_tokens=agg_cache_read,
        cache_creation_tokens=agg_cache_creation,
        loop_outcome=classify_loop_outcome(
            "Agent runtime stopped: maximum iterations reached.",
            tool_calls=tool_calls,
            degraded=True,
        ),
    )


def _local_llm_complete(
    user_text: str,
    *,
    base_url: str,
    model: str,
    api_key: str = "",
    include_identity: bool = True,
    system_overlay: str | None = None,
) -> ProviderResult:
    from aethos_core.aethos_identity.identity_contract_loader import build_identity_system_persona_block
    from aethos_core.identity.operational_voice import LLM_SYSTEM_PERSONA

    identity_block = build_identity_system_persona_block() if include_identity else ""
    system = LLM_SYSTEM_PERSONA
    if identity_block:
        system = f"{LLM_SYSTEM_PERSONA}\n\n{identity_block}"
    if system_overlay and system_overlay.strip():
        system = f"{system}\n\n{system_overlay.strip()}"
    root = base_url.rstrip("/")
    url = root if root.endswith("/chat/completions") else f"{root}/chat/completions"
    payload = {
        "model": _local_runtime_model_name(model),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    try:
        response = _http_request_with_transient_retry("POST", url, json=payload, headers=headers)
        data = response.json()
    except httpx.HTTPError as exc:
        return ProviderResult(
            text=f"Local LLM request failed: {exc}. Check LOCAL_LLM_BASE_URL and model name.",
            provider="local",
            model=model,
            used_llm=False,
        )
    choices = data.get("choices") if isinstance(data, dict) else []
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else {}
        text = str((message or {}).get("content") or "").strip()
        if text:
            in_tok, out_tok = _openai_usage(data)
            return ProviderResult(
                text=text, provider="local", model=model, used_llm=True, input_tokens=in_tok, output_tokens=out_tok
            )
    return ProviderResult(text="Local LLM returned an empty response.", provider="local", model=model, used_llm=False)


def local_tool_loop_base_url(model: str) -> str:
    """OpenAI-compatible base URL for the local tool loop (served endpoint first).

    A served Foundry model is self-sufficient: when its loopback endpoint resolves we
    use it directly, so the operator does NOT also have to set LOCAL_LLM_BASE_URL.
    """
    served = _served_local_base_url(model)
    if served:
        return served
    if _local_llm_ready():
        root = str(getattr(get_settings(), "local_llm_base_url", "") or "").rstrip("/")
        if root.endswith("/v1") or root.endswith("/chat/completions"):
            return root
        return f"{root}/v1" if root else ""
    return ""


def _local_runtime_model_name(model: str) -> str:
    """Model name to send to the local OpenAI-compatible runtime.

    A served Foundry catalog id (`qwen2.5-14b`) must be addressed on Ollama by its
    runtime tag (`qwen2.5:14b`). Prefer the served record's runtime name, then the
    catalog→tag map, else the id as-is.
    """
    try:
        from aethos_core.workspace_suite.model_foundry import ollama_tag_for, served_model_runtime_name

        runtime = served_model_runtime_name(model)
        if runtime:
            return runtime
        tag = ollama_tag_for(model)
        if tag:
            return tag
    except Exception:
        pass
    return model


def local_tool_loop_diagnostics(model: str) -> dict[str, Any]:
    """Resolved local tool-loop wiring for a model (for startup/diag logging)."""
    base_url = local_tool_loop_base_url(model)
    return {
        "model": model,
        "base_url": base_url,
        "runtime_model": _local_runtime_model_name(model) if base_url else "",
        "capable": bool(base_url),
    }


def _anthropic_tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Anthropic tool schemas → OpenAI function-tool schemas."""
    converted: list[dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name") or "")
        if not name:
            continue
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": str(tool.get("description") or ""),
                    "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
        )
    return converted


def _run_openai_compatible_tool_loop(
    *,
    url: str,
    headers: dict[str, str],
    provider: str,
    model: str,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    max_iterations: int = 8,
    max_tool_streak: int = 20,
) -> ToolLoopResult | None:
    """Agent tool loop on any OpenAI-compatible runtime (Ollama, OpenRouter, …).

    Returns None when the runtime can't run a tool loop (a hard error on the first
    call) so the caller can fall back *and surface it* — never a silent swap.
    """
    import json as _json

    from aethos_core.agents.runtime.tool_call_repair import (
        allowed_names_from_tools,
        classify_loop_outcome,
        parse_tool_arguments,
        repair_result_text,
        validate_tool_call,
        ToolCallRepairBudget,
    )

    openai_tools = _anthropic_tools_to_openai(tools)
    allowed_tool_names = allowed_names_from_tools(tools)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]
    tool_calls = 0
    streak = 0
    agg_in = 0
    agg_out = 0
    repair_budget = ToolCallRepairBudget()

    for iteration in range(1, max_iterations + 1):
        payload: dict[str, Any] = {"model": model, "messages": messages}
        if openai_tools:
            payload["tools"] = openai_tools
            payload["tool_choice"] = "auto"
        from time import perf_counter as _pc

        _model_t0 = _pc()
        try:
            response = _http_request_with_transient_retry("POST", url, json=payload, headers=headers)
            data = response.json()
        except httpx.HTTPError as exc:
            _record_model_ms(int((_pc() - _model_t0) * 1000))
            label = _provider_display_label(provider)
            err_text = format_provider_http_error(exc, provider_label=label, model=model, provider=provider)
            if iteration == 1:
                return ToolLoopResult(
                    text=err_text,
                    provider=provider,
                    model=model,
                    used_llm=False,
                    loop_outcome="error_degraded",
                )
            return ToolLoopResult(
                text=f"{provider} runtime tool loop ended early after a provider error.",
                provider=provider,
                model=model,
                used_llm=True,
                tool_calls=tool_calls,
                iterations=iteration,
                input_tokens=agg_in,
                output_tokens=agg_out,
            )

        _record_model_ms(int((_pc() - _model_t0) * 1000))
        in_tok, out_tok = _openai_usage(data)
        agg_in += in_tok
        agg_out += out_tok
        choices = data.get("choices") if isinstance(data, dict) else None
        message = (choices[0].get("message") if isinstance(choices, list) and choices else {}) or {}
        pending = message.get("tool_calls") if isinstance(message.get("tool_calls"), list) else []

        if pending:
            streak += len(pending)
            if streak > max_tool_streak:
                return ToolLoopResult(
                    text=f"{provider} agent runtime stopped: tool loop limit reached.",
                    provider=provider,
                    model=model,
                    used_llm=True,
                    tool_calls=tool_calls,
                    iterations=iteration,
                    input_tokens=agg_in,
                    output_tokens=agg_out,
                )
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": pending,
                }
            )
            for call in pending:
                fn = call.get("function") if isinstance(call, dict) else {}
                name = str((fn or {}).get("name") or "")
                raw_args = (fn or {}).get("arguments")
                args, parse_hint = parse_tool_arguments(raw_args)
                repair_hint = parse_hint or validate_tool_call(
                    name, dict(args), allowed_names=allowed_tool_names
                )
                if repair_hint:
                    if repair_budget.allow_repair():
                        repair_budget.record_repair()
                        result_text = repair_result_text(repair_hint, exhausted=repair_budget.exhausted)
                    else:
                        result_text = repair_result_text(
                            "Too many malformed tool calls — answer in plain text.",
                            exhausted=True,
                        )
                else:
                    result_text = _truncate_tool_result(tool_executor(name, dict(args)))
                tool_calls += 1
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": str(call.get("id") or name),
                        "content": result_text,
                    }
                )
            continue

        final_text = str(message.get("content") or "").strip() or f"{provider} agent runtime returned an empty response."
        return ToolLoopResult(
            text=final_text,
            provider=provider,
            model=model,
            used_llm=True,
            tool_calls=tool_calls,
            iterations=iteration,
            input_tokens=agg_in,
            output_tokens=agg_out,
            loop_outcome=classify_loop_outcome(final_text, tool_calls=tool_calls),
        )

    return ToolLoopResult(
        text=f"{provider} agent runtime stopped: maximum iterations reached.",
        provider=provider,
        model=model,
        used_llm=True,
        tool_calls=tool_calls,
        iterations=max_iterations,
        input_tokens=agg_in,
        output_tokens=agg_out,
        loop_outcome=classify_loop_outcome(
            f"{provider} agent runtime stopped: maximum iterations reached.",
            tool_calls=tool_calls,
            degraded=True,
        ),
    )


def run_local_tool_loop(
    *,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    model: str,
    max_iterations: int = 8,
    max_tool_streak: int = 20,
) -> ToolLoopResult | None:
    """Agent tool loop on a local OpenAI-compatible runtime (Ollama /v1)."""
    base_url = local_tool_loop_base_url(model)
    if not base_url:
        _log.info("local_tool_loop unavailable model=%s — no served endpoint or LOCAL_LLM_BASE_URL", model)
        return None
    runtime_model = _local_runtime_model_name(model)
    _log.info(
        "local_tool_loop base_url=%s selected_model=%s runtime_model=%s", base_url, model, runtime_model
    )
    api_key = str(getattr(get_settings(), "local_llm_api_key", "") or "").strip()
    url = base_url if base_url.endswith("/chat/completions") else f"{base_url}/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return _run_openai_compatible_tool_loop(
        url=url,
        headers=headers,
        provider="local",
        model=runtime_model,
        system=system,
        user_message=user_message,
        tools=tools,
        tool_executor=tool_executor,
        max_iterations=max_iterations,
        max_tool_streak=max_tool_streak,
    )


def run_openrouter_tool_loop(
    *,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    model: str,
    max_iterations: int = 8,
    max_tool_streak: int = 20,
) -> ToolLoopResult | None:
    """Agent tool loop on OpenRouter's OpenAI-compatible tools API.

    Honors an OpenRouter selection for tools instead of swapping to Anthropic.
    """
    from aethos_core.llm.model_providers import resolve_model_provider_key

    api_key = _resolved_openrouter_api_key()
    if not api_key:
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return _run_openai_compatible_tool_loop(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        provider="openrouter",
        model=model,
        system=system,
        user_message=user_message,
        tools=tools,
        tool_executor=tool_executor,
        max_iterations=max_iterations,
        max_tool_streak=max_tool_streak,
    )


def _registry_provider_complete(user_text: str, *, provider: str, model: str) -> ProviderResult:
    """§2 — single-shot completion on any OpenAI-compatible model provider.

    Key resolves from .env or the MC vault; never echoed. Reuses the OpenAI chat
    schema that OpenAI, Gemini (compat), Mistral, Groq, xAI, DeepSeek, Cohere,
    Together, Fireworks and Perplexity all speak.
    """
    from aethos_core.aethos_identity.identity_contract_loader import build_identity_system_persona_block
    from aethos_core.identity.operational_voice import LLM_SYSTEM_PERSONA
    from aethos_core.llm.model_providers import model_provider_spec, resolve_model_provider_key

    spec = model_provider_spec(provider)
    if spec is None:
        return ProviderResult(text=f"Provider {provider} not configured.", provider=provider, model=model, used_llm=False)
    if not spec.openai_compatible:
        if provider == "anthropic":
            key = resolve_model_provider_key(provider)
            if key:
                return _anthropic_complete(user_text, key, model)
        return ProviderResult(
            text=f"{spec.label} is not available through the OpenAI-compatible path.",
            provider=provider,
            model=model,
            used_llm=False,
        )
    api_key = resolve_model_provider_key(provider)
    if not api_key:
        return ProviderResult(
            text=f"{spec.label} not configured. Add a key in Mission Control → Advanced settings → Credentials.",
            provider=provider,
            model=model,
            used_llm=False,
        )
    identity_block = build_identity_system_persona_block()
    system = f"{LLM_SYSTEM_PERSONA}\n\n{identity_block}" if identity_block else LLM_SYSTEM_PERSONA
    url = f"{spec.base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model or str(getattr(get_settings(), spec.model_attr, "") or ""),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = _http_request_with_transient_retry("POST", url, json=payload, headers=headers)
        data = response.json()
    except httpx.HTTPStatusError as exc:
        # §4 — honest classification: 402/429 mean the key worked but the account
        # lacks credits/quota (user-side), distinct from an AethOS config error.
        from aethos_core.llm.model_error_classifier import classify_status

        status = exc.response.status_code
        verdict = classify_status(status, provider_label=spec.label)
        return ProviderResult(
            text=f"{verdict['message']} [HTTP {status}]",
            provider=provider,
            model=model,
            used_llm=False,
        )
    except httpx.HTTPError as exc:
        return ProviderResult(
            text=format_provider_http_error(exc, provider_label=spec.label, model=model, provider=provider),
            provider=provider,
            model=model,
            used_llm=False,
        )
    choices = data.get("choices") if isinstance(data, dict) else []
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else {}
        text = str((message or {}).get("content") or "").strip()
        if text:
            in_tok, out_tok = _openai_usage(data)
            return ProviderResult(
                text=text, provider=provider, model=model, used_llm=True, input_tokens=in_tok, output_tokens=out_tok
            )
    return ProviderResult(text=f"{spec.label} returned an empty response.", provider=provider, model=model, used_llm=False)


def run_registry_provider_tool_loop(
    *,
    provider: str,
    system: str,
    user_message: str,
    tools: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], str],
    model: str,
    max_iterations: int = 8,
    max_tool_streak: int = 20,
) -> ToolLoopResult | None:
    """§2 — agent tool loop on an OpenAI-compatible model provider (key from vault/.env).

    Returns None when the key is missing or the runtime can't run tools, so the
    caller falls back honestly (never a silent swap).
    """
    from aethos_core.llm.model_providers import model_provider_spec, resolve_model_provider_key

    spec = model_provider_spec(provider)
    if spec is None or not spec.tool_capable:
        return None
    # Defense: the OpenAI-compatible tool loop needs a real https base_url. A non-compatible
    # provider (e.g. Anthropic) or one with an empty base_url must fall back honestly instead
    # of POSTing to a relative "/chat/completions" (which raises UnsupportedProtocol).
    if not getattr(spec, "openai_compatible", False) or not str(spec.base_url or "").strip():
        return None
    api_key = resolve_model_provider_key(provider)
    if not api_key:
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return _run_openai_compatible_tool_loop(
        url=f"{spec.base_url.rstrip('/')}/chat/completions",
        headers=headers,
        provider=provider,
        model=model,
        system=system,
        user_message=user_message,
        tools=tools,
        tool_executor=tool_executor,
        max_iterations=max_iterations,
        max_tool_streak=max_tool_streak,
    )


def _openrouter_complete(user_text: str, api_key: str, model: str) -> ProviderResult:
    from aethos_core.aethos_identity.identity_contract_loader import build_identity_system_persona_block
    from aethos_core.identity.operational_voice import LLM_SYSTEM_PERSONA

    identity_block = build_identity_system_persona_block()
    system = LLM_SYSTEM_PERSONA
    if identity_block:
        system = f"{LLM_SYSTEM_PERSONA}\n\n{identity_block}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = _http_request_with_transient_retry(
            "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        data = response.json()
    except httpx.HTTPError as exc:
        return ProviderResult(
            text=format_provider_http_error(exc, provider_label="OpenRouter", model=model, provider="openrouter"),
            provider="openrouter",
            model=model,
            used_llm=False,
        )
    choices = data.get("choices") if isinstance(data, dict) else []
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") if isinstance(choices[0], dict) else {}
        text = str((message or {}).get("content") or "").strip()
        if text:
            in_tok, out_tok = _openai_usage(data)
            return ProviderResult(
                text=text, provider="openrouter", model=model, used_llm=True, input_tokens=in_tok, output_tokens=out_tok
            )
    return ProviderResult(text="OpenRouter returned an empty response.", provider="openrouter", model=model, used_llm=False)
