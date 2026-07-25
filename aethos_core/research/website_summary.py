# SPDX-License-Identifier: Apache-2.0
"""Website summary — lightweight HTTP read + optional browser-backed inspection."""

from __future__ import annotations

import html
import re
import urllib.error
import urllib.request
from typing import Any

from aethos_core.research.research_artifacts import store_research_artifact
from aethos_core.research.research_provider import SearchResultSet, WebsiteSummary

_HTTP_USER_AGENT = "AethOS-public-read/1.0"
_MAX_HTML_BYTES = 500_000


def normalize_website_url(raw: str) -> str:
    from aethos_core.browser.runtime.browser_runtime import normalize_target_url

    return normalize_target_url(raw)


def extract_url_from_text(text: str) -> str | None:
    from aethos_core.aethos_identity.identity_contract_loader import is_identity_filename
    from aethos_core.browser.runtime.browser_runtime import extract_url_from_request

    if is_identity_filename((text or "").strip()):
        return None

    url = extract_url_from_request(text)
    if url:
        return url
    m = re.search(
        r"\b(?:about|details?\s+about|tell\s+me\s+(?:high\s+level\s+)?details?\s+about|"
        r"analyze|inspect|summarize|research)\s+(?:the\s+)?(?:website\s+)?"
        r"(?:https?://)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})\b",
        text or "",
        re.I,
    )
    if m:
        return normalize_website_url(m.group(1))
    m = re.search(r"\b([a-z0-9][a-z0-9.-]+\.[a-z]{2,})\b", text or "", re.I)
    if m:
        token = m.group(1).lower()
        if token not in ("aethos.com", "vercel.com", "github.com"):
            return normalize_website_url(token)
    return None


def extract_search_query(text: str) -> str | None:
    raw = (text or "").strip()
    m = re.search(r"\b(?:search|look\s+up|find)\s+(?:the\s+web\s+for\s+|online\s+for\s+|for\s+)?(.+)$", raw, re.I)
    if m:
        return m.group(1).strip(" ?.")
    if re.search(r"\b(search the web|search online|can you search)\b", raw, re.I):
        return raw
    return None


