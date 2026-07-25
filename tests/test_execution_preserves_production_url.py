# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_formatting import normalize_production_url


def test_execution_preserves_production_url_normalization():
    assert normalize_production_url("talking-avatar-agent.vercel.app") == (
        "https://talking-avatar-agent.vercel.app"
    )
    assert normalize_production_url("https://example.com") == "https://example.com"
    assert normalize_production_url("") is None
