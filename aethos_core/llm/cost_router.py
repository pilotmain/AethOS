# SPDX-License-Identifier: Apache-2.0
"""Cost-aware model routing — send simple turns to a cheaper model, escalate when needed.

Only engages when the user has made NO explicit model choice (i.e. the resolver would
otherwise use the .env default). An explicit per-turn or per-session selection always
wins — cost routing never overrides what the operator picked.

Default behaviour is unchanged: the feature is off unless ``COST_AWARE_ROUTING_ENABLED``
is set AND ``COST_ROUTER_CHEAP_MODEL`` names a configured catalog model. The complexity
classifier is heuristic (deterministic, zero token cost).
"""

from __future__ import annotations

import re
from typing import Any

# Signals that a prompt warrants the premium (default) model.
_COMPLEX_KEYWORDS = (
    "analyze",
    "analyse",
    "debug",
    "refactor",
    "architect",
    "architecture",
    "design",
    "plan",
    "compare",
    "optimi",
    "investigate",
    "root cause",
    "trace",
    "step by step",
    "step-by-step",
    "explain why",
    "prove",
    "derive",
    "orchestrat",
    "strategy",
    "trade-off",
    "tradeoff",
    "migrate",
    "diagnose",
)

_CODE_RX = re.compile(r"```|\bdef \b|\bclass \b|\bimport \b|\bfunction \b|=>|\{\s*\n")


def classify_complexity(prompt: str) -> str:
    """Return 'simple' or 'complex' for a prompt (heuristic, deterministic)."""
    text = (prompt or "").strip()
    if not text:
        return "simple"
    low = text.lower()
    if len(text) > 280:
        return "complex"
    if _CODE_RX.search(text):
        return "complex"
    if low.count("?") >= 2:
        return "complex"
    if any(kw in low for kw in _COMPLEX_KEYWORDS):
        return "complex"
    # Multi-sentence and not short → lean complex.
    if len(re.findall(r"[.!?]\s", text)) >= 2 and len(text) > 160:
        return "complex"
    return "simple"


def cheap_model_entry() -> dict[str, Any] | None:
    """Resolve the configured cheap model to a *configured* catalog entry, or None."""
    from aethos_core.config import get_settings
    from aethos_core.llm.model_catalog import catalog_entry_for_id

    cheap_id = str(getattr(get_settings(), "cost_router_cheap_model", "") or "").strip()
    if not cheap_id:
        return None
    entry = catalog_entry_for_id(cheap_id)
    if entry and entry.get("configured"):
        return entry
    return None


def route_for_prompt(prompt: str | None) -> dict[str, Any] | None:
    """Return the cheap catalog entry to use for a SIMPLE prompt, else None (use default).

    None means "no routing decision — fall through to the default model". Returns the
    cheap entry only when: feature enabled, a configured cheap model exists, and the
    prompt classifies as simple.
    """
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "cost_aware_routing_enabled", False):
        return None
    if not prompt or classify_complexity(prompt) != "simple":
        return None
    return cheap_model_entry()
