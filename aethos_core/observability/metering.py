# SPDX-License-Identifier: Apache-2.0
"""Usage metering — honest, always-visible token + cost tracking.

AethOS never hides what a turn costs. Each LLM turn records real input/output
token counts (as returned by the provider) and a derived cost from a transparent
per-model rate table. When the rate for a model is unknown we report tokens only
and label the cost "n/a" — we never invent a number.
"""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.production.paths import production_root


# Transparent per-model rate table — USD per 1,000,000 tokens, (input, output).
# Matched by case-insensitive substring against the model id. Public list prices;
# update as providers change pricing. Unknown models => cost reported as "n/a".
MODEL_RATES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-7-sonnet": (3.00, 15.00),
    "claude-haiku-4": (1.00, 5.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-opus-4": (15.00, 75.00),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-haiku": (0.25, 1.25),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "o3-mini": (1.10, 4.40),
}


# Per-model context-window limits (tokens), matched by case-insensitive substring.
# Used for the §3 "context used %" display. Unknown models => context % is "n/a".
MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "claude-3-5-haiku": 200_000,
    "claude-3-5-sonnet": 200_000,
    "claude-3-7-sonnet": 200_000,
    "claude-haiku-4": 200_000,
    "claude-sonnet-4": 200_000,
    "claude-opus-4": 200_000,
    "claude-3-opus": 200_000,
    "claude-3-haiku": 200_000,
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
    "gpt-4.1-mini": 1_047_576,
    "gpt-4.1": 1_047_576,
    "o3-mini": 200_000,
}


def _path():
    return production_root() / "metering.json"


def _load() -> dict[str, Any]:
    if not _path().is_file():
        return {"orgs": {}, "updated_at": time()}
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"orgs": {}, "updated_at": time()}


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _match_rate(model: str | None) -> tuple[float, float] | None:
    if not model:
        return None
    low = str(model).lower()
    for key, rate in MODEL_RATES_USD_PER_MTOK.items():
        if key in low:
            return rate
    return None


def _match_context_limit(model: str | None) -> int | None:
    if not model:
        return None
    low = str(model).lower()
    for key, limit in MODEL_CONTEXT_LIMITS.items():
        if key in low:
            return limit
    return None


def compute_cost_usd(
    model: str | None,
    input_tokens: float,
    output_tokens: float,
    provider: str | None = None,
) -> float | None:
    """Derived cost in USD. Local inference is free → explicit $0.00 (not "n/a").

    Returns None only when a paid model's rate is genuinely unknown.
    """
    if str(provider or "").lower() == "local":
        return 0.0
    rate = _match_rate(model)
    if rate is None:
        return None
    in_rate, out_rate = rate
    return (float(input_tokens) / 1_000_000.0) * in_rate + (float(output_tokens) / 1_000_000.0) * out_rate


def _accumulate_tokens(
    bucket: dict[str, Any],
    *,
    model: str | None,
    input_tokens: float,
    output_tokens: float,
    cache_read_tokens: float = 0.0,
    cache_creation_tokens: float = 0.0,
    provider: str | None = None,
) -> None:
    """Add one turn's tokens + cost into a bucket (org / model / session)."""
    bucket["input_tokens"] = float(bucket.get("input_tokens") or 0) + float(input_tokens)
    bucket["output_tokens"] = float(bucket.get("output_tokens") or 0) + float(output_tokens)
    bucket["cache_read_tokens"] = float(bucket.get("cache_read_tokens") or 0) + float(cache_read_tokens)
    bucket["cache_creation_tokens"] = float(bucket.get("cache_creation_tokens") or 0) + float(cache_creation_tokens)
    bucket["turns"] = float(bucket.get("turns") or 0) + 1
    # Context window consumed on the most recent turn = full uncached + cached prefix.
    bucket["last_context_tokens"] = float(input_tokens) + float(cache_read_tokens) + float(cache_creation_tokens)
    if model:
        bucket["last_model"] = model
    if provider:
        bucket["provider"] = provider
    # §1 prompt caching saves on cache reads: billed at ~10% of base input rate.
    cost = compute_cost_usd(model, input_tokens, output_tokens, provider=provider)
    if cost is None:
        # Cost for at least one turn is unknown — the whole bucket is "n/a".
        bucket["cost_known"] = False
    else:
        cache_rate = _match_rate(model)
        if cache_rate is not None and cache_read_tokens:
            cost += (float(cache_read_tokens) / 1_000_000.0) * cache_rate[0] * 0.1
        bucket["cost_usd"] = float(bucket.get("cost_usd") or 0) + cost
        bucket.setdefault("cost_known", True)


