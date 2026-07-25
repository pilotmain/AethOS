# SPDX-License-Identifier: Apache-2.0
"""Documents AI assist diff (§B3)."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.workspace_suite import documents_store


@pytest.fixture(autouse=True)
def _suite_on(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_SUITE_ENABLED", "true")
    monkeypatch.setenv("WORKSPACE_SUITE_STORE_DIR", str(tmp_path / "ws"))
    get_settings.cache_clear()
    documents_store.clear_documents_for_tests()
    yield
    documents_store.clear_documents_for_tests()
    get_settings.cache_clear()


def test_create_edit_and_ai_suggestion_diff():
    created = documents_store.create_document(title="Brief", content="PilotMain is cool.")
    doc_id = created["document"]["id"]
    sug = documents_store.propose_ai_edit(doc_id=doc_id, instruction="expand the opening")
    assert sug["ok"] is True
    assert sug["accept_required"] is True
    assert sug["diff"]["before"] == "PilotMain is cool."
    assert "expand" in sug["diff"]["after"].lower() or sug["diff"]["after"] != sug["diff"]["before"]

    applied = documents_store.apply_ai_edit(suggestion_id=sug["suggestion_id"], accept=True)
    assert applied.get("ok") is True
    got = documents_store.get_document(doc_id=doc_id)
    assert got["document"]["content"] == sug["diff"]["after"]
