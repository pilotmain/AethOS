# SPDX-License-Identifier: Apache-2.0
"""§3 unified tamper-evident audit ledger — chaining, verification, export."""

from __future__ import annotations

import pytest

import aethos_core.observability.audit_ledger as ledger
from aethos_core.config import get_settings


@pytest.fixture
def ledger_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_LEDGER_ENABLED", "true")
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def test_chain_links_and_verifies(ledger_env):
    a = ledger.record_audit_event(action="auth.login", actor="alice@x.io")
    b = ledger.record_audit_event(action="mutation.execute", actor="alice@x.io", target="railway:restart")
    assert a["seq"] == 1 and b["seq"] == 2
    assert b["prev_hash"] == a["entry_hash"]
    result = ledger.verify_chain()
    assert result["ok"] and result["entries"] == 2


def test_secrets_are_redacted(ledger_env):
    entry = ledger.record_audit_event(
        action="vault.write",
        metadata={"authorization": "Bearer abcdefghijklmnopqrstuvwxyz0123456789"},
    )
    assert "abcdefghijklmnopqrstuvwxyz" not in str(entry["metadata"])


def test_editing_past_entry_breaks_chain(ledger_env):
    ledger.record_audit_event(action="auth.login", actor="alice@x.io")
    ledger.record_audit_event(action="approval.grant", actor="bob@x.io")
    path = ledger._ledger_path()
    lines = path.read_text(encoding="utf-8").splitlines()
    # Tamper with the first entry's payload without recomputing its hash.
    lines[0] = lines[0].replace("alice@x.io", "mallory@x.io")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = ledger.verify_chain()
    assert result["ok"] is False
    assert result["reason"] in {"entry_hash_mismatch", "prev_hash_mismatch"}


def test_export_csv_and_filter(ledger_env):
    ledger.record_audit_event(action="auth.login", actor="alice@x.io", org="acme")
    ledger.record_audit_event(action="agent.spawn", actor="bob@x.io", org="other")
    acme = ledger.read_entries(org="acme")
    assert len(acme) == 1 and acme[0]["actor"] == "alice@x.io"
    csv_text = ledger.export_csv(ledger.read_entries())
    assert "seq,at,action" in csv_text
    assert "agent.spawn" in csv_text


def test_disabled_flag_is_noop(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_LEDGER_ENABLED", "false")
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    get_settings.cache_clear()
    try:
        assert ledger.record_audit_event(action="auth.login") == {}
        assert not ledger._ledger_path().exists()
    finally:
        get_settings.cache_clear()
