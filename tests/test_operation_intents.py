# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.intents import infer_operation_preflight_intent


def test_redeploy_intent():
    out = infer_operation_preflight_intent("redeploy quotepilot")
    assert out is not None
    title, job_type, params = out
    assert job_type == "operation_preflight"
    assert params["operation_type"] == "redeploy"


def test_logs_intent():
    out = infer_operation_preflight_intent("check logs for talking-avatar-agent")
    assert out is not None
    _, job_type, params = out
    assert job_type == "operation_preflight"
    assert params["operation_type"] == "check_logs"


def test_down_intent():
    out = infer_operation_preflight_intent("why is talking-avatar-agent down?")
    assert out is not None
    assert out[1] == "operation_preflight"


def test_why_did_fail_intent():
    out = infer_operation_preflight_intent("why did talking-avatar-agent fail")
    assert out is not None
    assert out[1] == "operation_preflight"
    assert out[2]["operation_type"] == "why_down"
    assert "talking-avatar-agent" in out[2]["target_hints"]

def test_env_var_intent():
    out = infer_operation_preflight_intent("set NEXT_PUBLIC_API_URL for quotepilot")
    assert out is not None
    assert out[1] == "operation_preflight"


def test_local_workspace_intent():
    out = infer_operation_preflight_intent("check the local workspace code and fix issues")
    assert out is not None
    assert out[1] == "local_workspace_fix_preflight"
    assert out[2]["provider"] == "local"


def test_deferred_cloud_intent():
    out = infer_operation_preflight_intent("restart my app on aws")
    assert out is not None
    assert out[1] == "operation_preflight"
    assert out[2]["provider"] == "aws"


def test_railway_restart_routes_to_railway_preflight_not_deferred():
    out = infer_operation_preflight_intent("restart my app on railway")
    assert out is not None
    assert out[1] == "operation_preflight"
    assert out[2]["provider"] == "railway"
