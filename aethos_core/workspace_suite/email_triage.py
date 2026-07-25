# SPDX-License-Identifier: Apache-2.0
"""Workspace suite — Email triage tab (handoff §8).

Readonly IMAP inbox triage (urgency, auto-tag, summary, spam heuristics) plus
DRAFT replies. Drafts are NEVER auto-sent: sending a draft routes through the
existing governed outbound-send preflight (handoff §5/§8), which itself requires
operator approval + OUTBOUND_SEND_EXECUTION_ENABLED + recipient allowlist.

Credentials resolve vault-first (per-tenant IMAP in Providers → Email (IMAP/SMTP)). Local
single-operator deploys may still use gitignored email_creds.json or IMAP_* env.
Gated by WORKSPACE_SUITE_ENABLED, default off.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

_URGENT_KEYWORDS = (
    "urgent", "asap", "immediately", "deadline", "action required", "past due",
    "overdue", "final notice", "payment failed", "security alert", "expires",
)
_SPAM_KEYWORDS = (
    "winner", "free money", "click here to claim", "you've won", "viagra",
    "crypto giveaway", "act now", "limited time offer", "wire transfer",
)
_TAG_RULES = {
    "billing": ("invoice", "payment", "billing", "receipt", "subscription"),
    "security": ("security", "password", "login", "2fa", "verification code"),
    "ci": ("build failed", "pipeline", "workflow", "deploy", "ci/cd"),
    "meeting": ("meeting", "calendar", "invite", "schedule", "zoom", "call"),
    "support": ("ticket", "support", "issue", "bug", "incident"),
}


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (
        getattr(get_settings(), "workspace_suite_store_dir", "data/workspace_suite")
        or "data/workspace_suite"
    ).strip()
    return Path(raw)


def _enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "workspace_suite_enabled", False))


def triage_message(*, subject: str, sender: str, body: str) -> dict[str, Any]:
    """Pure heuristic triage — urgency, tags, spam, one-line summary. No network."""
    text = f"{subject}\n{body}".lower()
    urgency = "high" if any(k in text for k in _URGENT_KEYWORDS) else "normal"
    is_spam = sum(1 for k in _SPAM_KEYWORDS if k in text) >= 2
    tags = sorted({tag for tag, kws in _TAG_RULES.items() if any(k in text for k in kws)})
    first_line = (subject or "").strip() or (body or "").strip().splitlines()[0] if (body or "").strip() else ""
    summary = (first_line or "(no subject)")[:160]
    return {
        "urgency": urgency,
        "tags": tags,
        "spam": is_spam,
        "summary": summary,
    }


def _resolve_imap_creds() -> dict[str, str] | None:
    """Vault-first per-tenant creds; local file/env only for single-operator local deploys."""
    from aethos_core.workspace_suite.email_credentials import resolve_email_imap_connection

    vault_creds = resolve_email_imap_connection()
    if vault_creds:
        return {
            "host": vault_creds["host"],
            "user": vault_creds["user"],
            "password": vault_creds["password"],
            "mailbox": vault_creds["mailbox"],
            "port": vault_creds.get("port") or "993",
        }

    from aethos_core.production.deployment_mode import is_hosted_deployment
    from aethos_core.config import get_settings

    if is_hosted_deployment() or get_settings().multi_tenant_enabled:
        return None

    creds_path = _store_root() / "email_creds.json"
    if creds_path.is_file():
        try:
            data = json.loads(creds_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("imap_host") and data.get("imap_user"):
                return {
                    "host": str(data["imap_host"]),
                    "user": str(data["imap_user"]),
                    "password": str(data.get("imap_password") or ""),
                    "mailbox": str(data.get("imap_mailbox") or "INBOX"),
                    "port": str(data.get("imap_port") or "993"),
                }
        except (OSError, json.JSONDecodeError):
            pass
    host = os.environ.get("IMAP_HOST")
    user = os.environ.get("IMAP_USER")
    if host and user:
        return {
            "host": host,
            "user": user,
            "password": os.environ.get("IMAP_PASSWORD", ""),
            "mailbox": os.environ.get("IMAP_MAILBOX", "INBOX"),
            "port": os.environ.get("IMAP_PORT", "993"),
        }
    return None


def triage_inbox(*, limit: int = 20) -> dict[str, Any]:
    """Readonly IMAP fetch + heuristic triage. Returns imap_not_configured if no creds."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled", "messages": []}
    creds = _resolve_imap_creds()
    if creds is None:
        return {
            "ok": False,
            "error": "imap_not_configured",
            "hint": "Connect your inbox in Mission Control → Advanced settings → Credentials → Email (IMAP/SMTP), then triage here.",
            "messages": [],
        }
    import email
    import imaplib
    from email.header import decode_header, make_header

    cap = max(1, min(int(limit or 20), 50))
    try:
        port = int(str(creds.get("port") or "993"))
        conn = imaplib.IMAP4_SSL(creds["host"], port)
        conn.login(creds["user"], creds["password"])
        # readonly=True — triage never marks/moves/deletes mail.
        conn.select(creds["mailbox"], readonly=True)
        typ, data = conn.search(None, "ALL")
        ids = (data[0].split() if data and data[0] else [])[-cap:]
        messages: list[dict[str, Any]] = []
        for raw_id in reversed(ids):
            typ, msg_data = conn.fetch(raw_id, "(RFC822)")
            if typ != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = str(make_header(decode_header(msg.get("Subject", ""))))
            sender = str(make_header(decode_header(msg.get("From", ""))))
            body = _extract_text(msg)
            triage = triage_message(subject=subject, sender=sender, body=body)
            messages.append(
                {
                    "uid": raw_id.decode() if isinstance(raw_id, bytes) else str(raw_id),
                    "subject": subject[:200],
                    "from": sender[:200],
                    "snippet": body.strip()[:280],
                    **triage,
                }
            )
        conn.logout()
        return {"ok": True, "message_count": len(messages), "readonly": True, "messages": messages}
    except Exception as exc:  # IMAP/transport failure
        return {"ok": False, "error": "imap_fetch_failed", "detail": str(exc)[:300], "messages": []}


