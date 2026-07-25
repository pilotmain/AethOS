# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

from aethos_core.research.providers.searxng_provider import SearxngResearchProvider


@patch("aethos_core.research.providers.searxng_provider.httpx.Client")
def test_searxng_search_parses_results(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"title": "AethOS", "url": "https://example.com/aethos", "content": "Agent platform"},
        ]
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    provider = SearxngResearchProvider("http://127.0.0.1:8080")
    result = provider.search("aethos agent", max_results=3)
    assert result.ok
    assert result.provider == "searxng"
    assert len(result.results) == 1
    assert result.results[0].title == "AethOS"
