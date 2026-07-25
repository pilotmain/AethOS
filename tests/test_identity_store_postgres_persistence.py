# SPDX-License-Identifier: Apache-2.0
"""Identity store durability: when a database is configured the whole identity
document is persisted via the shared tenant_records store (Postgres on hosted,
SQLite locally), and the legacy on-disk JSON store is migrated in once.

The roundtrip here exercises the SQLite branch of tenant_data_store (no real
Postgres needed); on hosted, the same code path connects to DATABASE_URL.
"""

from __future__ import annotations

import json

import pytest

from aethos_core.api.routes import aethos_identity as ai
from aethos_core.tenancy import tenant_data_store as tds


@pytest.fixture
def shared_store(tmp_path, monkeypatch):
    # Force the shared-store branch and route tenant_data_store at an isolated SQLite db.
    monkeypatch.setenv("DATABASE_URL", "")  # cleared so tds uses sqlite...
    monkeypatch.setattr(ai, "_use_shared_store", lambda: True)
    monkeypatch.setenv("TENANT_DATA_DIR", str(tmp_path / "tdata"))
    monkeypatch.setattr(ai, "_store_path", lambda: tmp_path / "auth" / "auth_store.json")
    tds.reset_for_tests()
    yield tmp_path
    tds.reset_for_tests()


def test_save_then_load_roundtrips_through_shared_store(shared_store):
    store = ai._empty_store()
    store["users"]["u@x.com"] = {"user_id": "u@x.com", "email": "u@x.com", "roles": ["tenant_admin"]}
    ai._save_store(store)

    # New read goes to the shared store, not the (absent) JSON file.
    loaded = ai._load_store()
    assert "u@x.com" in loaded["users"]
    assert loaded["users"]["u@x.com"]["email"] == "u@x.com"


def test_legacy_json_store_is_migrated_in_once(shared_store, tmp_path):
    # Seed a legacy on-disk store as if from the old volume-backed file.
    legacy_path = tmp_path / "auth" / "auth_store.json"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text(
        json.dumps(
            {
                "users": {"legacy@x.com": {"user_id": "legacy@x.com", "email": "legacy@x.com", "roles": ["tenant_admin"]}},
                "sessions": {},
                "oidc_flows": {},
            }
        ),
        encoding="utf-8",
    )

    # First load adopts the legacy file into the shared store.
    loaded = ai._load_store()
    assert "legacy@x.com" in loaded["users"]

    # And it now lives in the shared store directly (independent of the file).
    legacy_path.unlink()
    again = ai._load_store()
    assert "legacy@x.com" in again["users"], "migrated user must persist without the JSON file"


def test_local_mode_without_database_uses_json_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ai, "_use_shared_store", lambda: False)
    monkeypatch.setattr(ai, "_store_path", lambda: tmp_path / "auth_store.json")
    store = ai._empty_store()
    store["users"]["local@x.com"] = {"user_id": "local@x.com", "email": "local@x.com", "roles": ["tenant_admin"]}
    ai._save_store(store)
    assert (tmp_path / "auth_store.json").exists(), "local mode must still write the JSON file"
    assert "local@x.com" in ai._load_store()["users"]
