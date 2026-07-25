# SPDX-License-Identifier: Apache-2.0
"""Identity contract loader tests — SOUL/MEMORY runtime authority."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.aethos_identity.identity_contract_loader import (
    clear_contract_cache_for_tests,
    compose_identity_contract_reply,
    is_internal_identity_file_prompt,
    load_identity_contracts,
    reload_identity_contracts,
    set_repo_root_for_tests,
)
from aethos_core.aethos_identity.self_consistency_guard import should_block_generic_fallback
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_contract_cache_for_tests()
    set_repo_root_for_tests(None)
    yield
    clear_contract_cache_for_tests()
    set_repo_root_for_tests(None)
    get_settings.cache_clear()


def test_loads_local_soul_md():
    bundle = load_identity_contracts()
    assert bundle.soul.exists
    assert "governed operational intelligence partner" in bundle.soul.content.lower()
    assert bundle.soul.content_hash
    assert bundle.active_doctrines


def test_loads_local_memory_md():
    bundle = load_identity_contracts()
    assert bundle.memory.exists
    assert "Active operational thread" in bundle.active_memory_hierarchy
    assert bundle.memory_precedence
    assert "semantic and continuity-aware" in bundle.memory.content.lower()


def test_internal_identity_prompt_detection():
    assert is_internal_identity_file_prompt("do you have soul.md?")
    assert is_internal_identity_file_prompt("do you have memory.md?")
    assert not is_internal_identity_file_prompt("restart speakglobal-ai")


def test_compose_identity_contract_reply_for_soul():
    reply = compose_identity_contract_reply("do you have SOUL.md?")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "identity_contract_runtime"
    assert "internal **SOUL.md** loaded from the project runtime" in body
    assert "browser evidence" not in body.lower()
    assert meta.get("source") == "project_runtime"


def test_compose_identity_contract_reply_for_memory():
    reply = compose_identity_contract_reply("do you have memory.md?")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "identity_contract_runtime"
    assert "internal **MEMORY.md** loaded from the project runtime" in body
    assert "browser evidence" not in body.lower()


@patch("aethos_core.chat.web_intelligence.execute_web_intelligence")
def test_does_not_use_browser_for_internal_files(mock_web):
    mock_web.return_value = ("I inspected `soul.md` using browser evidence.", "website_summary", {})

    result = resolve_chat_turn("do you have soul.md?", session_id="identity-no-browser")
    assert "browser evidence" not in result.reply.lower()
    assert "internal **SOUL.md**" in result.reply
    mock_web.assert_not_called()


def test_reload_reflects_file_edits(tmp_path: Path):
    soul = tmp_path / "SOUL.md"
    memory = tmp_path / "MEMORY.md"
    soul.write_text(
        "# Test Soul\n\n**When custom doctrine applies, honor it.**\n",
        encoding="utf-8",
    )
    memory.write_text(
        "# Test Memory\n\n| Layer | Scope | Typical retention |\n|-------|--------|-------------------|\n"
        "| Custom layer | test | 1 hour |\n\n1. Custom runtime evidence\n",
        encoding="utf-8",
    )
    set_repo_root_for_tests(tmp_path)

    first = load_identity_contracts()
    assert "custom doctrine" in first.soul.content.lower()

    soul.write_text(
        "# Test Soul\n\n**When edited doctrine applies, honor edits.**\n",
        encoding="utf-8",
    )
    reloaded = reload_identity_contracts()
    assert reloaded["ok"] is True
    assert any("edited doctrine" in d.lower() for d in reloaded["active_doctrines"])
    assert "Custom layer" in reloaded["active_memory_hierarchy"]


def test_generic_fallback_blocked_by_memory_rules():
    assert should_block_generic_fallback(
        text="can you check top 5 logs and its timestamp for pilotos-api?",
        session_id="memory-contract-block",
    )


def test_reload_api_endpoint(tmp_path: Path):
    soul = tmp_path / "SOUL.md"
    memory = tmp_path / "MEMORY.md"
    soul.write_text("# Soul\n\n**When test applies, run test.**\n", encoding="utf-8")
    memory.write_text(
        "# Memory\n\n| Layer | Scope | Typical retention |\n|---|---|---|\n| Layer A | scope | 1h |\n",
        encoding="utf-8",
    )
    set_repo_root_for_tests(tmp_path)

    from aethos_core.api.main import app

    client = TestClient(app)
    response = client.post("/api/v1/aethos-identity/reload")
    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["soul"]["content_hash"]
    assert payload["memory"]["content_hash"]
    assert payload["active_doctrines"]
