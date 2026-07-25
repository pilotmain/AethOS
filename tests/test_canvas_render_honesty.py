# SPDX-License-Identifier: Apache-2.0
"""Canvas render honesty — claim must match a real structured view in the store."""

from __future__ import annotations

import re
from unittest.mock import patch

import pytest

from aethos_core.canvas.canvas_store import (
    clear_canvas_for_tests,
    get_canvas_state,
    is_structured_canvas_view_data,
    render_canvas_view,
)
from aethos_core.canvas.session_context import canvas_client_session_scope, clear_canvas_client_session_for_tests
from aethos_core.channels.session_alias import link_session_ids, resolve_canonical_session_id
from aethos_core.execution_brain.agent_runtime import (
    _CANVAS_SUCCESS_CLAIM_RX,
    _ensure_canvas_render,
    _try_deterministic_canvas_render,
    canvas_render_success_confirmation,
)

_CANVAS_PROMPT = "render a job timeline on the canvas"

_TIMELINE_DATA = {
    "events": [
        {"label": "Preflight", "status": "completed", "timestamp": "2026-06-01T10:00:00Z"},
        {"label": "Deploy", "status": "running", "timestamp": "2026-06-01T10:05:00Z"},
    ]
}

_REFUSAL_REPLY = (
    "The canvas rendering tool isn't available in this chat channel. "
    "I can't render a job timeline to the Canvas."
)


