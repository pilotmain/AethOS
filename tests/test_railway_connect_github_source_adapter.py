# SPDX-License-Identifier: Apache-2.0
"""FIX 109 — governed Railway connect_source / GitHub binding adapter."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter import (
    connect_github_source,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_connect_github_source_authorization,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_connect_github_source_rejects_unauthorized_call():
    result = connect_github_source(
        environment_name="staging",
        environment_id="env-1",
        service_id="svc-1",
        repository="org/repo",
        branch="main",
        idempotency_key="idem",
    )
    assert result.ok is False
    assert any("authorization" in err.lower() for err in result.errors)


def test_connect_github_source_staging_bind_skip_deploy():
    with (
        patch.dict(
            "os.environ",
            {
                "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
                "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
                "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
            },
            clear=False,
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.resolve_railway_mutation_credentials",
            return_value=("tok", "env", None),
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.stage_github_source_binding",
            return_value={"ok": True, "detail": "staged"},
        ) as mock_stage,
        patch(
            "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.commit_staged_changes_skip_deploy",
            return_value={"ok": True, "detail": "committed"},
        ) as mock_commit,
        live_connect_github_source_authorization(),
    ):
        get_settings.cache_clear()
        result = connect_github_source(
            environment_name="staging",
            environment_id="env-staging",
            service_id="svc-109",
            repository="org/repo",
            branch="main",
            idempotency_key="idem-109",
        )

    assert result.ok is True
    assert result.mutation_performed is True
    mock_stage.assert_called_once()
    mock_commit.assert_called_once()


def test_connect_github_source_idempotent_journal_binding():
    with (
        patch.dict(
            "os.environ",
            {
                "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
                "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
                "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
            },
            clear=False,
        ),
        live_connect_github_source_authorization(),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.stage_github_source_binding",
        ) as mock_stage,
    ):
        get_settings.cache_clear()
        result = connect_github_source(
            environment_name="staging",
            environment_id="env-staging",
            service_id="svc-109",
            repository="org/repo",
            branch="main",
            idempotency_key="idem-replay",
            existing_binding={"repository": "org/repo", "branch": "main"},
        )

    assert result.ok is True
    assert result.idempotent_replay is True
    assert result.mutation_performed is False
    mock_stage.assert_not_called()
