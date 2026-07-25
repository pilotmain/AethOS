# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.testclient import TestClient

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import PersistenceMode
from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver
from tests.job_test_utils import drain_job_executor


def test_inventory_chat_returns_200_with_job_not_connection_drop():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=True)
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    browser_profile_store.clear_all_for_tests()
    browser_profile_store.save_from_session(
        session_id="bsess-inv",
        site="vercel.com",
        storage_state={"cookies": [{"name": "s", "value": "1", "domain": ".vercel.com", "path": "/"}]},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "show my Vercel apps", "session_id": "inv-never-drop"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "connection dropped" not in body["reply"].lower()
        assert "created tracked job" in body["reply"].lower()
        job_id = (body.get("meta") or {}).get("proposed_job_id")
        assert job_id
        drain_job_executor()
    finally:
        reset_browser_test_state()
