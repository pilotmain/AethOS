# SPDX-License-Identifier: Apache-2.0
"""Operator parity — CLI surface and provider evidence adapters."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from aethos_core.conversation.provider_memory.adapters.github_adapter import GitHubEvidenceAdapter
from aethos_core.conversation.provider_memory.adapters.vercel_adapter import VercelEvidenceAdapter
from aethos_core.conversation.provider_memory.provider_evidence_adapter import load_evidence_adapter
from aethos_core.operational_skill_runtime.skill_registry import skill_registry_snapshot


def test_cli_help_lists_operator_commands():
    proc = subprocess.run(
        [sys.executable, "-m", "aethos_core.cli.main", "-h"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    for cmd in ("onboard", "gateway", "status", "logs", "message", "doctor"):
        assert cmd in proc.stdout


def test_load_vercel_and_github_evidence_adapters():
    assert isinstance(load_evidence_adapter("vercel"), VercelEvidenceAdapter)
    assert isinstance(load_evidence_adapter("github"), GitHubEvidenceAdapter)


def test_vercel_adapter_status_with_mock_deployment():
    thread = MagicMock()
    thread.service_path.return_value = "my-app / production / my-app"
    thread.service = "my-app"
    thread.status = "execution_queued"
    thread.operation = "redeploy"
    thread.last_evidence = {}
    with patch(
        "aethos_core.conversation.provider_memory.adapters.vercel_adapter._fetch_latest_deployment",
        return_value={"ok": True, "state": "ready", "created_at": "2026-05-29T12:00:00Z"},
    ):
        status = VercelEvidenceAdapter().get_operation_status(thread, None)
    assert status.status_label == "ready"
    assert status.service_health == "online"


def test_skill_registry_marks_vercel_github_partial_or_implemented():
    with patch(
        "aethos_core.provider_skills.vercel.skill.VercelProviderSkill.discover",
        return_value={"ok": True, "inventory": {"project_count": 1}},
    ), patch(
        "aethos_core.provider_skills.github.skill.GitHubProviderSkill.discover",
        return_value={"ok": True, "inventory": {"repository_count": 1}},
    ):
        snapshot = skill_registry_snapshot()
    by_provider = {row["provider"]: row["status"] for row in snapshot["providers"]}
    assert by_provider["railway"] in {"implemented", "partial"}
    assert by_provider["vercel"] in {"implemented", "partial"}
    assert by_provider["github"] in {"implemented", "partial"}
    assert by_provider["aws"] in {"partial", "implemented", "stub"}
