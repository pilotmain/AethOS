# SPDX-License-Identifier: Apache-2.0
"""Vercel adapter expansion capability tests."""

from __future__ import annotations

from unittest.mock import patch

import aethos_core.providers  # noqa: F401 — register providers

from aethos_core.capability_truth.provider_capability_matrix import get_provider_summary
from aethos_core.providers.vercel.expansion.capability_registry import (
    vercel_expansion_summary,
    vercel_operation_spec,
)
from aethos_core.providers.vercel.operations.readonly_execution import VercelReadonlyExecutionAdapter


def test_vercel_matrix_tier_is_expanding() -> None:
    summary = get_provider_summary("vercel")
    assert summary is not None
    assert summary.tier == "expanding"
    assert "redeploy" in " ".join(summary.mutation_ops)


def test_vercel_expansion_registry_marks_env_mutations_expanding() -> None:
    for operation in ("set_env_var", "remove_env_var", "rollback", "promote_deployment"):
        spec = vercel_operation_spec(operation)
        assert spec is not None
        assert spec.status == "expanding"
        assert spec.enabled is False

    redeploy = vercel_operation_spec("redeploy")
    assert redeploy is not None
    assert redeploy.status == "wired"
    assert redeploy.enabled is True


def test_vercel_env_metadata_readonly_returns_keys_only() -> None:
    adapter = VercelReadonlyExecutionAdapter("test-token")
    payload = {
        "ok": True,
        "project_name": "demo-app",
        "env_count": 1,
        "env_metadata": [{"key": "API_URL", "target": "production", "git_branch": "", "id": "env-1"}],
        "note": "Metadata only — secret values are never returned.",
    }
    with patch(
        "aethos_core.providers.vercel.operations.env_metadata_api.fetch_env_metadata",
        return_value=payload,
    ), patch(
        "aethos_core.providers.vercel.operations.env_metadata_api.format_env_metadata_output",
        return_value="Env metadata for demo-app",
    ):
        result = adapter.get_env_metadata(project_name="demo-app")
    assert result["ok"] is True
    assert result["env_metadata"][0]["key"] == "API_URL"
    assert "secret values" in result["note"].lower()


def test_vercel_expansion_summary_lists_wired_readonly_ops() -> None:
    summary = vercel_expansion_summary()
    assert "env_metadata" in summary["readonly_wired"]
    assert "redeploy" in summary["mutations_wired"]
    assert "set_env_var" in summary["expanding"]


def test_vercel_provider_capabilities_include_env_metadata() -> None:
    from aethos_core.providers.vercel.provider import VERCEL_LEGACY_CAPABILITIES

    assert VERCEL_LEGACY_CAPABILITIES["env_metadata"]["api"] is True
    assert VERCEL_LEGACY_CAPABILITIES["set_env_var"]["enabled"] is False
    assert VERCEL_LEGACY_CAPABILITIES["remove_env_var"]["enabled"] is False
