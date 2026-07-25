# SPDX-License-Identifier: Apache-2.0

import os

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state


def test_vercel_apps_prompt_without_profile_needs_session():
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
            json={
                "message": "tell me all my Vercel apps",
                "session_id": "p82-ro",
            },
        )
        body = r.json()
        reply = body["reply"].lower()
        assert body["used_llm"] is False
        assert "inventory failed" in reply or "token" in reply
        assert "enter your password" not in reply
        assert "provide your password" not in reply
        assert (body.get("meta") or {}).get("proposed_job_id") is None
    finally:
        reset_credential_vault_for_tests()
        get_credential_vault().clear_all_for_tests()
        reset_credential_vault_for_tests()
        reset_browser_test_state()


def test_vercel_readonly_job_with_saved_profile():
    from aethos_core.runtime.browser_profile_store import browser_profile_store
    from aethos_core.runtime.vercel_readonly_inspector import ReadonlyInspectionOutcome

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    browser_profile_store.clear_all_for_tests()
    from aethos_core.runtime.browser_profiles import PersistenceMode

    profile = browser_profile_store.save_from_session(
        session_id="bsess-save",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    )

    def fake_inspection(**kwargs):
        return ReadonlyInspectionOutcome(
            full_result="# Report\n\n- app-one\n",
            summary="Vercel projects inventory (read-only)",
            preview="Vercel projects inventory (read-only)",
            profile_status="active",
            used_saved_session=True,
            profile_id=kwargs.get("profile_id") or profile.profile_id,
            project_names=["app-one"],
            login_wall=False,
        )

    import aethos_core.runtime.vercel_readonly_inspector as insp_mod

    orig = insp_mod.run_readonly_inspection
    insp_mod.run_readonly_inspection = fake_inspection
    try:
        from aethos_core.config import get_settings
        from aethos_core.chat.vercel_readonly_prompts import create_vercel_readonly_job_reply
        from aethos_core.runtime.job_executor import job_executor
        from aethos_core.runtime.jobs import job_store

        get_settings.cache_clear()
        get_settings()
        handled = create_vercel_readonly_job_reply(
            "inspect my vercel account read-only using saved session",
            session_id="p82-job",
        )
        assert handled is not None
        body, _intent, meta = handled
        assert "job-" in body
        jid = meta["proposed_job_id"]
        while job_executor.drain_once_for_tests():
            pass
        job = job_store.get(jid)
        assert job is not None
        assert job.status.value == "completed"
        assert job.params.get("profile_id") == profile.profile_id
    finally:
        insp_mod.run_readonly_inspection = orig
        reset_browser_test_state()
