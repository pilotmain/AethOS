# SPDX-License-Identifier: Apache-2.0
"""Portable installer contract tests; these do not install dependencies."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_bash_installer_syntax_and_help(tmp_path):
    installer = ROOT / "install.sh"
    subprocess.run(["bash", "-n", str(installer)], check=True)
    result = subprocess.run(
        ["bash", str(installer), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--resume" in result.stdout
    assert "--status" in result.stdout
    assert "--help-step STEP" in result.stdout

    env = {**os.environ, "AETHOS_STATE_DIR": str(tmp_path / "state"), "NO_COLOR": "1"}
    status = subprocess.run(
        ["bash", str(installer), "--status"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert "preflight" in status.stdout
    assert "pending" in status.stdout
    assert "Continue:" in status.stdout


def test_runtime_launcher_syntax_and_help():
    launcher = ROOT / "run.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    result = subprocess.run(
        ["bash", str(launcher), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--api-only" in result.stdout
    assert "--web-only" in result.stdout


def test_windows_scripts_expose_equivalent_controls():
    install = (ROOT / "install.ps1").read_text(encoding="utf-8")
    run = (ROOT / "run.ps1").read_text(encoding="utf-8")
    for control in ("$Resume", "$Status", "$From", "$HelpStep", "$SkipWeb"):
        assert control in install
    assert "npm ci" in (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
    assert "$ApiOnly" in run
    assert "$WebOnly" in run


def test_installers_pin_project_dependencies_and_support_stream_resume():
    bash = (ROOT / "install.sh").read_text(encoding="utf-8")
    powershell = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert "pip install -c requirements.lock" in bash
    assert '"install", "-c", "requirements.lock"' in powershell
    assert "bash -s -- --resume" in bash
    assert "scriptblock]::Create" in powershell


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="PowerShell is not installed")
def test_windows_scripts_parse_in_powershell():
    subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(ROOT / "install.ps1"), "-Help"],
        check=True,
    )
    subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(ROOT / "run.ps1"), "-Help"],
        check=True,
    )