def _decode_html_body(raw: bytes, content_type: str | None) -> str:
    charset = "utf-8"
    if content_type and "charset=" in content_type.lower():
        charset = content_type.split("charset=", 1)[-1].split(";", 1)[0].strip() or charset
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def _strip_tags(fragment: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_page_fields(html_text: str) -> dict[str, Any]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
    title = _strip_tags(title_match.group(1)) if title_match else ""

    meta_desc = ""
    for tag in re.finditer(r"<meta[^>]+>", html_text, re.I):
        chunk = tag.group(0)
        name_m = re.search(r"(?:name|property)\s*=\s*['\"]?(description|og:description)['\"]?", chunk, re.I)
        if not name_m:
            continue
        content_m = re.search(r"content\s*=\s*['\"](.*?)['\"]", chunk, re.I | re.S)
        if content_m:
            meta_desc = _strip_tags(content_m.group(1))[:400]
            break

    headings: list[str] = []
    for level in (1, 2, 3):
        for match in re.finditer(rf"<h{level}[^>]*>(.*?)</h{level}>", html_text, re.I | re.S):
            text = _strip_tags(match.group(1))
            if text and text not in headings:
                headings.append(text)
            if len(headings) >= 8:
                break

    links: list[str] = []
    for match in re.finditer(r"<a[^>]+href\s*=\s*['\"](.*?)['\"]", html_text, re.I):
        href = match.group(1).strip()
        if href.startswith(("http://", "https://")) and href not in links:
            links.append(href)
        if len(links) >= 6:
            break

    body_match = re.search(r"<body[^>]*>(.*)</body>", html_text, re.I | re.S)
    visible = _strip_tags(body_match.group(1) if body_match else html_text)[:800]

    return {
        "title": title,
        "meta_description": meta_desc,
        "headings": headings,
        "visible_text_preview": visible,
        "links_sample": links,
    }


def summarize_url_via_http_fetch(
    url: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> WebsiteSummary:
    """Read a public URL with a lightweight HTTP GET — no browser automation."""
    from aethos_core.config import get_settings

    normalized = normalize_website_url(url)
    if not normalized:
        return WebsiteSummary(ok=False, url=url, error="Could not normalize URL.", confidence="low")

    timeout = float(get_settings().url_reachability_timeout_sec)
    req = urllib.request.Request(normalized, method="GET", headers={"User-Agent": _HTTP_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(_MAX_HTML_BYTES)
            html_text = _decode_html_body(raw, resp.headers.get("Content-Type"))
    except urllib.error.HTTPError as exc:
        if exc.code < 500:
            try:
                raw = exc.read(_MAX_HTML_BYTES)
                html_text = _decode_html_body(raw, exc.headers.get("Content-Type") if exc.headers else None)
            except Exception:
                html_text = ""
            if not html_text:
                err = f"HTTP {exc.code} from {normalized}"
                art = store_research_artifact(
                    artifact_type="website_metadata_summary",
                    intent="website_summary",
                    channel=channel,
                    confidence="low",
                    payload={"source_url": normalized, "evidence_source": "http_fetch_failed", "error": err},
                )
                return WebsiteSummary(
                    ok=False,
                    url=normalized,
                    error=err,
                    artifact_ids=[art["artifact_id"]],
                    confidence="low",
                )
        else:
            err = f"HTTP {exc.code} from {normalized}"
            art = store_research_artifact(
                artifact_type="website_metadata_summary",
                intent="website_summary",
                channel=channel,
                confidence="low",
                payload={"source_url": normalized, "evidence_source": "http_fetch_failed", "error": err},
            )
            return WebsiteSummary(
                ok=False,
                url=normalized,
                error=err,
                artifact_ids=[art["artifact_id"]],
                confidence="low",
            )
    except Exception as exc:
        err = str(exc)
        art = store_research_artifact(
            artifact_type="website_metadata_summary",
            intent="website_summary",
            channel=channel,
            confidence="low",
            payload={"source_url": normalized, "evidence_source": "http_fetch_failed", "error": err},
        )
        return WebsiteSummary(
            ok=False,
            url=normalized,
            error=err,
            artifact_ids=[art["artifact_id"]],
            confidence="low",
        )

    fields = _extract_page_fields(html_text)
    summary_payload = {
        "source_url": normalized,
        "evidence_source": "http_fetch",
        "metadata": fields,
    }
    art = store_research_artifact(
        artifact_type="website_metadata_summary",
        intent="website_summary",
        channel=channel,
        confidence="medium",
        payload=summary_payload,
    )
    return WebsiteSummary(
        ok=True,
        url=normalized,
        title=fields.get("title") or "",
        meta_description=fields.get("meta_description") or "",
        headings=list(fields.get("headings") or []),
        visible_text_preview=str(fields.get("visible_text_preview") or ""),
        links_sample=list(fields.get("links_sample") or []),
        evidence_source="http_fetch",
        artifact_ids=[art["artifact_id"]],
        confidence="medium",
    )


class BrowserBackedResearchProvider:
    def search(self, query: str, *, max_results: int = 5) -> SearchResultSet:
        return SearchResultSet(ok=False, query=query, provider="none", detail="Search not implemented — inspect a URL instead.")

    def summarize_url(self, url: str, *, session_id: str = "default", channel: str = "chat") -> WebsiteSummary:
        from aethos_core.config import get_settings
        from aethos_core.runtime.authority import authority

        normalized = normalize_website_url(url)
        if not normalized:
            return WebsiteSummary(ok=False, url=url, error="Could not normalize URL.", confidence="low")

        http_summary = summarize_url_via_http_fetch(
            normalized,
            session_id=session_id,
            channel=channel,
        )
        if http_summary.ok:
            return http_summary

        if not authority.capabilities.get("browser_automation_enabled"):
            return http_summary

        from aethos_core.browser.runtime.browser_runtime import run_browser_evidence_capture

        capture_type = "full" if get_settings().browser_automation_enabled else "metadata"
        result = run_browser_evidence_capture(
            url=normalized,
            capture_type=capture_type,
            session_id=session_id,
            user_request=f"website summary {normalized}",
            approved=True,
        )
        if not result.get("ok"):
            err = str(result.get("error") or result.get("failure_class") or "capture failed")
            art = store_research_artifact(
                artifact_type="website_metadata_summary",
                intent="website_summary",
                channel=channel,
                confidence="low",
                payload={
                    "source_url": normalized,
                    "evidence_source": "browser_capture_failed",
                    "error": err,
                },
            )
            return WebsiteSummary(
                ok=False,
                url=normalized,
                error=err,
                artifact_ids=[art["artifact_id"]],
                confidence="low",
            )

        meta = result.get("metadata") or {}
        browser_artifact_ids = [a.get("artifact_id") for a in result.get("artifacts") or [] if a.get("artifact_id")]
        screenshot_id = next(
            (a.get("artifact_id") for a in result.get("artifacts") or [] if a.get("artifact_type") == "browser_screenshot"),
            None,
        )
        summary_payload = {
            "source_url": normalized,
            "evidence_source": "browser_metadata",
            "metadata": meta,
            "browser_artifact_ids": browser_artifact_ids,
        }
        art = store_research_artifact(
            artifact_type="website_metadata_summary",
            intent="website_summary",
            channel=channel,
            confidence="medium",
            payload=summary_payload,
        )
        meta_desc = _meta_description(meta.get("meta_tags") or [])
        return WebsiteSummary(
            ok=True,
            url=str(meta.get("url") or normalized),
            title=str(meta.get("title") or ""),
            meta_description=meta_desc,
            headings=[str(h) for h in (meta.get("headings") or [])[:8]],
            visible_text_preview=str(meta.get("visible_text_preview") or "")[:800],
            links_sample=[str(x) for x in (meta.get("links_sample") or [])[:6]],
            evidence_source="browser_metadata",
            artifact_ids=[art["artifact_id"], *browser_artifact_ids],
            screenshot_artifact_id=screenshot_id,
            confidence="medium",
        )


def _meta_description(meta_tags: list[Any]) -> str:
    for tag in meta_tags:
        if not isinstance(tag, dict):
            continue
        name = str(tag.get("name") or tag.get("property") or "").lower()
        if name in ("description", "og:description"):
            return str(tag.get("content") or "")[:400]
    return ""


def format_website_summary_report(summary: WebsiteSummary, *, inspected_label: str | None = None) -> str:
    host = summary.url.replace("https://", "").replace("http://", "").split("/")[0]
    if not summary.ok:
        err = summary.error or "network error"
        if "browser_automation" in err.lower():
            err = (
                "I couldn't read that page directly. "
                "Add a search key in **Connections** if you need broader web research."
            )
        lines = [
            f"I could not reach `{host}`.",
            f"**Reason:** {err}",
            "",
            "**Limitations:** No claims made without evidence.",
        ]
        if summary.artifact_ids:
            lines.append(f"**Artifact:** `{summary.artifact_ids[0]}`")
        return "\n".join(lines)

    source_label = {
        "http_fetch": "by reading the public page directly",
        "browser_metadata": "using browser evidence",
    }.get(summary.evidence_source, f"via {summary.evidence_source}")

    lines = [
        f"I summarized `{host}` {source_label}.",
        "",
        "## High-level summary",
    ]
    if summary.title:
        lines.append(f"- **Title:** {summary.title}")
    if summary.meta_description:
        lines.append(f"- **Description:** {summary.meta_description[:300]}")
    for h in summary.headings[:5]:
        lines.append(f"- **Heading:** {h}")
    preview = (summary.visible_text_preview or "").strip()
    if preview:
        lines.append(f"- **Visible text (preview):** {preview[:400]}")
    if summary.links_sample:
        lines.append(f"- **Links sample:** {', '.join(summary.links_sample[:4])}")
    lines.extend(
        [
            "",
            f"**Evidence source:** {summary.evidence_source}",
            f"**Confidence:** {summary.confidence}",
        ]
    )
    if summary.screenshot_artifact_id:
        lines.append(f"**Screenshot artifact:** `{summary.screenshot_artifact_id}`")
    if summary.artifact_ids:
        lines.append(f"**Research artifact:** `{summary.artifact_ids[0]}`")
    if summary.evidence_source == "browser_metadata":
        lines.append("")
        lines.append("*Governed readonly inspection — no hidden interactions.*")
    return "\n".join(lines)
