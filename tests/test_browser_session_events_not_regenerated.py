# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_lifecycle import BrowserSessionStatus
from aethos_core.runtime.browser_session import BrowserSession, browser_session_store


def test_emit_idempotent_same_event_type():
    session = BrowserSession(
        id="bsess-dedup",
        target="vercel.com",
        url="https://vercel.com",
        status=BrowserSessionStatus.RUNNING,
    )
    browser_session_store._sessions[session.id] = session
    try:
        e1 = browser_session_store._emit(session, "session_running")
        e2 = browser_session_store._emit(session, "session_running")
        assert e1.id == e2.id
        running = [e for e in browser_session_store._events if e.event_type == "session_running"]
        assert len(running) == 1
    finally:
        browser_session_store._sessions.pop(session.id, None)
        browser_session_store._events[:] = [
            e for e in browser_session_store._events if e.session_id != session.id
        ]