@pytest.fixture(autouse=True)
def _clean_canvas(tmp_path, monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_store_dir", str(tmp_path / "canvas"))
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()
    yield
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()


def test_surface_disabled_strips_false_success_claim(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", False)
    fake_success = canvas_render_success_confirmation("job_timeline")
    reply = _ensure_canvas_render(
        _CANVAS_PROMPT,
        session_id="sess-disabled",
        reply=fake_success,
        views_before=set(),
    )
    assert not _CANVAS_SUCCESS_CLAIM_RX.search(reply)
    assert "disabled" in reply.lower() or "CANVAS_SURFACE_ENABLED" in reply
    assert get_canvas_state(session_id="sess-disabled")["view_count"] == 0


def test_model_refusal_does_not_create_prose_card(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    reply = _ensure_canvas_render(
        _CANVAS_PROMPT,
        session_id="sess-refusal",
        reply=_REFUSAL_REPLY,
        views_before=set(),
    )
    assert get_canvas_state(session_id="sess-refusal")["view_count"] == 1
    assert reply == canvas_render_success_confirmation("job_timeline")


def test_prose_summary_rejected_by_store(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    out = render_canvas_view(
        session_id="sess-prose",
        view_type="job_timeline",
        title="Job Timeline",
        data={"summary": "model prose refusal text", "source": "agent_runtime"},
    )
    assert out["ok"] is False
    assert get_canvas_state(session_id="sess-prose")["view_count"] == 0


def test_structured_timeline_writes_and_confirms(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    out = render_canvas_view(
        session_id="sess-timeline",
        view_type="job_timeline",
        title="Job Timeline",
        data=_TIMELINE_DATA,
    )
    assert out["ok"] is True
    state = get_canvas_state(session_id="sess-timeline")
    assert state["view_count"] == 1
    assert state["views"][0]["data"]["events"]
    assert is_structured_canvas_view_data("job_timeline", state["views"][0]["data"])[0]

    reply = _ensure_canvas_render(
        _CANVAS_PROMPT,
        session_id="sess-timeline",
        reply=canvas_render_success_confirmation("job_timeline"),
        views_before=set(),
    )
    assert reply == canvas_render_success_confirmation("job_timeline")


def test_rerender_same_type_replaces_not_stacks(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    render_canvas_view(
        session_id="sess-dedup",
        view_type="job_timeline",
        title="Jobs v1",
        data={"events": [{"label": "A", "status": "done"}]},
    )
    render_canvas_view(
        session_id="sess-dedup",
        view_type="job_timeline",
        title="Jobs v2",
        data={"events": [{"label": "B", "status": "running"}]},
    )
    state = get_canvas_state(session_id="sess-dedup")
    assert state["view_count"] == 1
    assert state["views"][0]["title"] == "Jobs v2"


def test_claim_implies_structured_view_property(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    session_id = "sess-invariant"
    render_canvas_view(
        session_id=session_id,
        view_type="job_timeline",
        title="Jobs",
        data=_TIMELINE_DATA,
    )
    reply = _ensure_canvas_render(
        _CANVAS_PROMPT,
        session_id=session_id,
        reply=canvas_render_success_confirmation("job_timeline"),
        views_before=set(),
    )
    if _CANVAS_SUCCESS_CLAIM_RX.search(reply):
        views = get_canvas_state(session_id=session_id)["views"]
        assert views
        assert is_structured_canvas_view_data("job_timeline", views[0]["data"])[0]


def test_session_round_trip_client_and_canonical(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    client_sid = "sess-client-roundtrip"
    canonical = "sess-canonical-roundtrip"
    link_session_ids(session_ids=[client_sid, canonical], canonical_session_id=canonical)

    with canvas_client_session_scope(client_sid):
        out = render_canvas_view(
            session_id=canonical,
            view_type="job_timeline",
            title="Jobs",
            data={"events": [{"label": "step", "status": "ok"}]},
        )
    assert out["ok"] is True
    assert get_canvas_state(session_id=client_sid)["view_count"] >= 1
    assert get_canvas_state(session_id=canonical)["view_count"] >= 1
    assert get_canvas_state(session_id=resolve_canonical_session_id(client_sid))["view_count"] >= 1


def test_model_chat_text_without_tool_gets_deterministic_view(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    reply = _ensure_canvas_render(
        _CANVAS_PROMPT,
        session_id="sess-no-tool",
        reply="Here is a timeline summary in chat instead.",
        views_before=set(),
    )
    assert get_canvas_state(session_id="sess-no-tool")["view_count"] == 1
    assert reply == canvas_render_success_confirmation("job_timeline")


def test_deterministic_canvas_render_roundtrip(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    session_id = "sess-deterministic-timeline"
    assert _try_deterministic_canvas_render(_CANVAS_PROMPT, session_id=session_id) is True
    state = get_canvas_state(session_id=session_id)
    assert state["view_count"] == 1
    assert state["views"][0]["view_type"] == "job_timeline"

    reply = _ensure_canvas_render(
        _CANVAS_PROMPT,
        session_id=session_id,
        reply="Here is a timeline summary in chat instead.",
        views_before=set(),
    )
    assert reply == canvas_render_success_confirmation("job_timeline")


def test_fallback_render_failure_is_honest(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    fake = canvas_render_success_confirmation("job_timeline")
    with patch("aethos_core.canvas.canvas_store.render_canvas_view", return_value={"ok": False, "error": "unsupported_view_type"}):
        reply = _ensure_canvas_render(
            _CANVAS_PROMPT,
            session_id="sess-fail",
            reply=fake,
            views_before=set(),
        )
    assert not _CANVAS_SUCCESS_CLAIM_RX.search(reply)
    assert "couldn't render" in reply.lower()
    assert get_canvas_state(session_id="sess-fail")["view_count"] == 0


def test_empty_table_rows_rejected(monkeypatch):
    """A table whose rows are all-empty (renders as a wall of '—') must be rejected."""
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    out = render_canvas_view(
        session_id="sess-empty-table",
        view_type="table",
        title="Deployment Job Timeline",
        data={"columns": ["Provider", "Status"], "rows": [{}, {}, {}]},
    )
    assert out["ok"] is False
    assert out["error"] == "table_rows_all_empty"
    # header-only skeleton (columns, empty rows list) also rejected
    out2 = render_canvas_view(
        session_id="sess-empty-table",
        view_type="table",
        title="Skeleton",
        data={"columns": ["Provider", "Status"], "rows": []},
    )
    assert out2["ok"] is False
    assert out2["error"] == "table_rows_all_empty"


def test_empty_timeline_rows_rejected(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    out = render_canvas_view(
        session_id="sess-empty-tl",
        view_type="job_timeline",
        title="Jobs",
        data={"events": [{"label": "", "status": ""}, {}]},
    )
    assert out["ok"] is False
    assert out["error"] == "job_timeline_rows_all_empty"


def test_populated_table_still_accepted(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    out = render_canvas_view(
        session_id="sess-good-table",
        view_type="table",
        title="Deployments",
        data={
            "columns": ["Provider", "Status"],
            "rows": [{"Provider": "railway", "Status": "failed"}],
        },
    )
    assert out["ok"] is True


def test_empty_session_falls_back_to_latest_render(monkeypatch):
    """Canvas bound to a different/empty session still shows the latest render."""
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    render_canvas_view(
        session_id="sess-rendered-here",
        view_type="job_timeline",
        title="Jobs",
        data={"events": [{"label": "Deploy", "status": "success"}]},
    )
    # A completely different (empty) session — e.g. the Canvas in another window.
    state = get_canvas_state(session_id="sess-some-other-window")
    assert state["view_count"] == 1
    assert state["showing_latest_render"] is True
    assert state["resolved_session"] == "sess-rendered-here"
    assert state["views"][0]["data"]["events"][0]["label"] == "Deploy"


def test_session_with_own_views_does_not_fall_back(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    render_canvas_view(
        session_id="sess-A",
        view_type="job_timeline",
        title="A",
        data={"events": [{"label": "A", "status": "success"}]},
    )
    render_canvas_view(
        session_id="sess-B",
        view_type="job_timeline",
        title="B",
        data={"events": [{"label": "B", "status": "success"}]},
    )
    state = get_canvas_state(session_id="sess-A")
    assert state["showing_latest_render"] is False
    assert state["resolved_session"] == "sess-A"
    assert state["views"][0]["title"] == "A"


def test_include_fallback_false_counts_only_own_session(monkeypatch):
    """Verification path must count only the session's own views, not the tenant fallback —
    otherwise a prior render in another session makes before/after deltas falsely fail."""
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    # A prior render exists in another session.
    render_canvas_view(
        session_id="sess-prior",
        view_type="research_report",
        title="Prior",
        data={"sections": [{"title": "x", "content": "y"}]},
    )
    # The new turn's session starts genuinely empty for verification purposes.
    before = get_canvas_state(session_id="sess-new-turn", include_fallback=False)
    assert before["view_count"] == 0
    assert before["showing_latest_render"] is False
    # (with fallback it WOULD show the prior render)
    assert get_canvas_state(session_id="sess-new-turn", include_fallback=True)["view_count"] == 1
    # Now this session renders → exact count increases 0 → 1.
    render_canvas_view(
        session_id="sess-new-turn",
        view_type="research_report",
        title="New",
        data={"sections": [{"title": "a", "content": "b"}]},
    )
    after = get_canvas_state(session_id="sess-new-turn", include_fallback=False)
    assert after["view_count"] == 1
    assert after["view_count"] > before["view_count"]


def test_render_then_verify_succeeds_with_prior_other_session(monkeypatch):
    """End-to-end: agent_runtime verification reports success even when a prior render
    exists in a different session (the reported regression)."""
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_runtime import (
        _ensure_canvas_render,
        _canvas_view_ids,
        canvas_render_success_confirmation,
    )

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    render_canvas_view(
        session_id="sess-old",
        view_type="research_report",
        title="Old report",
        data={"sections": [{"title": "old", "content": "old"}]},
    )
    sid = "sess-fresh"
    before = _canvas_view_ids(sid)  # empty despite the prior render in another session
    assert before == set()
    render_canvas_view(
        session_id=sid,
        view_type="research_report",
        title="Killit Deploy — Blocker Report",
        data={"sections": [{"title": "Blocker 1", "content": "Railway project missing"}]},
    )
    reply = _ensure_canvas_render(
        "summarize the killit deploy blockers and render a report on the canvas",
        session_id=sid,
        reply=canvas_render_success_confirmation("research_report"),
        views_before=before,
    )
    assert reply == canvas_render_success_confirmation("research_report")
    assert "couldn't render" not in reply.lower()


def test_rerender_same_type_still_verified(monkeypatch):
    """Re-rendering the same view type (replace-in-place) must still verify as a render —
    count stays 1 but the view id changes, so id-set verification catches it."""
    from aethos_core.config import get_settings
    from aethos_core.execution_brain.agent_runtime import (
        _ensure_canvas_render,
        _canvas_view_ids,
        canvas_render_success_confirmation,
    )

    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    sid = "sess-rerender"
    # First markdown render exists.
    render_canvas_view(session_id=sid, view_type="markdown", title="v1", data={"content": "first"})
    before = _canvas_view_ids(sid)
    assert len(before) == 1
    # Second markdown render replaces in place (count stays 1, id changes).
    render_canvas_view(session_id=sid, view_type="markdown", title="v2", data={"content": "second"})
    reply = _ensure_canvas_render(
        "render a markdown checklist on the canvas",
        session_id=sid,
        reply=canvas_render_success_confirmation("markdown"),
        views_before=before,
    )
    assert reply == canvas_render_success_confirmation("markdown")
    assert "couldn't render" not in reply.lower()
