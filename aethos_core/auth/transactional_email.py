# SPDX-License-Identifier: Apache-2.0
"""Transactional email for auth flows — outside outbound governance."""

from __future__ import annotations

import json
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from aethos_core.config import get_settings

_log = logging.getLogger("aethos.auth.transactional_email")

_DEFAULT_PLACEHOLDER_FROM = "noreply@aethos.local"
_MAILER_USER_AGENT = "AethOS/1.0 (+https://pilotmain.com)"


def _outbound_headers(authorization: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": _MAILER_USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if authorization:
        headers["Authorization"] = authorization
    return headers


def _is_cloudflare_edge_block(detail: str) -> bool:
    lower = (detail or "").lower()
    return "1010" in lower or "cloudflare" in lower


def transactional_mailer_configured() -> bool:
    s = get_settings()
    if str(s.sendgrid_api_key or "").strip():
        return True
    if str(s.smtp_host or "").strip():
        return True
    if str(os.environ.get("RESEND_API_KEY") or "").strip():
        return True
    return False


def _redact(text: str) -> str:
    from aethos_core.security.secret_redaction import redact_text

    return redact_text(str(text or ""))


def _actionable_hint(detail: str) -> str | None:
    lower = (detail or "").lower()
    if "mailer_not_configured" in lower or "not configured" in lower and "email_from" in lower:
        return "Set RESEND_API_KEY (or SendGrid/SMTP) and EMAIL_FROM in your deployment variables."
    if _is_cloudflare_edge_block(detail):
        return (
            "Request blocked by the email provider's CDN edge (Cloudflare error 1010). "
            "Retry shortly or contact the provider — this is not an API key problem."
        )
    if "domain" in lower and ("not verified" in lower or "unverified" in lower):
        domain = ""
        for token in detail.replace(",", " ").split():
            if "." in token and "@" not in token:
                domain = token.strip(".")
                break
        if domain:
            return f"Verify {domain} in your email provider (Resend → Domains)."
        return "Verify your sender domain in your email provider (Resend → Domains)."
    if any(
        phrase in lower
        for phrase in (
            "unauthorized",
            "invalid api key",
            "invalid key",
            "authentication failed",
            "401",
        )
    ):
        return "Check RESEND_API_KEY / SENDGRID_API_KEY in your deployment variables."
    if "email_from" in lower:
        return "Set EMAIL_FROM to a verified sender address on your mail provider."
    return None


def _failure(
    *,
    provider: str,
    detail: str,
    status: int | None = None,
) -> dict[str, Any]:
    redacted = _redact(detail)
    hint = _actionable_hint(redacted)
    out: dict[str, Any] = {
        "ok": False,
        "provider": provider,
        "detail": redacted,
    }
    if status is not None:
        out["status"] = status
    if hint:
        out["hint"] = hint
    _log.warning(
        "transactional_email_failed provider=%s status=%s detail=%s",
        provider,
        status,
        redacted,
    )
    return out


def _success(provider: str) -> dict[str, Any]:
    return {"ok": True, "provider": provider}


def _read_http_error_body(exc: HTTPError) -> str:
    try:
        raw = exc.read()
        if isinstance(raw, bytes):
            text = raw.decode("utf-8", errors="replace")
        else:
            text = str(raw)
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                msg = payload.get("message") or payload.get("error") or payload.get("detail")
                if isinstance(msg, dict):
                    msg = msg.get("message") or json.dumps(msg)
                if msg:
                    return str(msg)
        except json.JSONDecodeError:
            pass
        return text.strip()[:500] or str(exc)
    except Exception:  # noqa: BLE001
        return str(exc)


def _format_http_detail(provider: str, status: int, body: str) -> str:
    msg = _redact(body.strip() or "request failed")
    return f"{provider} {status}: {msg}"


def _http_post_json(
    *,
    provider: str,
    url: str,
    payload: dict[str, Any],
    authorization: str,
) -> dict[str, Any]:
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_outbound_headers(authorization),
        method="POST",
    )
    try:
        with urlopen(req, timeout=20) as resp:
            if 200 <= resp.status < 300:
                return _success(provider)
            body_text = resp.read().decode("utf-8", errors="replace")
            return _failure(
                provider=provider,
                status=resp.status,
                detail=_format_http_detail(provider, resp.status, body_text),
            )
    except HTTPError as exc:
        body_text = _read_http_error_body(exc)
        return _failure(
            provider=provider,
            status=exc.code,
            detail=_format_http_detail(provider, exc.code, body_text),
        )
    except URLError as exc:
        return _failure(provider=provider, detail=f"{provider} network error: {exc.reason}")
    except (OSError, ValueError) as exc:
        return _failure(provider=provider, detail=f"{provider} error: {exc}")


