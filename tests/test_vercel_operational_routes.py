# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.testclient import TestClient

from aethos_core.runtime.browser_intents import classify_operational_intent
from aethos_core.runtime.vercel_readonly_jobs import infer_vercel_readonly_job


def test_show_my_vercel_apps_is_inspection():
    text = "show my Vercel apps"
    assert classify_operational_intent(text) == "vercel_inspection"
    assert infer_vercel_readonly_job(text) is not None


def test_saved_session_follow_up_is_inspection():
    text = "give me the list of services deployed in vercel using saved session"
    assert classify_operational_intent(text) == "vercel_inspection"
    assert infer_vercel_readonly_job(text) is not None


def test_chat_show_apps_without_profile():
    from aethos_core.api.main import app
    from aethos_core.runtime.browser_profile_store import browser_profile_store
    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    browser_profile_store.clear_all_for_tests()
    reset_credential_vault_for_tests()
    from aethos_core.security.credential_vault import get_credential_vault

    get_credential_vault().clear_all_for_tests()
    reset_credential_vault_for_tests()
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        get_settings()
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "show my Vercel apps", "session_id": "route-apps"},
        )
        body = r.json()
        assert body["used_llm"] is False
        reply = body["reply"].lower()
        assert "inventory failed" in reply or "token" in reply
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        reset_credential_vault_for_tests()
        get_credential_vault().clear_all_for_tests()
        reset_credential_vault_for_tests()
        from aethos_core.config import get_settings

        get_settings.cache_clear()


def test_chat_open_supervised_session_proposes_browser():
    from aethos_core.api.main import app

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        get_settings()
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "Open supervised Vercel session", "session_id": "route-open"},
        )
        body = r.json()
        assert body["used_llm"] is False
        assert (body.get("meta") or {}).get("proposed_action_type") == "browser_navigation_plan"
        assert "npm i -g vercel" not in body["reply"].lower()
        assert "approval" in body["reply"].lower() or "browser job proposed" in body["reply"].lower()
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from aethos_core.config import get_settings

        get_settings.cache_clear()
