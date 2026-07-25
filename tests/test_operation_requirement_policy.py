# SPDX-License-Identifier: Apache-2.0
"""Operation requirement policy tests."""

from __future__ import annotations

from aethos_core.provider_topology.operation_requirement_policy import requires_source_binding


def test_railway_restart_does_not_require_github_binding():
    assert requires_source_binding("railway", "restart") is False


def test_railway_deploy_requires_source_binding():
    assert requires_source_binding("railway", "deploy") is True
    assert requires_source_binding("railway", "deploy_from_git") is True


def test_railway_redeploy_default_does_not_require_binding():
    assert requires_source_binding("railway", "redeploy") is False


def test_railway_redeploy_source_linked_requires_binding():
    assert requires_source_binding("railway", "redeploy", execution_mode="source_linked") is True


def test_vercel_deploy_requires_binding():
    assert requires_source_binding("vercel", "deploy") is True
