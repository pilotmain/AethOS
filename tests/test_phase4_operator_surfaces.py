# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.channels.discord.discord_identity import discord_session_id
from aethos_core.execution_brain.agent_tool_policy import is_tool_allowed, policy_snapshot
from aethos_core.research.research_notes_store import pin_note, list_notes


def test_discord_session_id_format() -> None:
    sid = discord_session_id(channel_id="999", user_id="111")
    assert sid.startswith("discord-")
    assert "999" in sid


def test_tool_policy_blocks_terminal_on_telegram() -> None:
    assert is_tool_allowed("web_search", channel="telegram") is True
    assert is_tool_allowed("terminal_create_preflight", channel="telegram") is False
    snap = policy_snapshot(channel="telegram")
    assert snap["restricted_channel"] is True


def test_voice_surface_gated_by_flag(monkeypatch) -> None:
    """handoff §11/§21 step 9 — voice intake is gated behind VOICE_SURFACE_ENABLED."""
    from aethos_core.config import get_settings
    from aethos_core.voice.voice_runtime import process_voice_transcript

    monkeypatch.setattr(get_settings(), "voice_surface_enabled", False)
    out = process_voice_transcript(transcript="show vercel projects", session_id="voice-test")
    assert out["ok"] is False
    assert out["error"] == "voice_surface_disabled"


def test_channel_pairing_gate_blocks_unknown_sender(tmp_path, monkeypatch) -> None:
    """handoff §6/§21 step 7 — unknown external sender is paired, not processed."""
    from aethos_core.channels import pairing_store
    from aethos_core.channels.base.channel_adapter import ChannelMessage
    from aethos_core.channels.inbound import handle_channel_message
    from aethos_core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "channel_pairing_store_dir", str(tmp_path / "pairing"))
    monkeypatch.setattr(settings, "channel_gateway_enabled", True)
    monkeypatch.setattr(settings, "channel_dm_policy", "pairing")

    msg = ChannelMessage(
        channel="telegram",
        external_user_id="u-777",
        external_chat_id="c-1",
        text="show vercel projects",
        session_id="tg-c-1-u-777",
    )
    blocked = handle_channel_message(msg)
    assert blocked.intent == "channel_pairing_required"
    code = blocked.meta["pairing_code"]
    assert pairing_store.is_sender_allowed("telegram", "u-777") is False

    approved = pairing_store.approve_pairing("telegram", code)
    assert approved["status"] == "paired"
    assert pairing_store.is_sender_allowed("telegram", "u-777") is True


def test_channel_pairing_gate_off_when_gateway_disabled(tmp_path, monkeypatch) -> None:
    from aethos_core.channels.base.channel_adapter import ChannelMessage
    from aethos_core.channels.inbound import _maybe_pairing_gate
    from aethos_core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "channel_pairing_store_dir", str(tmp_path / "pairing"))
    monkeypatch.setattr(settings, "channel_gateway_enabled", False)
    msg = ChannelMessage(
        channel="telegram",
        external_user_id="u-1",
        external_chat_id="c",
        text="hi",
        session_id="tg-c-u-1",
    )
    assert _maybe_pairing_gate(msg) is None  # existing behavior unchanged when off


def test_outbound_send_is_governed(tmp_path, monkeypatch) -> None:
    """handoff §5/§8 — channel_send creates a preflight and never sends without approval."""
    import json

    from aethos_core.channels import outbound_governance, pairing_store
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "channel_outbound_store_dir", str(tmp_path / "outbound"))
    monkeypatch.setattr(settings, "channel_pairing_store_dir", str(tmp_path / "pairing"))
    monkeypatch.setattr(settings, "channel_gateway_enabled", True)
    monkeypatch.setattr(settings, "outbound_send_execution_enabled", False)

    out = json.loads(
        execute_agent_tool(
            "channel_send",
            {"channel": "telegram", "to": "peer-1", "body": "hello there peer"},
            session_id="operator",
        )
    )
    assert out["requires_approval"] is True
    assert out["sent"] is False
    pid = out["preflight_id"]

    # Approval blocked while execution flag is off
    assert outbound_governance.approve_outbound_send(pid)["error"] == "outbound_send_execution_disabled"

    # With execution on but recipient not allowlisted -> blocked
    monkeypatch.setattr(settings, "outbound_send_execution_enabled", True)
    assert outbound_governance.approve_outbound_send(pid)["error"] == "recipient_not_allowlisted"


def test_channel_send_denied_for_sandboxed_session(monkeypatch) -> None:
    """handoff §8/§12 — outbound send is not callable from non-main sessions."""
    import json

    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    monkeypatch.setattr(get_settings(), "sandbox_nonmain_enabled", True)
    denied = json.loads(
        execute_agent_tool(
            "channel_send",
            {"channel": "telegram", "to": "p", "body": "hi there now"},
            session_id="agent:operator:subagent:spawn-x",
        )
    )
    assert denied["error"] == "tool_not_allowed_for_channel"


