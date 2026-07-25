# SPDX-License-Identifier: Apache-2.0
"""Interruption policy — notification suppression and cooldowns."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.presence.paths import presence_memory_root

_COOLDOWN_SEC = 1800.0
_URGENT_COOLDOWN_SEC = 600.0


def _state_path():
    return presence_memory_root() / "interruption_state.json"


def _load() -> dict[str, Any]:
    path = _state_path()
    if not path.is_file():
        return {"sent": {}, "suppressed": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sent": {}, "suppressed": 0}


def _save(data: dict[str, Any]) -> None:
    _state_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def should_notify(*, fingerprint: str, priority: str, focus_mode: str | None = None) -> bool:
    if focus_mode == "engineering_debug":
        if priority in ("passive", "elevated"):
            _record_suppressed()
            return False
    state = _load()
    sent = dict(state.get("sent") or {})
    prev = sent.get(fingerprint)
    cooldown = _URGENT_COOLDOWN_SEC if priority in ("urgent", "critical") else _COOLDOWN_SEC
    if prev and time() - float(prev.get("at") or 0) < cooldown:
        _record_suppressed()
        return False
    return True


def mark_notified(fingerprint: str) -> None:
    state = _load()
    sent = dict(state.get("sent") or {})
    sent[fingerprint] = {"at": time()}
    state["sent"] = sent
    _save(state)


def _record_suppressed() -> None:
    state = _load()
    state["suppressed"] = int(state.get("suppressed") or 0) + 1
    _save(state)


def interruption_stats() -> dict[str, Any]:
    return _load()


def clear_interruption_state_for_tests() -> None:
    path = _state_path()
    if path.is_file():
        path.unlink()
