# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.preflight_summary import chat_summary_for_preflight
from aethos_core.runtime.job_artifacts import chat_completion_event_message


def test_blocked_preflight_summary_does_not_invite_approval():
    preflight = OperationPreflight(
        operation_id="op-1",
        provider="vercel",
        operation_type="check_logs",
        target_name="talking-avatar-agent",
        target_status="blocked_by_browser_runtime",
        risk_level="low",
        required_approval=True,
        execution_enabled=False,
        preflight_status="blocked",
        proposed_steps=["Read deployment logs"],
        blockers=["Browser runtime is not ready"],
        missing_information=[],
        next_action="Fix browser runtime",
        current_state={"profile_id": "bprof-1"},
    )
    summary = chat_summary_for_preflight(preflight, user_request="check logs")
    assert "approve execution" not in summary.lower()
    assert "blocked until browser runtime is healthy" in summary.lower()


def test_blocked_preflight_completion_message():
    msg = chat_completion_event_message(
        "vercel_logs_preflight",
        "Logs preflight",
        "Preflight summary",
        fallback=False,
        preflight_status="blocked",
    )
    assert "approve execution" not in msg.lower()
    assert "blocked until browser runtime is healthy" in msg.lower()