def test_live_canvas_render_is_gated_and_readonly(tmp_path, monkeypatch) -> None:
    """handoff §11/§21 step 10 — canvas_render is gated, read-only, and never executes."""
    import json

    from aethos_core.canvas.canvas_store import get_canvas_state
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "canvas_store_dir", str(tmp_path / "canvas"))
    monkeypatch.setattr(settings, "canvas_surface_enabled", False)
    off = json.loads(
        execute_agent_tool("canvas_render", {"view_type": "status", "title": "X"}, session_id="default")
    )
    assert off["error"] == "canvas_surface_disabled"

    monkeypatch.setattr(settings, "canvas_surface_enabled", True)
    on = json.loads(
        execute_agent_tool(
            "canvas_render",
            {"view_type": "job_timeline", "title": "Jobs", "data": {"events": [{"label": "a", "status": "ok"}]}},
            session_id="default",
        )
    )
    assert on["ok"] is True
    assert on["read_only"] is True
    bad = json.loads(
        execute_agent_tool("canvas_render", {"view_type": "execute", "title": "X"}, session_id="default")
    )
    assert bad["error"] == "unsupported_view_type"
    assert get_canvas_state(session_id="default")["view_count"] == 1


def test_canvas_render_is_deterministic_for_explicit_requests(tmp_path, monkeypatch) -> None:
    """Explicit canvas asks require a real tool write — no prose fallback."""
    from aethos_core.canvas.canvas_store import get_canvas_state, render_canvas_view
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_runtime import _ensure_canvas_render, canvas_render_success_confirmation

    settings = get_settings()
    monkeypatch.setattr(settings, "canvas_store_dir", str(tmp_path / "canvas"))

    # Flag off → no render, original reply preserved (honest disabled message stays).
    monkeypatch.setattr(settings, "canvas_surface_enabled", False)
    out = _ensure_canvas_render(
        "render a job timeline on the canvas", session_id="sess-det", reply="orig", views_before=0
    )
    assert out == "orig"
    assert get_canvas_state(session_id="sess-det")["view_count"] == 0

    # Flag on + model declined without tool → deterministic structured render (no chat dump).
    monkeypatch.setattr(settings, "canvas_surface_enabled", True)
    out = _ensure_canvas_render(
        "render a job timeline on the canvas",
        session_id="sess-det",
        reply="a big dumped table that should not be in chat",
        views_before=0,
    )
    state = get_canvas_state(session_id="sess-det")
    assert state["view_count"] == 1
    assert state["views"][0]["view_type"] == "job_timeline"
    assert "Canvas tab" in out
    assert "restricted" not in out.lower()

    # Structured tool write → confirmation when view exists.
    render_canvas_view(
        session_id="sess-det",
        view_type="job_timeline",
        title="Jobs",
        data={"events": [{"label": "deploy", "status": "success"}]},
    )
    out = _ensure_canvas_render(
        "render a job timeline on the canvas",
        session_id="sess-det",
        reply=canvas_render_success_confirmation("job_timeline"),
        views_before=0,
    )
    assert "Canvas tab" in out

    # Non-canvas request → untouched.
    out = _ensure_canvas_render(
        "what is the weather", session_id="sess-det", reply="sunny", views_before=1
    )
    assert out == "sunny"


def test_workspace_documents_are_gated_and_draft_only(tmp_path, monkeypatch) -> None:
    """handoff §8/§21 step 4 — Documents are gated, draft-only, and CRUD round-trips."""
    import json

    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_store_dir", str(tmp_path / "wsuite"))

    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    off = json.loads(execute_agent_tool("workspace_doc", {"action": "create", "title": "X"}, session_id="default"))
    assert off["error"] == "workspace_suite_disabled"

    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    created = json.loads(
        execute_agent_tool(
            "workspace_doc",
            {"action": "create", "title": "Notes", "content": "hello", "format": "markdown"},
            session_id="default",
        )
    )
    assert created["ok"] is True
    assert created["document"]["draft_only"] is True
    doc_id = created["document"]["id"]

    updated = json.loads(
        execute_agent_tool(
            "workspace_doc",
            {"action": "update", "doc_id": doc_id, "content": "hello world"},
            session_id="default",
        )
    )
    assert updated["ok"] is True
    assert updated["document"]["char_count"] == len("hello world")

    fetched = json.loads(execute_agent_tool("workspace_doc", {"action": "get", "doc_id": doc_id}, session_id="default"))
    assert fetched["document"]["content"] == "hello world"

    listed = json.loads(execute_agent_tool("workspace_doc", {"action": "list"}, session_id="default"))
    assert listed["document_count"] == 1


