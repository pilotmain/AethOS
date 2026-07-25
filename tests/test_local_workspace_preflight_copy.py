# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.preflight import run_operation_preflight


def test_local_preflight_summary_no_vercel_workspace():
    outcome = run_operation_preflight(
        job_type="local_workspace_fix_preflight",
        params={
            "user_request": "check the local workspace code and fix issues",
            "provider": "local",
            "operation_type": "local_workspace_fix",
            "target_hints": [],
        },
    )
    summary = outcome.summary.lower()
    assert "vercel workspace" not in summary
    assert "local workspace preflight" in summary
