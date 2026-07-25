# SPDX-License-Identifier: Apache-2.0
"""§3 Unified, tamper-evident audit ledger.

A single append-only log of *who did what, when, with what approval* across the
privileged surface (login, vault read/write, preflight, approval, mutation
execute, channel send, agent spawn). Each entry carries a hash of the previous
entry, forming a chain: editing or deleting any past entry breaks verification
of every entry after it.

This consolidates the scattered audit signals (credential_audit, workspace_audit,
execution_receipts, render snapshots) into one ordered, exportable trail for SIEM
ingestion. It does not replace those domain logs; it is the cross-cutting spine
that links them by ``approval_id`` / ``ref``.

Storage is an append-only JSONL file guarded by a process lock — consistent with
AethOS's existing file-backed stores and sufficient for the single-node /
small-team scale this product targets. Values are secret-redacted on the way in.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Iterable

_log = logging.getLogger(__name__)
_LOCK = threading.RLock()

GENESIS_HASH = "0" * 64

# The privileged action vocabulary. Keep additions append-only and descriptive.
ACTIONS = (
    "auth.login",
    "auth.login_failed",
    "auth.logout",
    "auth.sso_login",
    "vault.read",
    "vault.write",
    "vault.delete",
    "mutation.preflight",
    "approval.grant",
    "approval.deny",
    "mutation.execute",
    "channel.send",
    "agent.spawn",
    "user.roles_changed",
    "user.disabled",
)


def _ledger_path() -> Path:
    from aethos_core.config import get_settings

    raw = Path(getattr(get_settings(), "audit_ledger_dir", "data/audit"))
    if not raw.is_absolute():
        raw = Path(__file__).resolve().parents[2] / raw
    raw.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(raw, 0o700)
    except OSError:
        pass
    return raw / "ledger.jsonl"


def _canonical(entry: dict[str, Any]) -> str:
    """Deterministic serialization of an entry minus its own hash."""
    payload = {k: v for k, v in entry.items() if k != "entry_hash"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _hash_entry(entry: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(entry).encode("utf-8")).hexdigest()


def _last_entry() -> dict[str, Any] | None:
    path = _ledger_path()
    if not path.exists():
        return None
    last_line = ""
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last_line = line
    if not last_line:
        return None
    try:
        return json.loads(last_line)
    except json.JSONDecodeError:
        return None


def record_audit_event(
    *,
    action: str,
    actor: str | None = None,
    org: str | None = None,
    target: str | None = None,
    before: Any = None,
    after: Any = None,
    approval_id: str | None = None,
    outcome: str = "ok",
    ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a hash-chained audit entry. Never raises into the caller's path."""
    from aethos_core.config import get_settings
    from aethos_core.security.secret_redaction import redact_value

    if not getattr(get_settings(), "audit_ledger_enabled", True):
        return {}
    try:
        with _LOCK:
            prev = _last_entry()
            prev_hash = prev.get("entry_hash", GENESIS_HASH) if prev else GENESIS_HASH
            seq = (prev.get("seq", 0) + 1) if prev else 1
            entry: dict[str, Any] = {
                "seq": seq,
                "at": time.time(),
                "action": action,
                "actor": actor or "system",
                "org": org or "default",
                "target": target,
                "outcome": outcome,
                "approval_id": approval_id,
                "ref": ref,
                "before": redact_value(before) if before is not None else None,
                "after": redact_value(after) if after is not None else None,
                "metadata": redact_value(metadata or {}),
                "prev_hash": prev_hash,
            }
            entry["entry_hash"] = _hash_entry(entry)
            path = _ledger_path()
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
            return entry
    except OSError:
        _log.exception("audit_ledger_write_failed action=%s", action)
        return {}


def read_entries(
    *,
    org: str | None = None,
    actor: str | None = None,
    action: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    path = _ledger_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with _LOCK, path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if org and row.get("org") != org:
                continue
            if actor and row.get("actor") != actor:
                continue
            if action and row.get("action") != action:
                continue
            rows.append(row)
    if limit is not None and limit >= 0:
        rows = rows[-limit:]
    return rows


def verify_chain() -> dict[str, Any]:
    """Recompute the hash chain. Returns ok=False with the first break point."""
    path = _ledger_path()
    if not path.exists():
        return {"ok": True, "entries": 0, "verified": True}
    prev_hash = GENESIS_HASH
    count = 0
    with _LOCK, path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                return {"ok": False, "entries": count, "broken_at": lineno, "reason": "malformed_json"}
            count += 1
            if row.get("prev_hash") != prev_hash:
                return {
                    "ok": False,
                    "entries": count,
                    "broken_at": row.get("seq", lineno),
                    "reason": "prev_hash_mismatch",
                }
            recomputed = _hash_entry(row)
            if recomputed != row.get("entry_hash"):
                return {
                    "ok": False,
                    "entries": count,
                    "broken_at": row.get("seq", lineno),
                    "reason": "entry_hash_mismatch",
                }
            prev_hash = row["entry_hash"]
    return {"ok": True, "entries": count, "verified": True, "head_hash": prev_hash}


def archive_before(cutoff_ts: float) -> dict[str, Any]:
    """§10 retention — archive audit entries older than cutoff, then re-chain the
    remaining (recent) entries from genesis. The full pre-rotation ledger is
    snapshotted to a timestamped archive so the historical chain stays
    independently verifiable; the active ledger remains valid (new genesis)."""
    path = _ledger_path()
    if not path.exists():
        return {"ok": True, "archived": 0, "kept": 0}
    with _LOCK:
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        old = [r for r in rows if r.get("at", 0) < cutoff_ts]
        keep = [r for r in rows if r.get("at", 0) >= cutoff_ts]
        if not old:
            return {"ok": True, "archived": 0, "kept": len(keep)}
        archive_dir = path.parent / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"ledger-{int(time.time())}.jsonl"
        # Snapshot the full pre-rotation ledger (preserves the entire chain).
        archive_path.write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )
        # Re-chain the kept entries from genesis into the active ledger.
        prev_hash = GENESIS_HASH
        rebuilt: list[dict[str, Any]] = []
        for i, row in enumerate(keep, start=1):
            entry = {k: v for k, v in row.items() if k != "entry_hash"}
            entry["seq"] = i
            entry["prev_hash"] = prev_hash
            entry["entry_hash"] = _hash_entry(entry)
            prev_hash = entry["entry_hash"]
            rebuilt.append(entry)
        path.write_text("".join(json.dumps(r) + "\n" for r in rebuilt), encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return {
            "ok": True,
            "archived": len(old),
            "kept": len(keep),
            "archive_file": str(archive_path),
        }


_CSV_FIELDS = (
    "seq",
    "at",
    "action",
    "actor",
    "org",
    "target",
    "outcome",
    "approval_id",
    "ref",
    "entry_hash",
    "prev_hash",
)


def export_csv(rows: Iterable[dict[str, Any]]) -> str:
    import csv
    import io

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in _CSV_FIELDS})
    return buf.getvalue()
