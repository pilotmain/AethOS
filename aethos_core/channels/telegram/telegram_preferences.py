# SPDX-License-Identifier: Apache-2.0
"""Telegram notification preferences — calm by default."""

from __future__ import annotations

from typing import Literal

NotifyMode = Literal["calm", "verbose", "completion_only"]

_DEFAULT_MODE: NotifyMode = "calm"
_session_modes: dict[str, NotifyMode] = {}


def get_notify_mode(*, session_id: str | None = None) -> NotifyMode:
    if session_id and session_id in _session_modes:
        return _session_modes[session_id]
    return _DEFAULT_MODE


def set_default_mode(mode: NotifyMode) -> None:
    global _DEFAULT_MODE
    _DEFAULT_MODE = mode


def set_session_mode(session_id: str, mode: NotifyMode) -> None:
    _session_modes[session_id[:64]] = mode


def preferences_snapshot() -> dict[str, str | dict[str, str]]:
    return {
        "default_mode": _DEFAULT_MODE,
        "session_modes": dict(_session_modes),
    }


def clear_for_tests() -> None:
    global _DEFAULT_MODE
    _DEFAULT_MODE = "calm"
    _session_modes.clear()
