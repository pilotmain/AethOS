# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_jobs_events_never_touch_browser_runtime():
    from aethos_core.api.main import app
    from aethos_core.runtime.authority import authority

    job = authority.create_job(
        title="Logs preflight",
        job_type="vercel_logs_preflight",
        params={"user_request": "check logs for talking-avatar-agent"},
        source="test",
        session_id="evt-test",
        auto_run=False,
    )
    client = TestClient(app)
    with patch("aethos_core.runtime.browser_diagnostics.probe_playwright_on_browser_thread") as probe:
        with patch("aethos_core.runtime.browser_diagnostics.validate_browser_runtime_for_execution") as validate:
            r = client.get(f"/api/v1/jobs/events?ids={job.id}")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("events"), list)
    probe.assert_not_called()
    validate.assert_not_called()


def test_actions_events_never_touch_browser_runtime():
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch("aethos_core.runtime.browser_diagnostics.probe_playwright_on_browser_thread") as probe:
        r = client.get("/api/v1/actions/events?ids=act-doesnotmatter")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("events"), list)
    probe.assert_not_called()


def test_browser_session_events_never_touch_browser_runtime():
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch("aethos_core.runtime.browser_diagnostics.probe_playwright_on_browser_thread") as probe:
        r = client.get("/api/v1/browser/sessions/events?ids=bsess-doesnotmatter")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("events"), list)
    probe.assert_not_called()