def test_workspace_doc_tool_hidden_when_suite_disabled(monkeypatch) -> None:
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import readonly_agent_tool_schemas

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    assert "workspace_doc" not in names
    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    assert "workspace_doc" in names


def test_workspace_notes_tasks_gated_and_scheduled_never_auto_executes(tmp_path, monkeypatch) -> None:
    """handoff §8/§21 step 4 — notes/tasks gated; scheduled tasks recorded, never auto-run."""
    import json

    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_store_dir", str(tmp_path / "wsuite"))

    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    off = json.loads(execute_agent_tool("workspace_notes", {"action": "note_add", "text": "x"}, session_id="default"))
    assert off["error"] == "workspace_suite_disabled"

    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    note = json.loads(execute_agent_tool("workspace_notes", {"action": "note_add", "text": "remember this"}, session_id="default"))
    assert note["ok"] is True

    task = json.loads(
        execute_agent_tool(
            "workspace_notes",
            {"action": "task_add", "text": "deploy check", "scheduled_for": "daily 9am"},
            session_id="default",
        )
    )
    assert task["ok"] is True
    assert task["task"]["scheduled_for"] == "daily 9am"
    # Scheduled tasks are recorded only — they must never auto-execute.
    assert task["task"]["auto_execute"] is False

    done = json.loads(
        execute_agent_tool("workspace_notes", {"action": "task_done", "task_id": task["task"]["id"]}, session_id="default")
    )
    assert done["task"]["done"] is True

    notes = json.loads(execute_agent_tool("workspace_notes", {"action": "note_list"}, session_id="default"))
    tasks = json.loads(execute_agent_tool("workspace_notes", {"action": "task_list"}, session_id="default"))
    assert notes["note_count"] == 1
    assert tasks["task_count"] == 1


def test_model_foundry_gated_and_serve_is_governed(tmp_path, monkeypatch) -> None:
    """handoff §8/§21 step 4 — foundry gated; serve is governed (recorded, never executed)."""
    import json

    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_store_dir", str(tmp_path / "wsuite"))

    monkeypatch.setattr(settings, "model_foundry_enabled", False)
    off = json.loads(execute_agent_tool("model_foundry", {"action": "scan"}, session_id="default"))
    assert off["error"] == "model_foundry_disabled"

    monkeypatch.setattr(settings, "model_foundry_enabled", True)
    scan = json.loads(execute_agent_tool("model_foundry", {"action": "scan"}, session_id="default"))
    assert scan["ok"] is True
    assert "usable_vram_gb" in scan

    rec = json.loads(execute_agent_tool("model_foundry", {"action": "recommend"}, session_id="default"))
    assert rec["ok"] is True
    assert rec["model_count"] >= 1

    serve = json.loads(
        execute_agent_tool("model_foundry", {"action": "serve_preflight", "model_id": "mistral-7b"}, session_id="default")
    )
    assert serve["ok"] is True
    # Governed: serving is recorded only, binds loopback, and never auto-executes.
    assert serve["serve_request"]["executed"] is False
    assert serve["serve_request"]["requires_approval"] is True
    assert serve["serve_request"]["bind"] == "127.0.0.1"

    unknown = json.loads(
        execute_agent_tool("model_foundry", {"action": "serve_preflight", "model_id": "nope"}, session_id="default")
    )
    assert unknown["error"] == "unknown_model"


def test_model_foundry_tool_hidden_when_disabled(monkeypatch) -> None:
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import readonly_agent_tool_schemas

    settings = get_settings()
    monkeypatch.setattr(settings, "model_foundry_enabled", False)
    assert "model_foundry" not in {t["name"] for t in readonly_agent_tool_schemas()}
    monkeypatch.setattr(settings, "model_foundry_enabled", True)
    assert "model_foundry" in {t["name"] for t in readonly_agent_tool_schemas()}


def test_email_triage_heuristic_classifies_urgency_and_tags() -> None:
    """handoff §8 — pure triage heuristic flags urgency, spam, and tags (no network)."""
    from aethos_core.workspace_suite.email_triage import triage_message

    urgent = triage_message(subject="URGENT: payment failed", sender="billing@x.com", body="Your invoice is overdue")
    assert urgent["urgency"] == "high"
    assert "billing" in urgent["tags"]

    spammy = triage_message(subject="You've won!", sender="x@y.z", body="crypto giveaway, act now to claim")
    assert spammy["spam"] is True


