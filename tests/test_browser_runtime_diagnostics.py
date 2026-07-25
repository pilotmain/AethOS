# SPDX-License-Identifier: Apache-2.0

import sys

from fastapi.testclient import TestClient


def test_browser_diagnostics_endpoint_shape():
    from aethos_core.api.main import app

    client = TestClient(app)
    body = client.get("/api/v1/browser/diagnostics").json()
    diag = body["diagnostics"]
    assert diag["python_executable"] == sys.executable
    assert diag["playwright_package"] in {"installed", "missing"}
    assert diag["chromium_browser"] in {"installed", "missing"}
    assert "recommended_install_commands" in diag
    assert "failure_kind" in diag
    if diag["playwright_package"] != "installed":
        assert len(diag["recommended_install_commands"]) >= 1
        assert sys.executable in diag["recommended_install_commands"][0]
    if diag.get("install_hint"):
        assert sys.executable in diag["install_hint"]


def test_status_includes_diagnostics_block():
    from aethos_core.api.main import app

    client = TestClient(app)
    body = client.get("/api/v1/browser/status").json()
    assert "diagnostics" in body
    assert body["diagnostics"]["python_executable"] == sys.executable


def test_install_commands_use_runtime_python():
    from aethos_core.runtime.browser_diagnostics import recommended_install_commands

    cmds = recommended_install_commands()
    assert any(sys.executable in c for c in cmds)