def resolve_from_address() -> tuple[str | None, dict[str, Any] | None]:
    """Return (from_address, error_payload). Hosted deploys require a real EMAIL_FROM."""
    s = get_settings()
    raw = str(s.email_from or "").strip()
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        if not raw or raw.lower() == _DEFAULT_PLACEHOLDER_FROM:
            detail = "EMAIL_FROM not configured (set a verified sender domain)"
            return None, _failure(provider="config", detail=detail)
        return raw, None
    return raw or _DEFAULT_PLACEHOLDER_FROM, None


def _send_resend(to_addr: str, subject: str, body: str) -> dict[str, Any]:
    key = str(os.environ.get("RESEND_API_KEY") or "").strip()
    if not key:
        return _failure(provider="resend", detail="RESEND_API_KEY not set")
    from_addr, from_err = resolve_from_address()
    if from_err:
        return from_err
    payload = {
        "from": from_addr,
        "to": [to_addr],
        "subject": subject,
        "text": body,
    }
    return _http_post_json(
        provider="resend",
        url="https://api.resend.com/emails",
        payload=payload,
        authorization=f"Bearer {key}",
    )


def _send_sendgrid(to_addr: str, subject: str, body: str) -> dict[str, Any]:
    s = get_settings()
    key = str(s.sendgrid_api_key or "").strip()
    if not key:
        return _failure(provider="sendgrid", detail="SENDGRID_API_KEY not set")
    from_addr, from_err = resolve_from_address()
    if from_err:
        return from_err
    payload = {
        "personalizations": [{"to": [{"email": to_addr}]}],
        "from": {"email": from_addr},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    return _http_post_json(
        provider="sendgrid",
        url="https://api.sendgrid.com/v3/mail/send",
        payload=payload,
        authorization=f"Bearer {key}",
    )


def _send_smtp(to_addr: str, subject: str, body: str) -> dict[str, Any]:
    s = get_settings()
    host = str(s.smtp_host or "").strip()
    if not host:
        return _failure(provider="smtp", detail="SMTP_HOST not set")
    from_addr, from_err = resolve_from_address()
    if from_err:
        return from_err
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, int(s.smtp_port or 587), timeout=20) as smtp:
            if s.smtp_use_tls:
                smtp.starttls()
            user = str(s.smtp_user or "").strip()
            if user:
                smtp.login(user, str(s.smtp_password or ""))
            smtp.send_message(msg)
        return _success("smtp")
    except smtplib.SMTPAuthenticationError as exc:
        return _failure(provider="smtp", detail=f"smtp auth failed: {exc.smtp_code} {exc.smtp_error}")
    except (OSError, smtplib.SMTPException) as exc:
        return _failure(provider="smtp", detail=f"smtp error: {exc}")


def send_transactional_email(to_addr: str, subject: str, body: str) -> dict[str, Any]:
    """Send one transactional message; returns provider result with redacted detail on failure."""
    to_addr = (to_addr or "").strip()
    if not to_addr or "@" not in to_addr:
        return {"ok": False, "detail": "invalid_recipient"}
    if not transactional_mailer_configured():
        detail = "mailer_not_configured"
        return {
            "ok": False,
            "detail": detail,
            "hint": _actionable_hint(detail),
        }
    subject = (subject or "").strip() or "AethOS"
    body = body or ""

    s = get_settings()
    senders: list[Any] = []
    if str(os.environ.get("RESEND_API_KEY") or "").strip():
        senders.append(_send_resend)
    if str(s.sendgrid_api_key or "").strip():
        senders.append(_send_sendgrid)
    if str(s.smtp_host or "").strip():
        senders.append(_send_smtp)

    last: dict[str, Any] | None = None
    for sender in senders:
        result = sender(to_addr, subject, body)
        if result.get("ok"):
            _log.info("transactional_email_sent provider=%s to=%s", result.get("provider"), to_addr)
            return result
        last = result
        # Stop on config errors — other providers would fail the same way.
        if result.get("provider") == "config":
            return result

    if last:
        return last
    return _failure(provider="unknown", detail="no mailer provider available")


def send_mailer_test_email(to_addr: str) -> dict[str, Any]:
    """Operator diagnostic — same pipeline as verification mail with a test body."""
    subject = "AethOS mailer test"
    body = (
        "This is a test message from your AethOS deployment.\n\n"
        "If you received this, transactional email (signup verification) should work."
    )
    return send_transactional_email(to_addr, subject, body)
