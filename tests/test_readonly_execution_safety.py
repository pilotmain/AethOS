# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_permissions import (
    actions_for_operation,
    assert_readonly_action,
    is_mutating_operation,
)


def test_mutating_operations_blocked():
    assert is_mutating_operation("redeploy") is True
    assert actions_for_operation("redeploy", provider="vercel") == []


def test_readonly_actions_allowed():
    for action in actions_for_operation("list_domains", provider="vercel"):
        assert_readonly_action(action)


def test_why_down_uses_api_deployments_not_mutations():
    actions = actions_for_operation("why_down", provider="vercel")
    assert "vercel_api_deployments" in actions
    assert "redeploy" not in actions