def record_usage(
    *,
    org_id: str,
    metric: str | None = None,
    amount: float = 1.0,
    input_tokens: float = 0.0,
    output_tokens: float = 0.0,
    model: str | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    cache_read_tokens: float = 0.0,
    cache_creation_tokens: float = 0.0,
) -> None:
    """Record dimensional usage and/or per-turn token usage for an org.

    Backward compatible: passing ``metric``/``amount`` records a dimension as
    before. Passing token counts records per-turn tokens + derived cost, broken
    down per model and per session (for the always-visible chat usage strip).
    """
    data = _load()
    orgs = dict(data.get("orgs") or {})
    bucket = dict(orgs.get(org_id) or {})

    if metric:
        bucket[metric] = float(bucket.get(metric) or 0) + amount

    if input_tokens or output_tokens or model:
        _accumulate_tokens(
            bucket,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            provider=provider,
        )
        if provider:
            bucket["last_provider"] = provider

        models = dict(bucket.get("models") or {})
        mkey = model or "unknown"
        mrec = dict(models.get(mkey) or {})
        _accumulate_tokens(
            mrec,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
            provider=provider,
        )
        models[mkey] = mrec
        bucket["models"] = models

        if session_id:
            sessions = dict(bucket.get("sessions") or {})
            srec = dict(sessions.get(session_id) or {})
            _accumulate_tokens(
                srec,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_creation_tokens=cache_creation_tokens,
                provider=provider,
            )
            if provider:
                srec["last_provider"] = provider
            # Per-session, per-model breakdown — drives the honest "72% local / 28%
            # cloud" split on the usage strip.
            smodels = dict(srec.get("models") or {})
            smrec = dict(smodels.get(mkey) or {})
            _accumulate_tokens(
                smrec,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_creation_tokens=cache_creation_tokens,
                provider=provider,
            )
            smodels[mkey] = smrec
            srec["models"] = smodels
            sessions[session_id] = srec
            bucket["sessions"] = sessions

    orgs[org_id] = bucket
    data["orgs"] = orgs
    _save(data)


def record_turn_usage(
    *,
    session_id: str,
    model: str | None,
    input_tokens: float,
    output_tokens: float,
    provider: str | None = None,
    org_id: str | None = None,
    cache_read_tokens: float = 0.0,
    cache_creation_tokens: float = 0.0,
) -> None:
    """Convenience: record one completed LLM turn for the current org/session."""
    if not (input_tokens or output_tokens):
        return
    from aethos_core.orgs.organizations import get_current_organization

    oid = org_id or get_current_organization().get("org_id")
    if not oid:
        return
    try:
        record_usage(
            org_id=str(oid),
            input_tokens=float(input_tokens),
            output_tokens=float(output_tokens),
            model=model,
            session_id=session_id,
            provider=provider,
            cache_read_tokens=float(cache_read_tokens),
            cache_creation_tokens=float(cache_creation_tokens),
        )
        from aethos_core.config import get_settings

        if get_settings().multi_tenant_enabled:
            from aethos_core.tenancy.tenant_metering import record_llm_tokens

            record_llm_tokens(
                0,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
            )
    except Exception:
        # Metering must never break a chat turn.
        pass


def _cost_block(cost_usd: Any, cost_known: Any) -> dict[str, Any]:
    known = bool(cost_known) and cost_usd is not None
    if not known:
        return {"usd": None, "known": False, "label": "n/a"}
    usd = round(float(cost_usd), 4)
    return {"usd": usd, "known": True, "label": f"${usd:.4f}"}


def _tokens_block(bucket: dict[str, Any]) -> dict[str, float]:
    inp = float(bucket.get("input_tokens") or 0)
    out = float(bucket.get("output_tokens") or 0)
    return {"input": inp, "output": out, "total": inp + out}


