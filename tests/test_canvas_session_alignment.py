"""Canvas write/read must use the live chat client session id (not canonical alias only)."""

import threading
from contextvars import copy_context

from aethos_core.canvas.canvas_store import clear_canvas_for_tests, get_canvas_state, render_canvas_view
from aethos_core.canvas.session_context import (
    canvas_client_session_scope,
    canvas_write_session_id,
    clear_canvas_client_session_for_tests,
)
from aethos_core.channels.session_alias import link_session_ids


def test_canvas_write_uses_client_session_not_canonical_alias(tmp_path, monkeypatch) -> None:
    from aethos_core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "canvas_store_dir", str(tmp_path / "canvas"))
    monkeypatch.setattr(settings, "canvas_surface_enabled", True)
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()

    client_sid = "sess-ui-live-chat"
    canonical = "sess-canonical-linked"
    link_session_ids(session_ids=[client_sid, canonical], canonical_session_id=canonical)

    with canvas_client_session_scope(client_sid):
        out = render_canvas_view(
            session_id=canonical,
            view_type="job_timeline",
            title="Jobs",
            data={"rows": [1]},
        )

    assert out["ok"] is True
    assert out["session_id"] == client_sid
    assert get_canvas_state(session_id=client_sid)["view_count"] == 1
    assert get_canvas_state(session_id=canonical)["view_count"] == 1


def test_canvas_read_merges_linked_session_aliases(tmp_path, monkeypatch) -> None:
    from aethos_core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "canvas_store_dir", str(tmp_path / "canvas2"))
    monkeypatch.setattr(settings, "canvas_surface_enabled", True)
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()

    a = "sess-merge-a"
    b = "sess-merge-b"
    link_session_ids(session_ids=[a, b], canonical_session_id=a)

    with canvas_client_session_scope(a):
        render_canvas_view(session_id=a, view_type="status", title="A", data={"items": [{"name": "a", "status": "ok"}]})

    state = get_canvas_state(session_id=b)
    assert state["view_count"] == 1
    assert state["views"][0]["title"] == "A"


def test_canvas_write_read_same_id_without_alias_link(tmp_path, monkeypatch) -> None:
    """Unlinked client id vs canonical fallback — dual-write must bridge the gap."""
    from aethos_core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "canvas_store_dir", str(tmp_path / "canvas3"))
    monkeypatch.setattr(settings, "canvas_surface_enabled", True)
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()

    client_sid = "sess-x9tk9y71"
    canonical_sid = "sess-canonical-only"

    with canvas_client_session_scope(client_sid):
        out = render_canvas_view(
            session_id=canonical_sid,
            view_type="job_timeline",
            title="Timeline",
            data={"events": [{"label": "start", "status": "running"}]},
        )

    assert out["session_id"] == client_sid
    read = get_canvas_state(session_id=client_sid)
    assert read["view_count"] == 1
    assert read["session_id"] == client_sid


def test_canvas_client_session_propagates_into_worker_thread() -> None:
    clear_canvas_client_session_for_tests()
    client = "sess-worker-client"
    seen: dict[str, str] = {}

    def worker() -> None:
        seen["sid"] = canvas_write_session_id("sess-canonical-fallback")

    with canvas_client_session_scope(client):
        ctx = copy_context()
        thread = threading.Thread(target=lambda: ctx.run(worker))
        thread.start()
        thread.join()

    assert seen["sid"] == client
