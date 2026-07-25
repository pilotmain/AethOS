# SPDX-License-Identifier: Apache-2.0
"""§Slice 0 — document corrected §End gate #1 (source only, no docs/*.md)."""

from __future__ import annotations

import subprocess


def test_forbidden_codenames_gate_source_only_empty():
    cmd = [
        "grep",
        "-rinE",
        "odysseus|openclaw|clawhub|exfoliate|paperclip|earendil|\\bpi-coding\\b|tongyi|llmfit|opencode",
        "aethos_core",
        "web",
        "--include=*.py",
        "--include=*.ts",
        "--include=*.tsx",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = [ln for ln in proc.stdout.splitlines() if "node_modules" not in ln]
    assert not lines
