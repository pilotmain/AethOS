# SPDX-License-Identifier: Apache-2.0
"""Cost-aware model routing: simple turns may use a cheaper model, but only when no
explicit model was chosen and the feature is enabled; complex turns + explicit picks
always use the full model. Default (disabled) behaviour is unchanged."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.llm import cost_router
from aethos_core.llm.effective_model import resolve_effective_model

_CHEAP = {"id": "cheap-1", "provider": "openrouter", "model": "x/cheap", "label": "Cheap", "configured": True}


def test_classify_simple_vs_complex():
    assert cost_router.classify_complexity("what time is it in Tokyo?") == "simple"
    assert cost_router.classify_complexity("hi") == "simple"
    assert cost_router.classify_complexity("analyze the architecture and propose a refactor plan") == "complex"
    assert cost_router.classify_complexity("```python\nprint(1)\n```") == "complex"
    assert cost_router.classify_complexity("Why does X fail? What about Y? And Z?") == "complex"
    assert cost_router.classify_complexity("a" * 300) == "complex"


class _FakeSettings:
    def __init__(self, enabled, cheap_id):
        self.cost_aware_routing_enabled = enabled
        self.cost_router_cheap_model = cheap_id


def test_route_disabled_returns_none():
    with patch.object(cost_router, "get_settings", create=True), \
         patch("aethos_core.config.get_settings", return_value=_FakeSettings(False, "cheap-1")):
        assert cost_router.route_for_prompt("hello there") is None


def test_route_simple_returns_cheap_when_enabled():
    with patch("aethos_core.config.get_settings", return_value=_FakeSettings(True, "cheap-1")), \
         patch("aethos_core.llm.model_catalog.catalog_entry_for_id", return_value=_CHEAP):
        assert cost_router.route_for_prompt("what's the capital of France?") == _CHEAP
        # Complex → no routing.
        assert cost_router.route_for_prompt("analyze and refactor this architecture") is None


def test_explicit_turn_override_beats_cost_routing():
    # Even with routing on + simple prompt, an explicit turn pick must win.
    with patch("aethos_core.config.get_settings", return_value=_FakeSettings(True, "cheap-1")), \
         patch("aethos_core.llm.model_catalog.catalog_entry_for_id", return_value=_CHEAP), \
         patch("aethos_core.llm.effective_model._resolve_explicit_selection") as explicit:
        explicit.return_value = "EXPLICIT"
        out = resolve_effective_model(session_id="s", turn_override="some-premium-model", prompt="hi there")
        assert out == "EXPLICIT"
        explicit.assert_called_once()


def test_simple_prompt_routes_to_cheap_on_default_branch():
    with patch("aethos_core.config.get_settings", return_value=_FakeSettings(True, "cheap-1")), \
         patch("aethos_core.llm.model_catalog.catalog_entry_for_id", return_value=_CHEAP), \
         patch("aethos_core.llm.session_model_override.get_session_model_override", return_value=""):
        out = resolve_effective_model(session_id="s", turn_override=None, prompt="hello, how are you?")
        assert out.source == "cost_router"
        assert out.model == "x/cheap"
