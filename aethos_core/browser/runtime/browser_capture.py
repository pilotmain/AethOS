# SPDX-License-Identifier: Apache-2.0
"""Low-level Playwright capture — browser executor thread only."""

from __future__ import annotations

from typing import Any


def capture_page_evidence(
    *,
    url: str,
    headless: bool,
    capture_type: str,
) -> dict[str, Any]:
    from aethos_core.runtime.browser_runtime import assert_on_browser_executor_thread

    assert_on_browser_executor_thread(caller="browser_capture.capture_page_evidence")
    from aethos_core.runtime.browser_diagnostics import validate_browser_runtime_for_execution

    validate_browser_runtime_for_execution()

    from playwright.sync_api import sync_playwright

    console_logs: list[dict[str, Any]] = []
    network_failures: list[dict[str, Any]] = []

    pw = sync_playwright().start()
    browser = None
    try:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        def _on_console(msg: Any) -> None:
            if msg.type in ("error", "warning"):
                console_logs.append({"type": msg.type, "text": str(msg.text)[:500]})

        def _on_request_failed(request: Any) -> None:
            failure = request.failure
            network_failures.append(
                {
                    "url": str(request.url)[:500],
                    "method": request.method,
                    "failure": str(failure)[:240] if failure else "failed",
                }
            )

        page.on("console", _on_console)
        page.on("requestfailed", _on_request_failed)

        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as exc:
            err = str(exc)
            failure_class = "browser_capture_failed"
            if any(token in err.lower() for token in ("err_name_not_resolved", "name not resolved", "dns", "nxdomain")):
                failure_class = "browser_capture_failed_dns_resolution"
            return {
                "ok": False,
                "error": err[:500],
                "failure_class": failure_class,
                "network_failures": network_failures[:50],
            }
        # Let JS-rendered / lazy content settle before we read or capture — SPAs paint after
        # DOMContentLoaded, so capturing immediately yields a blank page.
        from aethos_core.config import get_settings

        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass  # some sites keep long-lived connections open; the settle delay still applies
        settle_ms = int(getattr(get_settings(), "browser_capture_settle_ms", 2500) or 0)
        if settle_ms > 0:
            try:
                page.wait_for_timeout(settle_ms)
            except Exception:
                pass

        status_code = response.status if response else None
        final_url = page.url
        title = page.title()

        metadata = {
            "title": title,
            "url": final_url,
            "requested_url": url,
            "status_code": status_code,
            "meta_tags": _extract_meta(page),
            "visible_text_preview": _visible_text_preview(page),
            "headings": _headings(page),
            "links_sample": _links_sample(page),
            "forms_detected": _forms_detected(page),
        }

        screenshot_bytes: bytes | None = None
        dom_snapshot: dict[str, Any] | None = None

        if capture_type in ("screenshot", "full"):
            screenshot_bytes = page.screenshot(full_page=False, type="png")

        if capture_type in ("metadata", "full"):
            dom_snapshot = {
                "title": title,
                "url": final_url,
                "headings": metadata["headings"],
                "links_sample": metadata["links_sample"],
                "forms_detected": metadata["forms_detected"],
            }

        return {
            "ok": True,
            "metadata": metadata,
            "screenshot_bytes": screenshot_bytes,
            "dom_snapshot": dom_snapshot,
            "console_logs": console_logs[:50],
            "network_failures": network_failures[:50],
        }
    finally:
        if browser is not None:
            browser.close()
        pw.stop()


def _extract_meta(page: Any) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for el in page.locator("meta[name], meta[property]").all()[:20]:
        try:
            rows.append(
                {
                    "name": str(el.get_attribute("name") or el.get_attribute("property") or ""),
                    "content": str(el.get_attribute("content") or "")[:200],
                }
            )
        except Exception:
            continue
    return rows


def _visible_text_preview(page: Any) -> str:
    try:
        text = page.locator("body").inner_text(timeout=5_000)
        return " ".join(text.split())[:1200]
    except Exception:
        return ""


def _headings(page: Any) -> list[str]:
    out: list[str] = []
    for tag in ("h1", "h2", "h3"):
        for el in page.locator(tag).all()[:5]:
            try:
                t = (el.inner_text() or "").strip()
                if t:
                    out.append(f"{tag}: {t[:120]}")
            except Exception:
                continue
    return out[:15]


def _links_sample(page: Any) -> list[str]:
    out: list[str] = []
    for el in page.locator("a[href]").all()[:10]:
        try:
            href = str(el.get_attribute("href") or "")
            text = (el.inner_text() or "").strip()[:80]
            if href:
                out.append(f"{text or href} → {href[:120]}")
        except Exception:
            continue
    return out


def _forms_detected(page: Any) -> int:
    try:
        return page.locator("form").count()
    except Exception:
        return 0
