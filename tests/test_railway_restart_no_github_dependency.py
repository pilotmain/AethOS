# SPDX-License-Identifier: Apache-2.0
"""Railway restart must not depend on GitHub source binding."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.provider_topology.binding_verifier import verify_source_binding
from aethos_core.provider_topology.operation_requirement_policy import requires_source_binding


def test_restart_does_not_require_github_binding():
    assert requires_source_binding("railway", "restart") is False


def test_restart_allowed_with_no_github_installation():
    with patch("aethos_core.provider_topology.binding_verifier._accessible_github_repos", return_value=[]):
        result = verify_source_binding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            operation_type="restart",
        )
    assert result.ok is True
    assert "not required" in result.message.lower()


def test_restart_does_not_call_github_access_verifier():
    with patch("aethos_core.provider_topology.github_access_verifier.verify_github_repo_access") as verify:
        with patch("aethos_core.provider_topology.binding_verifier._accessible_github_repos", return_value=None):
            result = verify_source_binding(
                provider="railway",
                project="adequate-luck",
                environment="production",
                service_name="speakglobal-ai",
                operation_type="restart",
            )
    verify.assert_not_called()
    assert result.ok is True


def test_redeploy_can_require_source_binding():
    assert requires_source_binding("railway", "redeploy", execution_mode="deploy_from_source") is True
    assert requires_source_binding("railway", "redeploy", execution_mode="api") is False


def test_deploy_latest_requires_source_binding():
    assert requires_source_binding("railway", "deploy") is True
    assert requires_source_binding("railway", "deploy_latest") is True


def test_missing_source_binding_does_not_block_restart():
    with patch("aethos_core.provider_topology.binding_verifier._accessible_github_repos", return_value=[]):
        result = verify_source_binding(
            provider="railway",
            project="adequate-luck",
            environment="production",
            service_name="speakglobal-ai",
            operation_type="restart",
        )
    assert result.ok is True
