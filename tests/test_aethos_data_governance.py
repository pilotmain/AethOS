# SPDX-License-Identifier: Apache-2.0
"""§10 data governance — PII redaction, retention, audit archive, backup/restore."""

from __future__ import annotations

import importlib
import time

import pytest

from aethos_core.config import get_settings
from aethos_core.security import secret_redaction


def test_pii_redaction():
    out = secret_redaction.redact_pii("contact jane.doe@example.com or 415-555-1212")
    assert "jane.doe@example.com" not in out
    assert "415-555-1212" not in out


def test_retention_disabled_is_noop(monkeypatch):
    monkeypatch.delenv("RETENTION_ENABLED", raising=False)
    get_settings.cache_clear()
    from aethos_core.data_governance import retention

    try:
        report = retention.prune_retention(dry_run=True)
        assert report["enabled"] is False
        assert report.get("note") == "retention_disabled"
    finally:
        get_settings.cache_clear()


def test_audit_archive_preserves_recent_and_verifies(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    get_settings.cache_clear()
    import aethos_core.observability.audit_ledger as ledger

    importlib.reload(ledger)
    try:
        old = ledger.record_audit_event(action="auth.login", actor="old@x")
        # Force the first entry to be "old".
        path = ledger._ledger_path()
        import json

        lines = path.read_text().splitlines()
        row = json.loads(lines[0])
        row["at"] = time.time() - 100 * 86400
        # Recompute its hash so the pre-archive chain is valid.
        row.pop("entry_hash")
        row["entry_hash"] = ledger._hash_entry(row)
        path.write_text(json.dumps(row) + "\n")
        ledger.record_audit_event(action="auth.login", actor="recent@x")

        result = ledger.archive_before(time.time() - 1 * 86400)
        assert result["archived"] == 1 and result["kept"] == 1
        # Active ledger re-chains from genesis and verifies clean.
        assert ledger.verify_chain()["ok"] is True
        remaining = ledger.read_entries()
        assert len(remaining) == 1 and remaining[0]["actor"] == "recent@x"
    finally:
        get_settings.cache_clear()
        importlib.reload(ledger)


def test_backup_restore_roundtrip(tmp_path):
    import sys

    sys.path.insert(0, str((tmp_path).parent))  # noqa: ensure importable path side-effect free
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "aethos_backup",
        str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "aethos_backup.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Build a fake instance root with some governed state.
    src = tmp_path / "instance"
    (src / "data" / "auth").mkdir(parents=True)
    (src / "data" / "auth" / "auth_store.json").write_text('{"users":{}}')
    (src / "data" / "audit").mkdir(parents=True)
    (src / "data" / "audit" / "ledger.jsonl").write_text('{"seq":1}\n')

    monkey_root = src
    mod._root = lambda: monkey_root  # type: ignore[assignment]

    archive = mod.do_backup(str(src / "data" / "backups"))
    assert archive.is_file()

    # Restore into a clean target.
    dest = tmp_path / "restored"
    dest.mkdir()
    mod._root = lambda: dest  # type: ignore[assignment]
    mod.do_restore(str(archive), str(dest), force=True)
    assert (dest / "data" / "auth" / "auth_store.json").read_text() == '{"users":{}}'
    assert (dest / "data" / "audit" / "ledger.jsonl").is_file()
