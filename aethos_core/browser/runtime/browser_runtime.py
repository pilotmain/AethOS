# SPDX-License-Identifier: Apache-2.0
"""Governed browser evidence runtime — single entry for orchestration."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from aethos_core.browser.runtime.browser_artifacts import store_artifact
from aethos_core.browser.runtime.browser_audit import append_browser_audit_event
from aethos_core.browser.runtime.browser_policy import evaluate_capture_request, normalize_capture_type
from aethos_core.browser.runtime.browser_session import BrowserEvidenceSession
from aethos_core.security.secret_redaction import redact_text


def normalize_target_url(raw: str) -> str:
    from aethos_core.aethos_identity.identity_contract_loader import is_identity_filename

    text = (raw or "").strip()
    if not text:
        return ""
    basename = text.rsplit("/", 1)[-1].lower()
    if is_identity_filename(basename):
        return ""
    if text.startswith(("http://", "https://")):
        return text
    if "." in text and " " not in text:
        return f"https://{text}"
    return ""


def extract_url_from_request(text: str, *, target_hint: str | None = None) -> str:
    from aethos_core.operations.intents import extract_target_hints
    from aethos_core.operations.orchestration.provider_inference import resolve_url_for_target

    if target_hint:
        inventory_url = resolve_url_for_target(target_hint)
        if inventory_url:
            return inventory_url
        url = normalize_target_url(target_hint)
        if url:
            return url
    raw = text or ""
    for hint in extract_target_hints(raw):
        inventory_url = resolve_url_for_target(hint)
        if inventory_url:
            return inventory_url
    m = re.search(r"https?://[^\s]+", raw, re.I)
    if m:
        return m.group(0).rstrip(".,)")
    m = re.search(
        r"\b(?:for|of|on|at)\s+([a-z0-9][a-z0-9.-]+\.[a-z]{2,})\b",
        raw,
        re.I,
    )
    if m:
        return normalize_target_url(m.group(1))
    m = re.search(r"\bcapture(?:\s+\w+){0,4}\s+([a-z0-9][a-z0-9.-]*)\b", raw, re.I)
    if m:
        token = m.group(1)
        if "." not in token and token.lower() not in ("screenshot", "metadata", "evidence", "browser", "deployment"):
            slug_url = resolve_url_for_target(token)
            if slug_url:
                return slug_url
            return ""
    return ""


def run_browser_evidence_capture(
    *,
    url: str,
    capture_type: str = "screenshot",
    session_id: str = "default",
    user_request: str = "",
    approved: bool = True,
) -> dict[str, Any]:
    from aethos_core.config import get_settings
    from aethos_core.runtime.browser_runtime import run_playwright_on_browser_thread

    normalized_type = normalize_capture_type(capture_type)
    policy = evaluate_capture_request(
        url=url,
        capture_type=normalized_type,
        user_request=user_request,
        approved=approved,
    )
    if not policy.get("allowed"):
        denial = store_artifact(
            capture_type=normalized_type,
            source_url=url or "—",
            session_id=session_id,
            headless=get_settings().browser_headless,
            approved=approved,
            risk_tier=str(policy.get("risk_tier") or "T3"),
            payload={"detail": policy.get("detail"), "failure_class": policy.get("failure_class")},
            artifact_type="browser_policy_denial",
        )
        append_browser_audit_event(
            action="browser_capture",
            target_url=url or None,
            capture_type=normalized_type,
            policy_tier=str(policy.get("risk_tier") or "T3"),
            approved=approved,
            result="blocked",
            session_id=session_id,
            artifact_ids=[denial["artifact_id"]],
            detail=str(policy.get("detail") or ""),
        )
        return {
            "ok": False,
            "blocked": True,
            "policy": policy,
            "artifacts": [denial],
            "timeline": [{"event": "policy_denied", "detail": policy.get("detail")}],
        }

    settings = get_settings()
    evidence_session = BrowserEvidenceSession(
        session_id=session_id,
        source_url=url,
        capture_type=normalized_type,
    )
    evidence_session.record("browser_initialized")
    evidence_session.record("navigation_started", detail=url)

    try:
        payload = run_playwright_on_browser_thread(
            lambda: __import__(
                "aethos_core.browser.runtime.browser_capture",
                fromlist=["capture_page_evidence"],
            ).capture_page_evidence(
                url=url,
                headless=settings.browser_headless,
                capture_type=normalized_type,
            ),
            timeout=120.0,
        )
    except Exception as exc:
        err = redact_text(str(exc))
        failure_class = "browser_capture_failed"
        if any(token in err.lower() for token in ("err_name_not_resolved", "name not resolved", "dns", "nxdomain")):
            failure_class = "browser_capture_failed_dns_resolution"
        append_browser_audit_event(
            action="browser_capture",
            target_url=url,
            capture_type=normalized_type,
            policy_tier=str(policy.get("risk_tier") or "T1"),
            approved=approved,
            result="failed",
            session_id=session_id,
            detail=f"{failure_class}:{err[:80]}",
        )
        return {
            "ok": False,
            "error": err,
            "failure_class": failure_class,
            "timeline": evidence_session.to_dict()["events"],
        }

    if not payload.get("ok"):
        failure_class = str(payload.get("failure_class") or "capture_failed")
        return {
            "ok": False,
            "error": payload.get("error") or "capture failed",
            "failure_class": failure_class,
            "timeline": evidence_session.events,
        }

    evidence_session.record("capture_completed")
    artifacts: list[dict[str, Any]] = []
    tier = str(policy.get("risk_tier") or "T1")

    meta = store_artifact(
        capture_type=normalized_type,
        source_url=url,
        session_id=session_id,
        headless=settings.browser_headless,
        approved=approved,
        risk_tier=tier,
        payload={"metadata": payload.get("metadata") or {}},
        artifact_type="browser_page_metadata",
    )
    artifacts.append(meta)
    evidence_session.artifact_ids.append(meta["artifact_id"])

    if payload.get("dom_snapshot") is not None:
        dom_art = store_artifact(
            capture_type=normalized_type,
            source_url=url,
            session_id=session_id,
            headless=settings.browser_headless,
            approved=approved,
            risk_tier=tier,
            payload={"dom": payload.get("dom_snapshot") or {}},
            artifact_type="browser_dom_snapshot",
        )
        artifacts.append(dom_art)
        evidence_session.artifact_ids.append(dom_art["artifact_id"])

    if payload.get("screenshot_bytes"):
        shot = store_artifact(
            capture_type=normalized_type,
            source_url=url,
            session_id=session_id,
            headless=settings.browser_headless,
            approved=approved,
            risk_tier=tier,
            payload={"metadata": {"url": url}},
            binary=payload.get("screenshot_bytes"),
            artifact_type="browser_screenshot",
        )
        if not shot.get("file_exists") or int(shot.get("file_size_bytes") or 0) <= 0:
            append_browser_audit_event(
                action="browser_capture",
                target_url=url,
                capture_type=normalized_type,
                policy_tier=tier,
                approved=approved,
                result="failed",
                session_id=session_id,
                artifact_ids=[shot.get("artifact_id") or ""],
                detail="screenshot_file_missing",
            )
            return {
                "ok": False,
                "error": "Screenshot artifact file missing or empty after capture.",
                "artifacts": [shot],
                "timeline": evidence_session.to_dict(),
            }
        artifacts.append(shot)
        evidence_session.artifact_ids.append(shot["artifact_id"])

    if payload.get("console_logs"):
        console_art = store_artifact(
            capture_type=normalized_type,
            source_url=url,
            session_id=session_id,
            headless=settings.browser_headless,
            approved=approved,
            risk_tier=tier,
            payload={"logs": payload.get("console_logs") or []},
            artifact_type="browser_console_logs",
        )
        artifacts.append(console_art)
        evidence_session.artifact_ids.append(console_art["artifact_id"])

    if payload.get("network_failures"):
        net_art = store_artifact(
            capture_type=normalized_type,
            source_url=url,
            session_id=session_id,
            headless=settings.browser_headless,
            approved=approved,
            risk_tier=tier,
            payload={"failures": payload.get("network_failures") or []},
            artifact_type="browser_network_summary",
        )
        artifacts.append(net_art)
        evidence_session.artifact_ids.append(net_art["artifact_id"])

    evidence_session.record("artifact_stored", detail=f"{len(artifacts)} artifacts")
    append_browser_audit_event(
        action="browser_capture",
        target_url=url,
        capture_type=normalized_type,
        policy_tier=tier,
        approved=approved,
        result="success",
        session_id=session_id,
        artifact_ids=evidence_session.artifact_ids,
    )

    host = urlparse(url).netloc or url
    summary = f"Browser evidence captured for `{host}` ({normalized_type}) — {len(artifacts)} artifact(s)."
    return {
        "ok": True,
        "summary": summary,
        "artifacts": artifacts,
        "metadata": payload.get("metadata") or {},
        "timeline": evidence_session.to_dict(),
        "policy": policy,
    }


def run_deployment_evidence_capture(
    *,
    user_request: str,
    provider: str,
    target: str,
    session_id: str = "default",
    approved: bool = True,
    capture_type: str = "full",
) -> dict[str, Any]:
    from aethos_core.browser.deployment_url_resolution import resolve_public_deployment_url
    from aethos_core.config import get_settings

    settings = get_settings()
    resolution = resolve_public_deployment_url(provider=provider, target=target)
    resolution_art = store_artifact(
        capture_type="deployment_evidence",
        source_url=resolution.public_url or f"{provider}:{target}",
        session_id=session_id,
        headless=settings.browser_headless,
        approved=approved,
        risk_tier="T1",
        payload={"resolution": resolution.to_dict()},
        artifact_type="deployment_url_resolution",
    )
    artifacts: list[dict[str, Any]] = [resolution_art]

    if not resolution.resolved or not resolution.public_url:
        meta_art = store_artifact(
            capture_type="deployment_evidence",
            source_url=f"{provider}:{target}",
            session_id=session_id,
            headless=settings.browser_headless,
            approved=approved,
            risk_tier="T0",
            payload={
                "metadata": {
                    "provider": provider,
                    "target": target,
                    "browser_capture_attempted": False,
                    "browser_capture_success": False,
                    "fallback_mode": "metadata_only",
                    "failure_reason": resolution.failure_reason or "no_public_url",
                    "deployment_metadata": resolution.metadata,
                }
            },
            artifact_type="deployment_metadata_only",
        )
        artifacts.append(meta_art)
        append_browser_audit_event(
            action="browser_capture",
            target_url=None,
            capture_type="deployment_evidence",
            policy_tier="T0",
            approved=approved,
            result="metadata_only",
            session_id=session_id,
            artifact_ids=[a["artifact_id"] for a in artifacts],
            detail=resolution.failure_reason or "no_public_url",
        )
        summary = (
            f"No public deployment URL found for `{target}`. "
            "Captured deployment metadata evidence instead."
        )
        return {
            "ok": True,
            "metadata_only": True,
            "summary": summary,
            "artifacts": artifacts,
            "url_resolution": resolution.to_dict(),
            "timeline": {"events": [{"event": "metadata_only_fallback"}]},
        }

    capture = run_browser_evidence_capture(
        url=resolution.public_url,
        capture_type=capture_type,
        session_id=session_id,
        user_request=user_request,
        approved=approved,
    )
    capture["url_resolution"] = resolution.to_dict()
    capture["artifacts"] = [resolution_art, *(capture.get("artifacts") or [])]
    if capture.get("ok"):
        capture["summary"] = (
            f"Deployment evidence captured for `{target}` at `{resolution.public_url}` "
            f"({resolution.resolution_source})."
        )
    elif capture.get("failure_class") == "browser_capture_failed_dns_resolution":
        capture["summary"] = (
            f"Resolved URL `{resolution.public_url}` but browser capture failed DNS resolution."
        )
    return capture
