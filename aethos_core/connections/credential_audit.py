# SPDX-License-Identifier: Apache-2.0
"""Credential lifecycle audit — no raw secrets."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from time import time
from typing import Any

_log = logging.getLogger(__name__)


def _audit_path() -> Path:
    from aethos_core.security.credential_paths import credential_audit_path

    return credential_audit_path()


def append_credential_audit_event(
    *,
    event: str,
    provider: str,
    credential_id: str | None = None,
    detail: str | None = None,
    validation_status: str | None = None,
) -> None:
    row: dict[str, Any] = {
        "at": time(),
        "event": event,
        "provider": provider,
    }
    if credential_id:
        row["credential_id"] = credential_id
    if detail:
        row["detail"] = detail[:240]
    if validation_status:
        row["validation_status"] = validation_status
    try:
        path = _audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        _log.exception("credential_audit_write_failed")
    _log.info(
        "credential_audit event=%s provider=%s credential_id=%s status=%s",
        event,
        provider,
        credential_id or "—",
        validation_status or "—",
    )
