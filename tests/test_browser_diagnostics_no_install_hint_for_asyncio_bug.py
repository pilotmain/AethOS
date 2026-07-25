# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_diagnostics import normalize_browser_diagnostics, runtime_not_ready_message


def test_no_install_hint_for_asyncio_bug():
    norm = normalize_browser_diagnostics(
        {
            "playwright_package": "installed",
            "launch_probe_error": "Sync API inside the asyncio loop",
            "runtime_error_kind": "asyncio_sync_api_misuse",
            "execution_ready": False,
        }
    )
    msg = runtime_not_ready_message(norm)
    assert "do not run" in msg.lower()
    assert "runtime bug" in msg.lower() or "aethos runtime" in msg.lower()
    assert norm["recommended_install_commands"] == []
