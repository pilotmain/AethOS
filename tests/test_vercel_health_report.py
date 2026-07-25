# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.vercel_health import build_vercel_health_report


def test_vercel_health_report_has_sources_and_no_secrets():
    report = build_vercel_health_report(mode="public", user_request="check Vercel service health")
    assert report.full_result
    assert "Vercel" in report.full_result
    assert "No credentials" in report.full_result
    assert len(report.sources) >= 2
    types = {s["type"] for s in report.sources}
    assert "public_status" in types
    assert "cli" in types
    blob = str(report.sources) + report.full_result
    assert "api_key" not in blob.lower()
    assert "password" not in blob.lower()
    assert "sk-ant-" not in blob


def test_public_status_fetch_can_be_mocked():
    from unittest.mock import MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": {"indicator": "none", "description": "All Systems Operational"},
    }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            return mock_resp

    with patch("httpx.Client", FakeClient):
        report = build_vercel_health_report(mode="public")
    public = [s for s in report.sources if s["type"] == "public_status"][0]
    assert public["available"] is True
