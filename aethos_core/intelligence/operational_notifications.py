# SPDX-License-Identifier: Apache-2.0
"""Operational notifications — severity-based, deduplicated, bounded."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root


_COOLDOWN_SEC = 3600.0
_SEVERITY_MIN = {"high": 0, "medium": 1, "low": 2}


def _state_path():
    return agent_artifacts_root() / "operational_notification_state.json"


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.is_file():
        return {"sent": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sent": {}}


def _save_state(data: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def notify_operational_recommendations(
    recommendations: list[dict[str, Any]],
    *,
    channel: str = "telegram",
) -> dict[str, Any]:
    """Send bounded notifications for high/medium recommendations — no spam."""
    sent: list[str] = []
    skipped: list[str] = []
    for rec in recommendations:
        severity = str(rec.get("severity") or "low")
        if _SEVERITY_MIN.get(severity, 99) > _SEVERITY_MIN["medium"]:
            skipped.append(str(rec.get("recommendation_id")))
            continue
        key = f"{rec.get('kind')}:{rec.get('suggested_action')}"
        if not _should_notify(key, severity=severity):
            skipped.append(str(rec.get("recommendation_id")))
            continue
        message = _format_message(rec)
        if _dispatch(channel, message):
            sent.append(str(rec.get("recommendation_id")))
            _mark_sent(key)
    return {"ok": True, "sent": sent, "skipped": skipped, "channel": channel}


def _should_notify(fingerprint: str, *, severity: str) -> bool:
    state = _load_state()
    sent = dict(state.get("sent") or {})
    prev = sent.get(fingerprint)
    if not prev:
        return True
    cooldown = _COOLDOWN_SEC if severity != "high" else _COOLDOWN_SEC / 2
    return time() - float(prev.get("at") or 0) >= cooldown


def _mark_sent(fingerprint: str) -> None:
    state = _load_state()
    sent = dict(state.get("sent") or {})
    sent[fingerprint] = {"at": time()}
    state["sent"] = sent
    _save_state(state)


def _format_message(rec: dict[str, Any]) -> str:
    observed = rec.get("observed") or []
    lines = [
        "AethOS observed operational signals.",
        f"Severity: {str(rec.get('severity') or 'medium').upper()} · Confidence: {rec.get('confidence')}",
        "",
        "Observed:",
    ]
    for item in observed[:3]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            f"Suggested: {rec.get('suggested_action')}",
            "No actions taken automatically.",
            "Review in Mission Control → Operational Intelligence.",
        ]
    )
    return "\n".join(lines)


def _dispatch(channel: str, message: str) -> bool:
    if channel != "telegram":
        return False
    try:
        from aethos_core.channels.dispatch import dispatch_job_event
        from aethos_core.channels.session_identity import external_chat_id_from_session
        from aethos_core.channels.telegram.telegram_runtime import telegram_configured

        if not telegram_configured():
            return False
        if not external_chat_id_from_session("operational_runtime"):
            return False
        dispatch_job_event(session_id="operational_runtime", message=message[:3500])
        return True
    except Exception:
        return False


def clear_notification_state_for_tests() -> None:
    path = _state_path()
    if path.is_file():
        path.unlink()
