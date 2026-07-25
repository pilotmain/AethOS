# SPDX-License-Identifier: Apache-2.0
"""Operator-visible LLM catalog — model picker source for chat + Compare."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.llm.model_providers import ANTHROPIC_MODELS, anthropic_configured

DEFAULT_CATALOG_ID = "default"

OPENROUTER_MODELS: tuple[tuple[str, str], ...] = (
    ("anthropic/claude-opus-4", "OpenRouter · Claude Opus 4"),
    ("anthropic/claude-sonnet-4", "OpenRouter · Claude Sonnet 4"),
    ("anthropic/claude-3.5-haiku", "OpenRouter · Claude 3.5 Haiku"),
    ("openai/gpt-4.1-mini", "OpenRouter · GPT-4.1 Mini"),
)


def _anthropic_configured() -> bool:
    s = get_settings()
    if not s.use_real_llm:
        return False
    return anthropic_configured()


def _openrouter_configured() -> bool:
    s = get_settings()
    return bool(str(getattr(s, "openrouter_api_key", "") or "").strip())


def _local_configured() -> bool:
    s = get_settings()
    if not getattr(s, "local_llm_enabled", False):
        return False
    return bool(str(getattr(s, "local_llm_base_url", "") or "").strip())


def _local_model_rows() -> list[tuple[str, str]]:
    s = get_settings()
    rows: list[tuple[str, str]] = []
    default_model = str(getattr(s, "local_llm_default_model", "") or "llama3.2").strip() or "llama3.2"
    rows.append((default_model, f"Local · {default_model}"))
    extra = str(getattr(s, "local_llm_models", "") or "").strip()
    if extra:
        for part in extra.split(","):
            model = part.strip()
            if model and model != default_model:
                rows.append((model, f"Local · {model}"))
    return rows


def _served_foundry_rows() -> list[tuple[str, str, str]]:
    """(model_id, label, endpoint) for models served via the governed Model Foundry.

    These become ``configured`` ``local:`` catalog entries so an approved + served
    local model appears in the chat + Compare picker. Defensive: never raises.
    """
    try:
        from aethos_core.workspace_suite.model_foundry import list_served_models

        rows: list[tuple[str, str, str]] = []
        for record in list_served_models():
            model_id = str(record.get("model_id") or "").strip()
            if not model_id:
                continue
            label = str(record.get("label") or model_id)
            port = int(record.get("port") or 11434)
            endpoint = str(record.get("endpoint") or "").strip() or f"http://127.0.0.1:{port}"
            rows.append((model_id, f"{label} (local)", endpoint))
        return rows
    except Exception:
        return []


def _agent_tool_capable(provider: str, configured: bool) -> bool:
    """Whether this model can drive the agent tool loop (used to gate the picker).

    Local models are tool-capable only when LOCAL_TOOL_LOOP_ENABLED is on (they then
    run tools over the OpenAI-compatible API, with an honest cloud fallback). With the
    flag off, the picker disables them in agent mode rather than swapping silently.
    """
    if not configured:
        return False
    if provider == "local":
        return bool(getattr(get_settings(), "local_tool_loop_enabled", True))
    if provider in ("anthropic", "openrouter"):
        return True
    # §2 — registry providers drive the agent loop over their OpenAI-compatible
    # tools API; honest fallback covers any that can't.
    from aethos_core.llm.model_providers import model_provider_spec

    spec = model_provider_spec(provider)
    if spec is not None:
        return spec.tool_capable
    return False


def _entry(
    *,
    catalog_id: str,
    provider: str,
    model: str,
    label: str,
    configured: bool,
    model_source: str | None = None,
) -> dict[str, Any]:
    row = {
        "id": catalog_id,
        "provider": provider,
        "model": model,
        "label": label,
        "configured": configured,
        "agent_tool_capable": _agent_tool_capable(provider, configured),
    }
    if model_source:
        row["model_source"] = model_source
    return row


def catalog_entry_for_id(catalog_id: str) -> dict[str, Any] | None:
    for row in list_available_models(include_unconfigured=True):
        if row["id"] == catalog_id:
            return row
    return _synthetic_catalog_entry(catalog_id)


def _synthetic_catalog_entry(catalog_id: str) -> dict[str, Any] | None:
    """Build a catalog row for ``provider:model`` when the provider key is present."""
    raw = (catalog_id or "").strip()
    if ":" not in raw:
        return None
    provider, model = raw.split(":", 1)
    provider = provider.strip().lower()
    model = model.strip()
    if not provider or not model:
        return None
    from aethos_core.llm.model_providers import (
        live_model_rows,
        model_id_supported_by_provider,
        model_provider_configured,
        model_provider_spec,
    )

    spec = model_provider_spec(provider)
    if spec is None:
        return None
    if not model_id_supported_by_provider(provider, model):
        return None
    default_model = str(getattr(get_settings(), spec.model_attr, "") or "").strip()
    live_rows, source = live_model_rows(provider)
    label = model
    for mid, lbl in spec.models:
        if mid == model:
            label = lbl
            break
    else:
        for mid, lbl in live_rows:
            if mid == model:
                label = lbl
                break
        if model == default_model:
            label = f"{spec.label} · {model}"
    configured = model_provider_configured(provider)
    source_tag = "live" if source == "live" and model in {m for m, _ in live_rows} else None
    return _entry(
        catalog_id=raw,
        provider=provider,
        model=model,
        label=label,
        configured=configured,
        model_source=source_tag,
    )


def default_catalog_entry(*, provider: str | None = None) -> dict[str, Any] | None:
    for row in list_available_models(include_unconfigured=False):
        if provider is None or row["provider"] == provider:
            if row["id"] != DEFAULT_CATALOG_ID:
                return row
    return None


def env_default_catalog_entry() -> dict[str, Any]:
    s = get_settings()
    active = (s.active_provider or "none").strip().lower()
    if active == "openrouter" and _openrouter_configured():
        model = str(getattr(s, "openrouter_model", "openrouter/auto") or "openrouter/auto")
        return _entry(
            catalog_id=f"openrouter:{model}",
            provider="openrouter",
            model=model,
            label=f"Default (.env) · {model}",
            configured=True,
        )
    if _local_configured() and active == "local":
        model = str(getattr(s, "local_llm_default_model", "") or "llama3.2")
        return _entry(
            catalog_id=f"local:{model}",
            provider="local",
            model=model,
            label=f"Default (.env) · {model}",
            configured=True,
        )
    if _anthropic_configured():
        model = str(s.anthropic_model or "").strip()
        if not model:
            from aethos_core.llm.model_providers import model_provider_spec

            spec = model_provider_spec("anthropic")
            if spec is not None:
                rows = model_provider_rows_for_catalog(spec)
                if rows:
                    model = rows[0][0]
        if model:
            return _entry(
                catalog_id=f"anthropic:{model}",
                provider="anthropic",
                model=model,
                label=f"Default · {model}",
                configured=True,
            )
    # First configured registry provider (vault or .env for default tenant).
    from aethos_core.llm.model_providers import configured_model_providers
    from aethos_core.llm.model_selection import enabled_models_for_provider

    for spec in configured_model_providers():
        rows = enabled_models_for_provider(spec)
        if not rows:
            continue
        model_id, label = rows[0]
        return _entry(
            catalog_id=f"{spec.id}:{model_id}",
            provider=spec.id,
            model=model_id,
            label=f"Default · {label}",
            configured=True,
        )
    if _openrouter_configured():
        model = str(getattr(s, "openrouter_model", "openrouter/auto") or "openrouter/auto")
        return _entry(
            catalog_id=f"openrouter:{model}",
            provider="openrouter",
            model=model,
            label=f"Default · {model}",
            configured=True,
        )
    if _local_configured():
        model = str(getattr(s, "local_llm_default_model", "") or "llama3.2")
        return _entry(
            catalog_id=f"local:{model}",
            provider="local",
            model=model,
            label=f"Default · {model}",
            configured=True,
        )
    return _entry(
        catalog_id=DEFAULT_CATALOG_ID,
        provider="template",
        model="template",
        label="Add a provider API key in Mission Control → Advanced settings → Credentials",
        configured=False,
    )


def model_provider_rows_for_catalog(spec: Any) -> list[tuple[str, str]]:
    from aethos_core.llm.model_providers import model_provider_rows

    return model_provider_rows(spec)


def list_available_models(*, include_unconfigured: bool = False) -> list[dict[str, Any]]:
    """Models the operator can pick in agent mode."""
    default = env_default_catalog_entry()
    # §4 — show what "Default (.env)" actually resolves to, so the picker never
    # hides which model a default selection will run.
    default_model = str(default["model"])
    default_label = (
        f"Default · {default_model}" if default.get("configured") else str(default["label"])
    )
    rows: list[dict[str, Any]] = [
        _entry(
            catalog_id=DEFAULT_CATALOG_ID,
            provider=str(default["provider"]),
            model=default_model,
            label=default_label,
            configured=bool(default.get("configured")),
        )
    ]

    # OpenRouter is now a registry provider — the configured-providers loop below lists
    # its (vault-keyed, live) models, so it no longer needs a settings-only special case
    # here (which missed vault-stored keys and used a static shortlist).

    if _anthropic_configured():
        from aethos_core.llm.model_providers import live_model_rows

        env_model = str(get_settings().anthropic_model or "").strip()
        live_rows, source = live_model_rows("anthropic")
        catalog_models = live_rows if live_rows else list(ANTHROPIC_MODELS)
        catalog_ids = {m for m, _ in catalog_models}
        if env_model and env_model not in catalog_ids:
            rows.append(
                _entry(
                    catalog_id=f"anthropic:{env_model}",
                    provider="anthropic",
                    model=env_model,
                    label=f"Anthropic · {env_model} (.env)",
                    configured=True,
                    model_source=source if source == "live" else None,
                )
            )
        for model, label in catalog_models:
            rows.append(
                _entry(
                    catalog_id=f"anthropic:{model}",
                    provider="anthropic",
                    model=model,
                    label=label,
                    configured=True,
                    model_source="live" if source == "live" else None,
                )
            )

    # §2 — every configured model-API provider lists its full registry shortlist as
    # configured rows so any flagship can be selected when the vault key resolves.
    from aethos_core.llm.model_providers import configured_model_providers, model_provider_rows, live_model_rows

    for spec in configured_model_providers():
        if spec.id == "anthropic":
            continue
        _, source = live_model_rows(spec.id)
        for model, label in model_provider_rows(spec):
            rows.append(
                _entry(
                    catalog_id=f"{spec.id}:{model}",
                    provider=spec.id,
                    model=model,
                    label=label,
                    configured=True,
                    model_source="live" if source == "live" else None,
                )
            )

    if _local_configured():
        for model, label in _local_model_rows():
            rows.append(
                _entry(
                    catalog_id=f"local:{model}",
                    provider="local",
                    model=model,
                    label=label,
                    configured=True,
                )
            )

    # Governed Model Foundry: approved + served local models are configured and
    # routable to their loopback endpoint, regardless of LOCAL_LLM_* env config.
    existing_ids = {str(row.get("id")) for row in rows}
    for model_id, label, _endpoint in _served_foundry_rows():
        catalog_id = f"local:{model_id}"
        if catalog_id in existing_ids:
            continue
        existing_ids.add(catalog_id)
        rows.append(
            _entry(
                catalog_id=catalog_id,
                provider="local",
                model=model_id,
                label=label,
                configured=True,
            )
        )

    rows = _dedupe_catalog(rows)

    if include_unconfigured:
        return rows
    return [row for row in rows if row.get("configured")]


def _model_identity(row: dict[str, Any]) -> str:
    """Canonical identity for a model across routes.

    An OpenRouter-routed ``openai/gpt-4o`` and a direct ``openai`` ``gpt-4o`` are the
    same logical model, so they collapse to one catalog entry (§2).
    """
    provider = str(row.get("provider") or "")
    model = str(row.get("model") or "")
    if provider == "openrouter" and "/" in model:
        model = model.split("/", 1)[1]
    return model.strip().lower()


def _dedupe_catalog(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One canonical entry per logical model; prefer configured + direct-provider.

    Keeps the ``default`` entry untouched. For collisions, the kept entry is the one
    that is configured (a model whose provider key exists never loses to an
    unconfigured duplicate) and, tie-broken, the direct provider over OpenRouter.
    """
    out: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    for row in rows:
        if str(row.get("id")) == DEFAULT_CATALOG_ID:
            out.append(row)
            continue
        key = _model_identity(row)
        if key not in index:
            index[key] = len(out)
            out.append(row)
            continue
        existing = out[index[key]]
        candidate_rank = (bool(row.get("configured")), row.get("provider") != "openrouter")
        existing_rank = (bool(existing.get("configured")), existing.get("provider") != "openrouter")
        if candidate_rank > existing_rank:
            out[index[key]] = row
    return out


def model_catalog_snapshot(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.llm.effective_model import resolve_effective_model
    from aethos_core.llm.session_model_override import get_session_model_override

    effective = resolve_effective_model(session_id=session_id)
    return {
        "ok": True,
        "models": list_available_models(include_unconfigured=False),
        "default_catalog_id": DEFAULT_CATALOG_ID,
        "env_default": env_default_catalog_entry(),
        "session_override": get_session_model_override(session_id),
        "effective": {
            "catalog_id": effective.catalog_id,
            "provider": effective.provider,
            "model": effective.model,
            "label": effective.label,
            "source": effective.source,
        },
    }