def test_email_drafts_never_auto_send_and_route_through_governance(tmp_path, monkeypatch) -> None:
    """handoff §8/§21 step 4 — email drafts are draft-only; send goes through outbound governance."""
    import json

    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_store_dir", str(tmp_path / "wsuite"))
    monkeypatch.setattr(settings, "channel_outbound_store_dir", str(tmp_path / "outbound"))

    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    off = json.loads(execute_agent_tool("workspace_email", {"action": "triage"}, session_id="default"))
    assert off["error"] == "workspace_suite_disabled"

    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    # No IMAP creds configured -> graceful not_configured, never crashes.
    triage = json.loads(execute_agent_tool("workspace_email", {"action": "triage"}, session_id="default"))
    assert triage["error"] == "imap_not_configured"

    draft = json.loads(
        execute_agent_tool(
            "workspace_email",
            {"action": "draft_reply", "to": "person@example.com", "subject": "Re: hi", "body": "thanks!"},
            session_id="default",
        )
    )
    assert draft["ok"] is True
    assert draft["draft"]["sent"] is False
    assert draft["draft"]["status"] == "draft"
    draft_id = draft["draft"]["id"]

    # Sending routes through the governed outbound preflight (not a direct send).
    monkeypatch.setattr(settings, "channel_gateway_enabled", True)
    pre = json.loads(
        execute_agent_tool("workspace_email", {"action": "send_preflight", "draft_id": draft_id}, session_id="default")
    )
    assert pre["ok"] is True
    assert pre["requires_approval"] is True
    assert pre["sent"] is False


def test_workspace_calendar_ics_roundtrip_and_readonly_sync(tmp_path, monkeypatch) -> None:
    """handoff §8/§21 step 4 — calendar gated; .ics round-trips; CalDAV sync is readonly."""
    import json

    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_store_dir", str(tmp_path / "wsuite"))

    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    off = json.loads(execute_agent_tool("workspace_calendar", {"action": "list"}, session_id="default"))
    assert off["error"] == "workspace_suite_disabled"

    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    add = json.loads(
        execute_agent_tool(
            "workspace_calendar",
            {"action": "add", "summary": "Standup", "start": "20260604T090000Z", "end": "20260604T091500Z"},
            session_id="default",
        )
    )
    assert add["ok"] is True

    ics = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:abc@x\r\n"
        "SUMMARY:Imported meeting\r\nDTSTART:20260605T100000Z\r\nEND:VEVENT\r\nEND:VCALENDAR"
    )
    imported = json.loads(
        execute_agent_tool("workspace_calendar", {"action": "import_ics", "ics_text": ics}, session_id="default")
    )
    assert imported["imported"] == 1

    listed = json.loads(execute_agent_tool("workspace_calendar", {"action": "list"}, session_id="default"))
    assert listed["event_count"] == 2

    exported = json.loads(execute_agent_tool("workspace_calendar", {"action": "export_ics"}, session_id="default"))
    assert "BEGIN:VEVENT" in exported["ics"]
    assert "Imported meeting" in exported["ics"]

    # CalDAV sync degrades gracefully (no creds) and is readonly by design.
    sync = json.loads(execute_agent_tool("workspace_calendar", {"action": "sync"}, session_id="default"))
    assert sync["error"] == "caldav_not_configured"


def test_workspace_tabs_all_hidden_when_suite_disabled(monkeypatch) -> None:
    """handoff §8 — every workspace_* tool is hidden from the model when the suite is off."""
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_tool_executor import readonly_agent_tool_schemas

    settings = get_settings()
    monkeypatch.setattr(settings, "workspace_suite_enabled", False)
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    for tool in ("workspace_doc", "workspace_notes", "workspace_email", "workspace_calendar"):
        assert tool not in names
    monkeypatch.setattr(settings, "workspace_suite_enabled", True)
    names = {t["name"] for t in readonly_agent_tool_schemas()}
    for tool in ("workspace_doc", "workspace_notes", "workspace_email", "workspace_calendar"):
        assert tool in names


def test_research_notes_pin(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = pin_note(session_id="sess-notes", text="Railway deploy succeeded", replay_id="rrun-x")
    assert out["ok"] is True
    listed = list_notes(session_id="sess-notes")
    assert len(listed.get("notes") or []) == 1


def test_phase4_operator_routes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    assert client.get("/api/v1/runtime/agent-tool-policy?channel=chat").status_code == 200
    assert client.get("/api/v1/runtime/cron/status").status_code == 200
    assert client.get("/api/v1/runtime/sandbox/status").status_code == 200
    assert client.get("/api/v1/delivery/status").status_code == 200
    blind = client.post("/api/v1/research/blind-eval", json={"prompt": "compare railway vs vercel for api hosting"})
    assert blind.status_code == 200
    assert blind.json().get("ok") is True
