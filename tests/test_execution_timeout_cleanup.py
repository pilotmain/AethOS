# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.operations.execution.execution_runner import _truncate


def test_output_truncation():
    big = "x" * 20_000
    out = _truncate(big, limit=100)
    assert len(out) < 200
    assert "truncated" in out


def test_git_command_rejected():
    from aethos_core.operations.execution.execution_runner import _run_git
    from pathlib import Path

    with pytest.raises(PermissionError):
        _run_git(["git", "push"], cwd=Path("."))
