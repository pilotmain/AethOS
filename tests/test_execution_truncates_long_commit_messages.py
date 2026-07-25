# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_formatting import truncate_text


def test_execution_truncates_long_commit_messages():
    long_msg = "feat: " + "x" * 200
    out = truncate_text(long_msg, limit=120)
    assert len(out) <= 121
    assert out.endswith("…")
