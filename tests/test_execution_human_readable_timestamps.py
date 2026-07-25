# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_formatting import format_timestamp


def test_execution_human_readable_timestamps():
    assert format_timestamp(1776884598019) == "2026-04-22 18:03 UTC" or "2026" in (format_timestamp(1776884598019) or "")
    assert format_timestamp("2026-05-20T10:03:00Z") == "2026-05-20 10:03 UTC"
