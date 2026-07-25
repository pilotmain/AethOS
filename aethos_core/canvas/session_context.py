# SPDX-License-Identifier: Apache-2.0
"""Live chat session id for canvas writes — matches the web client's session_id."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_canvas_client_session: ContextVar[str | None] = ContextVar("canvas_client_session", default=None)


def get_canvas_client_session() -> str | None:
    return _canvas_client_session.get()


def canvas_write_session_id(fallback: str = "default") -> str:
    """Session key for canvas_store writes — prefers the live chat client id."""
    bound = _canvas_client_session.get()
    raw = (bound or fallback or "default").strip() or "default"
    return raw[:64]


@contextmanager
def canvas_client_session_scope(session_id: str) -> Iterator[str]:
    """Bind the operator's live chat session id for canvas_render during a turn."""
    sid = (session_id or "default").strip()[:64] or "default"
    token = _canvas_client_session.set(sid)
    try:
        yield sid
    finally:
        _canvas_client_session.reset(token)


def clear_canvas_client_session_for_tests() -> None:
    _canvas_client_session.set(None)
