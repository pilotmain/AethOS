# SPDX-License-Identifier: Apache-2.0
"""Deep research runtime acceptance (§B1)."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.research.deep_research_runtime import run_deep_research_pipeline
from aethos_core.research.research_runtime import ResearchRunResult


def test_deep_research_disabled_honest():
    with patch("aethos_core.research.deep_research_runtime.deep_research_enabled", return_value=False):
        out = run_deep_research_pipeline("research the current state of edge AI")
    assert out["ok"] is False
    assert out["error"] == "deep_research_disabled"


def test_deep_research_pipeline_steps_and_report():
    mock_run = ResearchRunResult(
        ok=True,
        query="edge AI market",
        replay_id="rrun-test",
        reply="# Edge AI\n\nSources indicate growth in on-device inference.",
        artifact_ids=["art-1"],
        timeline=[{"step": "synthesis", "source_count": 2}],
    )
    with patch("aethos_core.research.deep_research_runtime.deep_research_enabled", return_value=True), patch(
        "aethos_core.research.deep_research_runtime.run_research_query",
        return_value=mock_run,
    ), patch("aethos_core.canvas.canvas_store.render_canvas_view"):
        out = run_deep_research_pipeline(
            "research the current state of edge AI and write me a brief",
            depth=2,
            session_id="deep-test",
        )
    assert out["ok"] is True
    assert "Edge AI" in out["report"]
    assert any(s.get("step") == "synthesize" for s in out["steps"])
    assert out["artifact_ids"] == ["art-1"]
