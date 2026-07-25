# SPDX-License-Identifier: Apache-2.0
"""Chat threads must not leak across tenants."""

from __future__ import annotations

from aethos_core.chat.chat_thread_store import get_chat_thread, upsert_chat_thread
from aethos_core.tenancy import tenant_scope


def test_chat_threads_isolated_by_tenant(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with tenant_scope("user-a@example.com"):
        upsert_chat_thread(
            session_id="sess-shared-id",
            title="User A private",
            messages=[{"id": "1", "role": "user", "content": "secret from A"}],
        )

    with tenant_scope("user-b@example.com"):
        row = get_chat_thread("sess-shared-id")
        assert row is None

    with tenant_scope("user-b@example.com"):
        upsert_chat_thread(
            session_id="sess-shared-id",
            title="User B private",
            messages=[{"id": "1", "role": "user", "content": "secret from B"}],
        )
        row_b = get_chat_thread("sess-shared-id")
        assert row_b is not None
        assert row_b["thread"]["title"] == "User B private"

    with tenant_scope("user-a@example.com"):
        row_a = get_chat_thread("sess-shared-id")
        assert row_a is not None
        assert row_a["thread"]["title"] == "User A private"

    get_settings.cache_clear()
