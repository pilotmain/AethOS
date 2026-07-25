# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.execution_permissions import (
    actions_for_operation,
    assert_readonly_action,
    is_mutating_operation,
)


def test_mutating_operations_blocked():
    assert is_mutating_operation("redeploy")
    assert is_mutating_operation("set_env_var")
    assert not is_mutating_operation("check_logs")


def test_local_actions_are_readonly():
    actions = actions_for_operation("local_workspace_fix", provider="local")
    assert "git_status" in actions
    for a in actions:
        assert_readonly_action(a)


def test_disallowed_action_raises():
    try:
        assert_readonly_action("redeploy")
        assert False
    except PermissionError:
        pass
