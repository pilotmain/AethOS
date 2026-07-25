# SPDX-License-Identifier: Apache-2.0
"""Railway read-only diagnostics run directly — no preflight approval job."""

from unittest.mock import patch

from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply, is_railway_readonly_direct_request
from aethos_core.operational_session.railway_readonly_executor import ReadonlyExecutionResult


def test_railway_deploy_env_matches_direct_read():
    assert is_railway_readonly_direct_request("check my Railway deployment and env config")


def test_deploy_killit_not_railway_readonly_lane():
    assert not is_railway_readonly_direct_request(
        "deploy killit to railway and set up the env vars"
    )


def test_show_railway_deployments_still_readonly():
    assert is_railway_readonly_direct_request("show railway deployment status")


@patch("aethos_core.chat.railway_readonly_prompts.resolve_railway_auth_for_chat")
@patch("aethos_core.operational_session.railway_readonly_executor.execute_railway_readonly")
@patch("aethos_core.operational_session.operational_readonly_goal.classify_readonly_goal")
@patch("aethos_core.operational_session.operational_session.load_operational_session")
@patch("aethos_core.operational_session.active_subject_resolver.resolve_active_subject")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_railway_direct_read_no_job_created(
    mock_checks,
    mock_subject,
    mock_session,
    mock_goal,
    mock_execute,
    mock_auth,
):
    mock_checks.return_value = {"required_env_vars": ["RAILWAY_API_TOKEN (validated)"]}
    mock_auth.return_value = {"credential_id": "cred-r", "block_reason": None}
    from aethos_core.operational_session.session_subject import SessionSubject

    mock_subject.return_value.subject = SessionSubject(provider="railway", subject_source="session")
    from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal

    mock_goal.return_value = ReadonlyGoal(operation="deployment_status", user_text="check railway deployment")
    mock_execute.return_value = ReadonlyExecutionResult(
        ok=True,
        reply="**Railway deployment status:**\n\n- aethos-api — healthy",
        operation="deployment_status",
    )

    out = create_railway_readonly_job_reply("check my Railway deployment and env", session_id="sess-rail")
    assert out is not None
    body, intent, meta = out
    assert intent == "railway_readonly_direct"
    assert meta.get("route_id") == "railway_readonly_direct"
    assert "deployment" in body.lower()
    assert "Created tracked" not in body
    assert "RAILWAY_API_TOKEN" in body
