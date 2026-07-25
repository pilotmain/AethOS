# SPDX-License-Identifier: Apache-2.0
"""§2 — multi-provider model registry (bring-your-own-model).

Single source of truth for the model-API providers AethOS can talk to. Catalog,
router, completion, and the Connections vault wiring all read from here so adding
a provider is one entry.

Keys resolve from .env first (the operator's own key) and then the MC vault (a
per-user key stored encrypted via Connections) — never echoed, never logged.

Most providers expose an OpenAI-compatible ``/chat/completions`` endpoint (incl.
Google Gemini via its OpenAI-compat path and Cohere via ``/compatibility``), so a
single client drives them. Anthropic uses its native Messages API (handled in
``provider.completion``); ``local``/``openrouter`` keep their existing paths.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import httpx

from aethos_core.config import get_settings


@dataclass(frozen=True)
class ModelProviderSpec:
    id: str
    label: str
    key_attr: str  # settings attribute holding the .env key
    model_attr: str  # settings attribute holding the default model
    base_url: str  # OpenAI-compatible chat-completions base (…/v1), or "" if native
    models: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    openai_compatible: bool = True
    tool_capable: bool = True
    api_key_url: str = ""


# Flagship model shortlists per provider (id, label). Kept intentionally small so
# the picker stays readable; the .env/default model is always included too.
ANTHROPIC_MODELS: tuple[tuple[str, str], ...] = (
    ("claude-opus-4-6", "Claude Opus 4.6"),
    ("claude-sonnet-4-6", "Claude Sonnet 4.6"),
    ("claude-haiku-4-5", "Claude Haiku 4.5"),
    ("claude-sonnet-4-20250514", "Claude Sonnet 4 (20250514)"),
)

MODEL_PROVIDERS: dict[str, ModelProviderSpec] = {
    "anthropic": ModelProviderSpec(
        id="anthropic",
        label="Anthropic",
        key_attr="anthropic_api_key",
        model_attr="anthropic_model",
        base_url="",
        models=ANTHROPIC_MODELS,
        openai_compatible=False,
        tool_capable=True,
        api_key_url="https://console.anthropic.com/settings/keys",
    ),
    "openai": ModelProviderSpec(
        id="openai",
        label="OpenAI",
        key_attr="openai_api_key",
        model_attr="openai_model",
        base_url="https://api.openai.com/v1",
        models=(
            ("gpt-4o", "OpenAI · GPT-4o"),
            ("gpt-4o-mini", "OpenAI · GPT-4o mini"),
            ("o3-mini", "OpenAI · o3-mini"),
        ),
        api_key_url="https://platform.openai.com/api-keys",
    ),
    "gemini": ModelProviderSpec(
        id="gemini",
        label="Google Gemini",
        key_attr="gemini_api_key",
        model_attr="gemini_model",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        models=(
            ("gemini-2.0-flash", "Gemini · 2.0 Flash"),
            ("gemini-1.5-pro", "Gemini · 1.5 Pro"),
        ),
        api_key_url="https://aistudio.google.com/app/apikey",
    ),
    "mistral": ModelProviderSpec(
        id="mistral",
        label="Mistral",
        key_attr="mistral_api_key",
        model_attr="mistral_model",
        base_url="https://api.mistral.ai/v1",
        models=(
            ("mistral-large-latest", "Mistral · Large"),
            ("mistral-small-latest", "Mistral · Small"),
        ),
        api_key_url="https://console.mistral.ai/api-keys",
    ),
    "groq": ModelProviderSpec(
        id="groq",
        label="Groq",
        key_attr="groq_api_key",
        model_attr="groq_model",
        base_url="https://api.groq.com/openai/v1",
        models=(
            ("llama-3.3-70b-versatile", "Groq · Llama 3.3 70B"),
            ("llama-3.1-8b-instant", "Groq · Llama 3.1 8B"),
        ),
        api_key_url="https://console.groq.com/keys",
    ),
    "xai": ModelProviderSpec(
        id="xai",
        label="xAI (Grok)",
        key_attr="xai_api_key",
        model_attr="xai_model",
        base_url="https://api.x.ai/v1",
        models=(
            ("grok-2-latest", "xAI · Grok 2"),
            ("grok-2-mini", "xAI · Grok 2 mini"),
        ),
        api_key_url="https://console.x.ai",
    ),
    "deepseek": ModelProviderSpec(
        id="deepseek",
        label="DeepSeek",
        key_attr="deepseek_api_key",
        model_attr="deepseek_model",
        base_url="https://api.deepseek.com/v1",
        models=(
            ("deepseek-chat", "DeepSeek · Chat"),
            ("deepseek-reasoner", "DeepSeek · Reasoner"),
        ),
        api_key_url="https://platform.deepseek.com/api_keys",
    ),
    "cohere": ModelProviderSpec(
        id="cohere",
        label="Cohere",
        key_attr="cohere_api_key",
        model_attr="cohere_model",
        base_url="https://api.cohere.ai/compatibility/v1",
        models=(
            ("command-r-plus", "Cohere · Command R+"),
            ("command-r", "Cohere · Command R"),
        ),
        api_key_url="https://dashboard.cohere.com/api-keys",
    ),
    "together": ModelProviderSpec(
        id="together",
        label="Together",
        key_attr="together_api_key",
        model_attr="together_model",
        base_url="https://api.together.xyz/v1",
        models=(
            ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Together · Llama 3.3 70B"),
            ("Qwen/Qwen2.5-72B-Instruct-Turbo", "Together · Qwen2.5 72B"),
        ),
        api_key_url="https://api.together.xyz/settings/api-keys",
    ),
    "fireworks": ModelProviderSpec(
        id="fireworks",
        label="Fireworks",
        key_attr="fireworks_api_key",
        model_attr="fireworks_model",
        base_url="https://api.fireworks.ai/inference/v1",
        models=(
            ("accounts/fireworks/models/llama-v3p3-70b-instruct", "Fireworks · Llama 3.3 70B"),
            ("accounts/fireworks/models/qwen2p5-72b-instruct", "Fireworks · Qwen2.5 72B"),
        ),
        api_key_url="https://fireworks.ai/account/api-keys",
    ),
    "perplexity": ModelProviderSpec(
        id="perplexity",
        label="Perplexity",
        key_attr="perplexity_api_key",
        model_attr="perplexity_model",
        base_url="https://api.perplexity.ai",
        models=(
            ("sonar", "Perplexity · Sonar"),
            ("sonar-pro", "Perplexity · Sonar Pro"),
        ),
        api_key_url="https://www.perplexity.ai/settings/api",
    ),
    # OpenRouter is OpenAI-compatible and reaches many providers' models via one key.
    # Registering it makes key resolution vault-aware (resolve_model_provider_key) so the
    # selection card, model picker, and arbiter all see a vault-stored key. The dedicated
    # OpenRouter completion path (provider == "openrouter") still takes precedence in
    # provider/completion.py, so chat routing is unchanged. Live catalog is filtered to
    # major families in fetch_live_models_from_api; no static shortlist needed here.
    "openrouter": ModelProviderSpec(
        id="openrouter",
        label="OpenRouter",
        key_attr="openrouter_api_key",
        model_attr="openrouter_model",
        base_url="https://openrouter.ai/api/v1",
        models=(),
        openai_compatible=True,
        tool_capable=True,
        api_key_url="https://openrouter.ai/keys",
    ),
}


def model_provider_spec(provider: str) -> ModelProviderSpec | None:
    return MODEL_PROVIDERS.get((provider or "").strip().lower())


def is_registry_provider(provider: str) -> bool:
    return (provider or "").strip().lower() in MODEL_PROVIDERS


def resolve_model_provider_key(provider: str) -> str:
    """Resolve a provider's API key for the *current tenant*.

    Single-tenant (default): ``.env`` settings first, then the MC vault — unchanged.

    Multi-tenant: the deployment ``.env`` key is the *operator's* key, so only the
    operator/default tenant may use it. Every other tenant resolves strictly from
    their own vault credentials — no cross-tenant fallback — so each tenant's model
    calls bill their own account (Phase 2 acceptance). The vault itself is already
    scoped to the current tenant.

    Returns "" when nothing is configured for the tenant. Never logs the secret.
    """
    spec = model_provider_spec(provider)
    if spec is None:
        return ""
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    s = get_settings()
    tenant = get_current_tenant() if s.multi_tenant_enabled else DEFAULT_TENANT
    if tenant == DEFAULT_TENANT:
        env_key = str(getattr(s, spec.key_attr, "") or "").strip()
        if env_key:
            return env_key
    return _vault_key(spec.id)


def _vault_key(provider: str) -> str:
    """Best decryptable vault secret for ``provider`` — newest validated first."""
    try:
        from aethos_core.connections.credential_state import resolve_credential_state
        from aethos_core.connections.validation_status import (
            EXPIRED,
            INVALID,
            INSUFFICIENT_SCOPE,
            PERSISTENCE_FAILED,
            SECRET_MISSING,
            VALIDATED,
        )
        from aethos_core.security.credential_vault import get_credential_vault

        vault = get_credential_vault()
        bad_statuses = frozenset(
            {INVALID, EXPIRED, PERSISTENCE_FAILED, SECRET_MISSING, INSUFFICIENT_SCOPE}
        )
        fallback_token = ""
        for rec in vault.list_credentials(provider=provider):
            if getattr(rec, "revoked", False):
                continue
            state = resolve_credential_state(rec.credential_id)
            if not state.get("decryptable"):
                continue
            status = str(state.get("validation_status") or rec.validation_status or "")
            if status in bad_statuses:
                continue
            secret = vault.retrieve_secret(rec.credential_id) or {}
            token = str(secret.get("token") or "").strip()
            if not token:
                continue
            if status == VALIDATED:
                return token
            if not fallback_token:
                fallback_token = token
        return fallback_token
    except Exception:  # noqa: BLE001 — key resolution must never break a turn.
        return ""
    return ""


def model_provider_configured(provider: str) -> bool:
    return bool(resolve_model_provider_key(provider))


def anthropic_configured() -> bool:
    """Anthropic API key from .env (default tenant) or the per-tenant vault."""
    return model_provider_configured("anthropic")


def resolve_anthropic_api_key() -> str:
    return resolve_model_provider_key("anthropic")


def configured_model_providers() -> list[ModelProviderSpec]:
    return [spec for spec in MODEL_PROVIDERS.values() if model_provider_configured(spec.id)]


_LIVE_MODEL_CACHE: dict[tuple[str, str], dict[str, object]] = {}
_LIVE_CACHE_LOCK = threading.Lock()
_LIVE_CACHE_TTL_SEC = 3600
_LIVE_MODEL_CAP = 80


def _live_cache_tenant() -> str:
    try:
        from aethos_core.tenancy import get_current_tenant

        return str(get_current_tenant() or "default")
    except Exception:  # noqa: BLE001
        return "default"


def _get_live_cache(provider: str) -> list[tuple[str, str]] | None:
    key = (_live_cache_tenant(), (provider or "").strip().lower())
    with _LIVE_CACHE_LOCK:
        entry = _LIVE_MODEL_CACHE.get(key)
        if not entry:
            return None
        fetched_at = float(entry.get("fetched_at") or 0)
        if time.time() - fetched_at > _LIVE_CACHE_TTL_SEC:
            _LIVE_MODEL_CACHE.pop(key, None)
            return None
        rows = entry.get("rows")
        if isinstance(rows, list):
            return list(rows)
    return None


def _set_live_cache(provider: str, rows: list[tuple[str, str]]) -> None:
    key = (_live_cache_tenant(), (provider or "").strip().lower())
    with _LIVE_CACHE_LOCK:
        _LIVE_MODEL_CACHE[key] = {"fetched_at": time.time(), "rows": rows}


def clear_live_model_cache_for_tests() -> None:
    with _LIVE_CACHE_LOCK:
        _LIVE_MODEL_CACHE.clear()


def _parse_openai_compatible_models(data: dict[str, object]) -> list[tuple[str, str]]:
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    rows: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        mid = str(item.get("id") or "").strip()
        if not mid:
            continue
        name = str(item.get("name") or item.get("display_name") or mid)
        rows.append((mid, name))
    return sorted(rows, key=lambda x: x[0])


def _cap_live_rows(rows: list[tuple[str, str]], *, label_prefix: str) -> list[tuple[str, str]]:
    capped = rows[:_LIVE_MODEL_CAP]
    out: list[tuple[str, str]] = []
    for mid, lbl in capped:
        if lbl == mid or not lbl:
            lbl = f"{label_prefix} · {mid}"
        elif not lbl.startswith(label_prefix):
            lbl = f"{label_prefix} · {lbl}"
        out.append((mid, lbl))
    return out


def fetch_live_models_from_api(provider: str) -> list[tuple[str, str]]:
    """Fetch model ids from the provider API. Returns empty on failure."""
    prov = (provider or "").strip().lower()
    spec = model_provider_spec(prov)
    if spec is None or not model_provider_configured(prov):
        return []
    api_key = resolve_model_provider_key(prov)
    if not api_key:
        return []
    try:
        if prov == "anthropic":
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
            if resp.status_code >= 400:
                return []
            data = resp.json()
            rows = _parse_openai_compatible_models(data if isinstance(data, dict) else {})
            return _cap_live_rows(rows, label_prefix=spec.label)
        if prov == "openrouter":
            with httpx.Client(timeout=25.0) as client:
                resp = client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            if resp.status_code >= 400:
                return []
            data = resp.json()
            all_rows = _parse_openai_compatible_models(data if isinstance(data, dict) else {})
            # Prefer major chat routes — full OpenRouter catalog is enormous.
            preferred = [
                r for r in all_rows
                if any(
                    r[0].startswith(p)
                    for p in ("anthropic/", "openai/", "google/", "meta-llama/", "mistralai/")
                )
            ]
            rows = preferred or all_rows
            return _cap_live_rows(rows, label_prefix="OpenRouter")
        if spec.openai_compatible and spec.base_url:
            url = f"{spec.base_url.rstrip('/')}/models"
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(url, headers={"Authorization": f"Bearer {api_key}"})
            if resp.status_code >= 400:
                return []
            data = resp.json()
            rows = _parse_openai_compatible_models(data if isinstance(data, dict) else {})
            return _cap_live_rows(rows, label_prefix=spec.label)
    except httpx.HTTPError:
        return []
    return []


def refresh_live_models_for_provider(provider: str, *, force: bool = False) -> list[tuple[str, str]]:
    """Fetch and cache live models for a provider (per tenant)."""
    prov = (provider or "").strip().lower()
    if not force:
        cached = _get_live_cache(prov)
        if cached is not None:
            return cached
    rows = fetch_live_models_from_api(prov)
    if rows:
        _set_live_cache(prov, rows)
    return rows


def live_model_rows(provider: str) -> tuple[list[tuple[str, str]], str]:
    """Return (rows, source) where source is ``live`` or ``fallback``."""
    prov = (provider or "").strip().lower()
    cached = _get_live_cache(prov)
    if cached is not None:
        return cached, "live"
    rows = refresh_live_models_for_provider(prov)
    if rows:
        return rows, "live"
    spec = model_provider_spec(prov)
    if spec is None:
        return [], "fallback"
    return list(spec.models), "fallback"


def supported_model_ids_for_provider(provider: str) -> list[str]:
    rows, _ = live_model_rows(provider)
    spec = model_provider_spec(provider)
    ids = {mid for mid, _ in rows}
    if spec is not None:
        default = str(getattr(get_settings(), spec.model_attr, "") or "").strip()
        if default:
            ids.add(default)
        if not ids:
            ids = {mid for mid, _ in spec.models}
    return sorted(ids)


def model_id_supported_by_provider(provider: str, model_id: str) -> bool:
    """True when the model id is in the live or fallback list for this provider."""
    mid = (model_id or "").strip()
    if not mid:
        return False
    spec = model_provider_spec(provider)
    if spec is None:
        return False
    default = str(getattr(get_settings(), spec.model_attr, "") or "").strip()
    if mid == default:
        return True
    return mid in set(supported_model_ids_for_provider(provider))


def model_provider_rows(spec: ModelProviderSpec) -> list[tuple[str, str]]:
    """(model_id, label) rows — live API list when available, else registry shortlist."""
    default_model = str(getattr(get_settings(), spec.model_attr, "") or "").strip()
    live_rows, source = live_model_rows(spec.id)
    base_rows = live_rows if live_rows else list(spec.models)
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    if default_model:
        # No "(live)" tag — it's internal jargon, not user-meaningful in a model picker.
        rows.append((default_model, f"{spec.label} · {default_model}"))
        seen.add(default_model)
    for model, label in base_rows:
        if model in seen:
            continue
        seen.add(model)
        rows.append((model, label))
    return rows
