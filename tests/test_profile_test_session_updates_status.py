# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus
from aethos_core.runtime.vercel_readonly_inspector import ReadonlyInspectionOutcome, run_profile_session_check
from tests.browser_test_utils import use_mock_browser_driver


def test_session_test_marks_expired_on_login_wall():
    use_mock_browser_driver(installed=True)
    browser_profile_store.clear_all_for_tests()
    pid = browser_profile_store.save_from_session(
        session_id="s1",
        site="vercel.com",
        storage_state={},
    ).profile_id

    def fake_inspection(**kwargs):
        return ReadonlyInspectionOutcome(
            full_result="# R",
            summary="login required",
            preview="login",
            profile_status="active",
            used_saved_session=True,
            profile_id=pid,
            project_names=[],
            login_wall=True,
        )

    with patch(
        "aethos_core.runtime.vercel_readonly_inspector.run_readonly_inspection",
        fake_inspection,
    ):
        result = run_profile_session_check(pid)
    assert result["ok"] is False
    assert browser_profile_store.get(pid).status == BrowserProfileStatus.EXPIRED
