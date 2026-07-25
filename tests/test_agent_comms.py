# SPDX-License-Identifier: Apache-2.0
"""Inter-agent comms: a coordination run records who-talks-to-whom (dispatch/report/handoff)
so the live multi-agent visual can animate the team working. Read-only, tenant-scoped."""

from __future__ import annotations

from uuid import uuid4

import aethos_core.agents.runtime.comms as comms
from aethos_core.tenancy import tenant_scope


def _sid() -> str:
    return f"sess-{uuid4().hex[:8]}"


def test_record_and_read_events():
    sid = _sid()
    with tenant_scope("alice@example.com"):
        comms.start_coordination_comms(sid, [{"id": "code_intelligence", "label": "architect", "role": "architect"}], goal="build x")
        comms.record_agent_message(sid, frm="orchestrator", to="code_intelligence", mtype="dispatch", summary="architect: design")
        comms.record_agent_message(sid, frm="code_intelligence", to="orchestrator", mtype="report", summary="completed")
        log = comms.get_agent_comms(sid)
    assert any(a["id"] == "orchestrator" for a in log["agents"])
    assert len(log["events"]) == 2
    assert log["events"][0]["type"] == "dispatch" and log["events"][0]["seq"] == 0
    assert log["events"][1]["from"] == "code_intelligence"


def test_start_resets_events():
    sid = _sid()
    with tenant_scope("alice@example.com"):
        comms.record_agent_message(sid, frm="a", to="b", mtype="handoff")
        comms.start_coordination_comms(sid, [{"id": "x", "label": "x", "role": "x"}], goal="g")
        log = comms.get_agent_comms(sid)
    assert log["events"] == []  # fresh run starts clean


def test_coordination_run_emits_comms(monkeypatch):
    # A real (stubbed) coordination run should populate dispatch + report events.
    from aethos_core.agents.runtime import coordination

    class _Plan:
        plan_id = "plan-1"
        class _A:
            def __init__(self, aid, task, action):
                self.agent_id, self.task, self.action = aid, task, action
        assignments = [
            _A("code_intelligence", "architect: design", "team_planning"),
            _A("qa_verification", "qa: tests", "team_planning"),
        ]
        def to_dict(self):
            return {"plan_id": self.plan_id}

    monkeypatch.setattr(coordination, "plan_task", lambda *a, **k: _Plan())
    monkeypatch.setattr(coordination, "delegate_agent_step", lambda ctx: {"agent_id": ctx.agent_id, "status": "completed", "summary": "ok"})
    monkeypatch.setattr(coordination, "merge_agent_evidence", lambda **k: {"status": "completed", "agent_contracts": []})
    monkeypatch.setattr(coordination, "format_merged_report", lambda m: "report")
    monkeypatch.setattr(coordination, "build_coordination_graph", lambda *a, **k: {})
    monkeypatch.setattr(coordination, "store_agent_artifact", lambda **k: {"artifact_id": "art-1"})
    monkeypatch.setattr(coordination, "record_coordination_patterns", lambda **k: [], raising=False)

    sid = _sid()
    with tenant_scope("alice@example.com"):
        coordination.run_agent_coordination(goal="build x", session_id=sid)
        log = comms.get_agent_comms(sid)
    types = [e["type"] for e in log["events"]]
    assert "dispatch" in types and "report" in types
    assert "handoff" in types  # first agent hands off to the second
