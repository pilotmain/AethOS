# SPDX-License-Identifier: Apache-2.0
"""Multi-Agent Live must render ALL requested specialists, even when several share a
capability (researcher/copywriter/marketer all map to 'research'). Previously the
comms graph keyed nodes by capability id, collapsing 6 roles onto 2-3 nodes."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.agents.runtime import coordination
from aethos_core.agents.runtime.comms import get_agent_comms

PROMPT = (
    "orchestrate a team of a strategist, a researcher, a copywriter, a growth marketer, "
    "a data analyst, and a launch manager to plan a product launch"
)


def _fake_step(ctx):
    return {"agent_id": ctx.agent_id, "task": ctx.task, "status": "done", "summary": "ok"}


def test_six_roles_render_as_six_distinct_nodes():
    sid = "test-distinct-nodes"
    # Avoid real model/tool work — only the comms roster shape matters here.
    with patch.object(coordination, "delegate_agent_step", _fake_step):
        coordination.run_agent_coordination(goal=PROMPT, session_id=sid)

    comms = get_agent_comms(sid)
    specialists = [a for a in comms["agents"] if a["id"] != "orchestrator"]
    ids = [a["id"] for a in specialists]
    labels = [a["label"] for a in specialists]

    assert len(ids) == 6, f"expected 6 distinct specialist nodes, got {len(ids)}: {ids}"
    assert len(set(ids)) == 6, f"node ids must be unique: {ids}"
    # Role labels are preserved even though research/operations_analyst capabilities repeat.
    assert "strategist" in labels and "launch manager" in labels
