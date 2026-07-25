# SPDX-License-Identifier: Apache-2.0
"""Blind model comparison — operator research eval without model labels.

Honors the operator's chosen models/providers (no silent Anthropic substitution),
keeps them blind during the test, and reveals the *true* model + provider behind
each slot afterward.
"""

from __future__ import annotations

import random
from typing import Any


def _resolve(catalog_id: str | None) -> dict[str, str]:
    """Resolve a chosen catalog id (or the .env default) to model + provider."""
    from aethos_core.llm.model_catalog import catalog_entry_for_id, env_default_catalog_entry

    if catalog_id and catalog_id.lower() not in ("default", "env"):
        entry = catalog_entry_for_id(catalog_id)
        if entry is not None and entry.get("configured"):
            return {
                "catalog_id": str(entry["id"]),
                "label": str(entry["label"]),
                "model": str(entry["model"]),
                "provider": str(entry["provider"]),
            }
    default = env_default_catalog_entry()
    return {
        "catalog_id": "default",
        "label": str(default["label"]),
        "model": str(default["model"]),
        "provider": str(default["provider"]),
    }


def run_blind_model_eval(
    *,
    prompt: str,
    model_a: str | None = None,
    model_b: str | None = None,
    label_a: str = "Model A",
    label_b: str = "Model B",
) -> dict[str, Any]:
    """Run two completions on the chosen models and return blind-labeled responses."""
    topic = (prompt or "").strip()
    if len(topic) < 8:
        return {"ok": False, "error": "prompt_too_short"}

    from aethos_core.config import get_settings

    settings = get_settings()
    pick_a = _resolve(model_a)
    pick_b = _resolve(model_b)

    if not settings.use_real_llm:
        stub_a = f"Blind response on {pick_a['model']} for: {topic[:120]}… (enable USE_REAL_LLM for live eval)"
        stub_b = f"Blind response on {pick_b['model']} for: {topic[:120]}… (enable USE_REAL_LLM for live eval)"
        blind = _blind_pack(stub_a, pick_a, stub_b, pick_b)
        return {
            "ok": True,
            "mode": "stub",
            "prompt": topic,
            "labels": {"a": label_a, "b": label_b},
            "selected": {"a": pick_a, "b": pick_b},
            **blind,
        }

    from aethos_core.provider.completion import complete_chat

    system = "Answer concisely for an operator blind comparison. No preamble."
    # Honor each chosen model: model_override routes to that provider, no silent swap.
    out_a = complete_chat(topic, system_overlay=system, model_override=pick_a["catalog_id"])
    out_b = complete_chat(topic, system_overlay=system, model_override=pick_b["catalog_id"])
    text_a = (out_a.text or "").strip() or "(empty)"
    text_b = (out_b.text or "").strip() or "(empty)"
    # The TRUE mapping uses the model/provider that actually answered.
    actual_a = {"model": out_a.model, "provider": out_a.provider, "label": pick_a["label"]}
    actual_b = {"model": out_b.model, "provider": out_b.provider, "label": pick_b["label"]}
    blind = _blind_pack(text_a, actual_a, text_b, actual_b)
    return {
        "ok": True,
        "mode": "live",
        "prompt": topic,
        "labels": {"a": label_a, "b": label_b},
        "selected": {"a": pick_a, "b": pick_b},
        "providers": {"a": out_a.provider, "b": out_b.provider},
        **blind,
    }


def _reveal_text(meta: dict[str, str]) -> str:
    model = str(meta.get("model") or "?")
    provider = str(meta.get("provider") or "?")
    return f"{model} ({provider})"


def _blind_pack(
    text_a: str,
    meta_a: dict[str, str],
    text_b: str,
    meta_b: dict[str, str],
) -> dict[str, Any]:
    slots = [
        {"slot": "left", "text": text_a, "meta": meta_a},
        {"slot": "right", "text": text_b, "meta": meta_b},
    ]
    random.shuffle(slots)
    return {
        "blind_slots": [
            {"slot_id": f"slot-{idx + 1}", "text": row["text"]}
            for idx, row in enumerate(slots)
        ],
        # Reveal the TRUE model + provider behind each slot (e.g. "qwen2.5:14b (local)").
        "reveal_map": {
            f"slot-{idx + 1}": _reveal_text(row["meta"]) for idx, row in enumerate(slots)
        },
    }