def _extract_text(msg: Any) -> str:
    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            return ""
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    except Exception:  # pragma: no cover - defensive decode
        return ""
    return ""


def _drafts_path() -> Path:
    return _store_root() / "email_drafts.json"


def _load_drafts() -> dict[str, Any]:
    path = _drafts_path()
    if not path.is_file():
        return {"drafts": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"drafts": {}}
    return data if isinstance(data, dict) else {"drafts": {}}


def _save_drafts(data: dict[str, Any]) -> None:
    path = _drafts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def create_draft_reply(*, to: str, subject: str, body: str) -> dict[str, Any]:
    """Create a DRAFT reply — never sends. Sending routes through outbound governance."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    recipient = (to or "").strip()
    text = (body or "").strip()
    if not recipient or not text:
        return {"ok": False, "error": "to_and_body_required"}
    draft_id = f"draft-{secrets.token_hex(5)}"
    draft = {
        "id": draft_id,
        "to": recipient,
        "subject": (subject or "")[:200],
        "body": text[:8000],
        "status": "draft",  # never auto-sent
        "sent": False,
        "created_at": time.time(),
    }
    data = _load_drafts()
    drafts = dict(data.get("drafts") or {})
    drafts[draft_id] = draft
    data["drafts"] = drafts
    _save_drafts(data)
    return {"ok": True, "draft": draft}


def list_draft_replies(*, limit: int = 50) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled", "drafts": []}
    drafts = [d for d in (_load_drafts().get("drafts") or {}).values() if isinstance(d, dict)]
    drafts.sort(key=lambda d: float(d.get("created_at") or 0), reverse=True)
    return {"ok": True, "draft_count": len(drafts), "drafts": drafts[: max(1, min(int(limit or 50), 200))]}


def send_draft_preflight(*, draft_id: str, session_id: str = "operator") -> dict[str, Any]:
    """Route a draft into the governed outbound email preflight. Never sends directly."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    draft = (_load_drafts().get("drafts") or {}).get((draft_id or "").strip())
    if not isinstance(draft, dict):
        return {"ok": False, "error": "draft_not_found", "id": draft_id}
    from aethos_core.channels.outbound_governance import create_outbound_send_preflight

    return create_outbound_send_preflight(
        channel="email",
        to=str(draft.get("to")),
        body=str(draft.get("body")),
        subject=str(draft.get("subject") or ""),
        session_id=session_id,
    )


def clear_email_for_tests() -> None:
    for path in (_drafts_path(), _store_root() / "email_creds.json"):
        if path.is_file():
            path.unlink()
