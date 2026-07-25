# SPDX-License-Identifier: Apache-2.0
"""Cross-process shared store — worker write visible to API read."""

from __future__ import annotations

import os

import pytest

from aethos_core.canvas.canvas_db import canvas_uses_postgres, reset_canvas_db_for_tests
from aethos_core.canvas.canvas_store import clear_canvas_for_tests, get_canvas_state, init_canvas_store_schema, render_canvas_view
from aethos_core.channels.session_alias import clear_session_alias_for_tests, link_session_ids, resolve_canonical_session_id
from aethos_core.config import get_settings
from aethos_core.tenancy.tenant_data_store import reset_for_tests
from aethos_core.workspace_suite.documents_store import clear_documents_for_tests, create_document, get_document
from aethos_core.workspace_suite.notes_tasks_store import add_note, clear_notes_tasks_for_tests, list_notes


def _enable_hosted_shared(tmp_path, monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("TENANT_DATA_DIR", str(tmp_path / "tenant_data"))
    get_settings.cache_clear()
    reset_for_tests()
    clear_canvas_for_tests()
    clear_session_alias_for_tests()
    clear_documents_for_tests()
    clear_notes_tasks_for_tests()


def _postgres_url() -> str:
    return str(
        os.environ.get("TEST_DATABASE_URL", "") or os.environ.get("DATABASE_URL", "") or ""
    ).strip()


@pytest.fixture
def postgres_canvas_env(monkeypatch):
    url = _postgres_url()
    if not url:
        pytest.skip("DATABASE_URL or TEST_DATABASE_URL required for Postgres canvas tests")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    get_settings.cache_clear()
    reset_canvas_db_for_tests()
    clear_canvas_for_tests()
    init_canvas_store_schema()
    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    yield
    clear_canvas_for_tests()
    reset_canvas_db_for_tests()


def test_canvas_worker_write_api_read_postgres(postgres_canvas_env):
    """Worker write then API read against shared Postgres (simulated via connection reset)."""
    assert canvas_uses_postgres()
    out = render_canvas_view(
        session_id="sess-worker-pg",
        view_type="job_timeline",
        title="Jobs",
        data={"rows": [{"id": "j1"}]},
    )
    assert out["ok"] is True

    reset_canvas_db_for_tests()
    get_settings.cache_clear()
    init_canvas_store_schema()

    state = get_canvas_state(session_id="sess-worker-pg")
    assert state["view_count"] >= 1
    assert any(v.get("view_type") == "job_timeline" for v in state["views"])


def test_canvas_postgres_tenant_isolation(postgres_canvas_env, monkeypatch):
    from aethos_core.tenancy.tenant_context import set_current_tenant

    set_current_tenant("tenant-a")
    render_canvas_view(
        session_id="sess-tenant-a",
        view_type="status",
        title="A",
        data={"tenant": "a"},
    )
    set_current_tenant("tenant-b")
    state_b = get_canvas_state(session_id="sess-tenant-a")
    assert state_b["view_count"] == 0

    render_canvas_view(
        session_id="sess-tenant-b",
        view_type="status",
        title="B",
        data={"tenant": "b"},
    )
    state_b = get_canvas_state(session_id="sess-tenant-b")
    assert state_b["view_count"] == 1

    reset_canvas_db_for_tests()
    get_settings.cache_clear()
    init_canvas_store_schema()
    set_current_tenant("tenant-a")
    state_a = get_canvas_state(session_id="sess-tenant-a")
    assert state_a["view_count"] == 1


def test_session_alias_cross_process_hosted(tmp_path, monkeypatch):
    _enable_hosted_shared(tmp_path, monkeypatch)
    link_session_ids(session_ids=["sess-a", "sess-b"], canonical_session_id="sess-a")
    reset_for_tests()
    get_settings.cache_clear()
    assert resolve_canonical_session_id("sess-b") == "sess-a"


def test_documents_cross_process_hosted(tmp_path, monkeypatch):
    _enable_hosted_shared(tmp_path, monkeypatch)
    monkeypatch.setattr(get_settings(), "workspace_suite_enabled", True)
    created = create_document(title="Draft", content="hello")
    assert created["ok"] is True
    doc_id = created["document"]["id"]
    reset_for_tests()
    get_settings.cache_clear()
    got = get_document(doc_id=doc_id)
    assert got["ok"] is True
    assert got["document"]["content"] == "hello"


def test_notes_cross_process_hosted(tmp_path, monkeypatch):
    _enable_hosted_shared(tmp_path, monkeypatch)
    monkeypatch.setattr(get_settings(), "workspace_suite_enabled", True)
    add_note(text="remember this")
    reset_for_tests()
    get_settings.cache_clear()
    notes = list_notes()
    assert notes["ok"] is True
    assert notes["note_count"] >= 1


def test_local_mode_still_uses_json_file(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "deployment_mode", "local")
    monkeypatch.setattr(get_settings(), "canvas_store_dir", str(tmp_path / "canvas"))
    clear_canvas_for_tests()
    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    assert not canvas_uses_postgres()

    render_canvas_view(
        session_id="sess-local",
        view_type="status",
        title="Status",
        data={"ok": True},
    )
    canvas_file = tmp_path / "canvas" / "canvas.json"
    assert canvas_file.is_file()
    assert get_canvas_state(session_id="sess-local")["view_count"] >= 1