def _context_block(bucket: dict[str, Any]) -> dict[str, Any]:
    """Most-recent-turn context-window usage for the strip (e.g. 12k/200k = 6%)."""
    used = float(bucket.get("last_context_tokens") or 0)
    limit = _match_context_limit(bucket.get("last_model"))
    if not used or not limit:
        return {"used": used or None, "limit": limit, "pct": None, "known": False}
    pct = round((used / float(limit)) * 100.0, 1)
    return {"used": used, "limit": limit, "pct": pct, "known": True}


def _cache_block(bucket: dict[str, Any]) -> dict[str, Any]:
    """Cumulative prompt-cache effectiveness for the strip (cache hit ratio)."""
    read = float(bucket.get("cache_read_tokens") or 0)
    creation = float(bucket.get("cache_creation_tokens") or 0)
    fresh = float(bucket.get("input_tokens") or 0)
    cached_total = read + creation + fresh
    if cached_total <= 0:
        return {"read_tokens": 0.0, "creation_tokens": 0.0, "hit_ratio": None, "known": False}
    hit_ratio = round((read / cached_total) * 100.0, 1)
    return {
        "read_tokens": read,
        "creation_tokens": creation,
        "hit_ratio": hit_ratio,
        "known": read > 0 or creation > 0,
    }


def _model_breakdown(models: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-model split sorted by token share, each with an honest cost + pct.

    Powers the usage strip's "Qwen2.5 14B 72% ($0.00) · claude-opus-4-6 28% ($0.34)".
    """
    rows: list[dict[str, Any]] = []
    total = 0.0
    for mkey, mrec in (models or {}).items():
        if not isinstance(mrec, dict):
            continue
        tok = float(mrec.get("input_tokens") or 0) + float(mrec.get("output_tokens") or 0)
        total += tok
        rows.append(
            {
                "model": mkey,
                "provider": mrec.get("provider"),
                "tokens": _tokens_block(mrec),
                "cost": _cost_block(mrec.get("cost_usd"), mrec.get("cost_known")),
                "turns": int(mrec.get("turns") or 0),
                "_tok": tok,
            }
        )
    for row in rows:
        row["pct"] = round((row.pop("_tok") / total) * 100.0, 1) if total > 0 else 0.0
    rows.sort(key=lambda r: r["pct"], reverse=True)
    return rows


def get_usage_summary(*, org_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.orgs.organizations import get_current_organization

    oid = org_id or get_current_organization().get("org_id")
    orgs = (_load().get("orgs") or {})
    usage = orgs.get(oid) or {}

    models_summary: dict[str, Any] = {}
    for mkey, mrec in (usage.get("models") or {}).items():
        models_summary[mkey] = {
            "tokens": _tokens_block(mrec),
            "cost": _cost_block(mrec.get("cost_usd"), mrec.get("cost_known")),
            "turns": int(mrec.get("turns") or 0),
        }

    session_block: dict[str, Any] | None = None
    if session_id:
        srec = (usage.get("sessions") or {}).get(session_id) or {}
        session_block = {
            "session_id": session_id,
            "model": srec.get("last_model"),
            "provider": srec.get("last_provider"),
            "tokens": _tokens_block(srec),
            "cost": _cost_block(srec.get("cost_usd"), srec.get("cost_known")),
            "context": _context_block(srec),
            "cache": _cache_block(srec),
            "turns": int(srec.get("turns") or 0),
            "models": _model_breakdown(srec.get("models") or {}),
        }

    return {
        "org_id": oid,
        "usage": usage,
        "model": usage.get("last_model"),
        "provider": usage.get("last_provider"),
        "tokens": _tokens_block(usage),
        "cost": _cost_block(usage.get("cost_usd"), usage.get("cost_known")),
        "context": _context_block(usage),
        "cache": _cache_block(usage),
        "turns": int(usage.get("turns") or 0),
        "models": models_summary,
        "session": session_block,
        "dimensions": {
            "runtime_minutes": float(usage.get("runtime_minutes") or 0),
            "browser_captures": float(usage.get("browser_captures") or 0),
            "research_requests": float(usage.get("research_requests") or 0),
            "engineering_executions": float(usage.get("engineering_executions") or 0),
            "storage_bytes": float(usage.get("storage_bytes") or 0),
        },
        "integrations_ready": ["prometheus", "grafana", "opentelemetry", "loki"],
    }


def clear_metering_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
