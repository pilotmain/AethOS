# SPDX-License-Identifier: Apache-2.0
"""Slack Bot API transport."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def send_slack_message(*, token: str, channel_id: str, text: str) -> bool:
    if not token.strip() or not channel_id.strip() or not text.strip():
        return False
    payload = json.dumps({"channel": channel_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Authorization": f"Bearer {token.strip()}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return bool(body.get("ok"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return False


def test_slack_connection(token: str) -> dict[str, Any]:
    if not token.strip():
        return {"ok": False, "detail": "Slack bot token is empty."}
    req = urllib.request.Request(
        "https://slack.com/api/auth.test",
        headers={"Authorization": f"Bearer {token.strip()}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("ok"):
            return {"ok": False, "detail": str(data.get("error") or "auth.test failed")}
        return {"ok": True, "detail": f"Slack workspace verified ({data.get('team', '')}).", "team": data.get("team")}
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        return {"ok": False, "detail": str(exc)}
