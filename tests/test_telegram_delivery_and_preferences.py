# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.channels.telegram.telegram_delivery import clear_for_tests, deliver_message, queue_snapshot
from aethos_core.channels.telegram.telegram_preferences import (
    clear_for_tests as clear_prefs,
    get_notify_mode,
    set_default_mode,
)


def test_delivery_retries_then_queues():
    clear_for_tests()
    attempts = {"n": 0}

    def flaky_api(**kwargs):
        attempts["n"] += 1
        if attempts["n"] < 3:
            return {"ok": False, "detail": "Too Many Requests", "status_code": 429}
        return {"ok": True, "detail": "ok", "status_code": 200}

    out = deliver_message(token="t", chat_id="1", text="hi", bot_api_fn=flaky_api)
    assert out.get("ok") is True
    assert attempts["n"] == 3


def test_delivery_queues_on_persistent_failure():
    clear_for_tests()

    def fail_api(**kwargs):
        return {"ok": False, "detail": "Bad Request", "status_code": 400}

    out = deliver_message(token="t", chat_id="1", text="hello", bot_api_fn=fail_api)
    assert out.get("ok") is False
    assert "Bad Request" in str(out.get("detail") or "")
    assert queue_snapshot()["queued"] == 1


def test_notification_mode_completion_only():
    clear_prefs()
    set_default_mode("completion_only")
    assert get_notify_mode() == "completion_only"
