# SPDX-License-Identifier: Apache-2.0
"""Web intelligence lane — intent detection and execution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from aethos_core.research.research_artifacts import store_research_artifact
from aethos_core.research.research_policy import evaluate_web_request


class WebIntentType(str, Enum):
    WEB_SEARCH = "web_search"
    WEBSITE_SUMMARY = "website_summary"
    WEBSITE_METADATA = "website_metadata"
    WEBSITE_EVIDENCE_CAPTURE = "website_evidence_capture"
    WEBSITE_COMPARISON = "website_comparison"
    RESEARCH_SUMMARY = "research_summary"


@dataclass(frozen=True)
class WebIntent:
    intent: WebIntentType
    url: str | None = None
    query: str | None = None


_SEARCH_RX = re.compile(
    r"\b(search the web|search online|can you search|look this up|look up online|browse the web|^search\b)",
    re.I,
)
_RESEARCH_QUERY_RX = re.compile(r"^(?:research|search)\b", re.I)
_WEBSITE_RX = re.compile(
    r"\b(tell me (?:high level )?details about|what is on (?:this )?website|analyze|inspect|summarize)\b|"
    r"\b(?:about|details about)\s+[a-z0-9.-]+\.[a-z]{2,}\b|"
    r"\b[a-z0-9][a-z0-9.-]+\.[a-z]{2,}\b",
    re.I,
)
_RESEARCH_RX = re.compile(r"\bresearch\b", re.I)
_COMPARE_RESEARCH_RX = re.compile(
    r"\bcompare\b|\bvs\.?\b|\bversus\b|\bwhich is best\b|\bwhich one\b|\btell me which\b|\bsecond brain\b",
    re.I,
)
_GENERIC_SEARCH_RX = re.compile(
    r"^(?:can you\s+)?(?:search(?:\s+the\s+web)?(?:\s+now)?|search online|look this up online)\??$",
    re.I,
)


def is_generic_web_search_prompt(text: str) -> bool:
    raw = (text or "").strip()
    if _GENERIC_SEARCH_RX.match(raw):
        return True
    from aethos_core.research.website_summary import extract_search_query

    q = extract_search_query(raw)
    return bool(q and q.strip().lower() == raw.strip().lower())


def is_comparison_research_request(text: str) -> bool:
    raw = (text or "").strip()
    if len(raw) < 16:
        return False
    return bool(_COMPARE_RESEARCH_RX.search(raw))


def classify_web_intent(text: str) -> WebIntent | None:
    raw = (text or "").strip()
    if not raw:
        return None
    from aethos_core.aethos_identity.identity_contract_loader import is_internal_identity_file_prompt

    if is_internal_identity_file_prompt(raw):
        return None
    if not evaluate_web_request(raw).get("allowed") and not is_comparison_research_request(raw):
        return None

    if is_comparison_research_request(raw):
        from aethos_core.research.planner import extract_research_query

        return WebIntent(WebIntentType.RESEARCH_SUMMARY, query=extract_research_query(raw) or raw)

    from aethos_core.browser_observation.browser_observation_router import is_browser_observation_lane_intent
    from aethos_core.browser.runtime.browser_evidence_intents import is_browser_evidence_request

    if is_browser_observation_lane_intent(raw) or is_browser_evidence_request(raw):
        return None

    from aethos_core.research.planner import extract_research_query
    from aethos_core.research.website_summary import extract_search_query, extract_url_from_text

    if _SEARCH_RX.search(raw):
        return WebIntent(WebIntentType.WEB_SEARCH, query=extract_research_query(raw) or extract_search_query(raw) or raw)

    if _RESEARCH_QUERY_RX.search(raw) and not is_generic_web_search_prompt(raw):
        return WebIntent(WebIntentType.RESEARCH_SUMMARY, query=extract_research_query(raw))

    url = extract_url_from_text(raw)
    if url and _WEBSITE_RX.search(raw):
        if re.search(r"\bmetadata\b", raw, re.I):
            return WebIntent(WebIntentType.WEBSITE_METADATA, url=url)
        return WebIntent(WebIntentType.WEBSITE_SUMMARY, url=url)

    if url and not _RESEARCH_RX.search(raw):
        return WebIntent(WebIntentType.WEBSITE_SUMMARY, url=url)

    if _RESEARCH_RX.search(raw) and url:
        return WebIntent(WebIntentType.RESEARCH_SUMMARY, url=url, query=raw)

    if _RESEARCH_RX.search(raw):
        return WebIntent(WebIntentType.RESEARCH_SUMMARY, query=raw)

    return None


def is_web_intelligence_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.aethos_identity.identity_contract_loader import is_internal_identity_file_prompt

    if is_internal_identity_file_prompt(raw):
        return False
    if is_comparison_research_request(raw):
        return evaluate_web_request(raw).get("allowed", True)
    if not evaluate_web_request(raw).get("allowed") and (
        _SEARCH_RX.search(raw) or _WEBSITE_RX.search(raw) or _RESEARCH_RX.search(raw)
    ):
        return True
    return classify_web_intent(raw) is not None


def execute_web_intelligence(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> tuple[str, str, dict[str, str]] | None:
    """Run web intelligence lane — evidence-grounded, no generic LLM denial."""
    policy = evaluate_web_request(text)
    if not policy.get("allowed"):
        art = store_research_artifact(
            artifact_type="research_policy_denial",
            intent="policy_denial",
            channel=channel,
            confidence="high",
            payload={"reason": policy.get("reason"), "user_request": text[:240]},
        )
        body = (
            "# Web intelligence (policy denial)\n\n"
            f"{policy.get('reason')}\n\n"
            f"**Artifact:** `{art['artifact_id']}`"
        )
        return body, "web_intelligence_policy_denial", _meta(channel, art["artifact_id"], "policy_denial")

    intent = classify_web_intent(text)
    if intent is None:
        return None

    from aethos_core.research.research_provider import get_research_provider

    provider = get_research_provider()

    if intent.intent == WebIntentType.WEB_SEARCH:
        if is_generic_web_search_prompt(text):
            return _handle_web_search(text, intent, provider, channel=channel)
        from aethos_core.research.research_runtime import run_research_query

        run = run_research_query(text, session_id=session_id, channel=channel)
        return run.reply, run.intent, run.meta

    if intent.intent == WebIntentType.RESEARCH_SUMMARY and intent.query and not intent.url:
        from aethos_core.research.research_runtime import run_research_query

        run = run_research_query(text, session_id=session_id, channel=channel)
        return run.reply, run.intent, run.meta

    if intent.intent in (WebIntentType.WEBSITE_SUMMARY, WebIntentType.WEBSITE_METADATA, WebIntentType.RESEARCH_SUMMARY):
        if not intent.url:
            body = (
                "I can read and summarize a **specific public URL** directly.\n\n"
                "Try: `summarize pilotmain.com` or `inspect https://example.com`"
            )
            return body, "website_summary_help", _meta(channel, "", "website_summary")

        from aethos_core.research.website_summary import format_website_summary_report

        summary = provider.summarize_url(intent.url, session_id=session_id, channel=channel)
        body = format_website_summary_report(summary)
        art_id = summary.artifact_ids[0] if summary.artifact_ids else ""
        return body, "website_summary", _meta(channel, art_id, intent.intent.value, url=intent.url, confidence=summary.confidence)

    return None


def _handle_web_search(
    text: str,
    intent: WebIntent,
    provider: Any,
    *,
    channel: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.config import get_settings
    from aethos_core.research.research_config import (
        build_research_status,
        format_incomplete_config_message,
        is_research_search_configured,
    )
    from aethos_core.research.provider_factory import research_provider_label

    settings = get_settings()
    query = intent.query or text

    if is_generic_web_search_prompt(text):
        if is_research_search_configured(settings):
            label = research_provider_label(settings).capitalize()
            body = "\n".join(
                [
                    f"**Research provider configured:** {label}.",
                    "",
                    "What would you like me to search?",
                    "",
                    'Example: `"Search the web for latest Railway deployment docs"`',
                ]
            )
            return body, "web_search_ready", _meta(channel, "", "web_search", configured="true")
        if not settings.web_research_enabled:
            body = "\n".join(
                [
                    "**Web research is disabled.**",
                    "",
                    "Set in `.env`:",
                    "```",
                    "WEB_RESEARCH_ENABLED=true",
                    "WEB_SEARCH_PROVIDER=tavily",
                    "WEB_SEARCH_API_KEY=your_tavily_key_here",
                    "```",
                    "",
                    "Then restart the API.",
                    "",
                    "I can still read and summarize a **specific public URL** directly.",
                ]
            )
            return body, "web_search_disabled", _meta(channel, "", "web_search")
        body = format_incomplete_config_message(settings)
        art = store_research_artifact(
            artifact_type="web_search_result_set",
            intent="web_search",
            channel=channel,
            confidence="high",
            payload={"query": query, "configured": False, "status": build_research_status(settings)},
        )
        return body, "web_search_not_configured", _meta(channel, art["artifact_id"], "web_search")

    results = provider.search(query, max_results=settings.web_research_max_results)
    if not results.ok:
        status = build_research_status(settings)
        art = store_research_artifact(
            artifact_type="web_search_result_set",
            intent="web_search",
            channel=channel,
            confidence="high",
            payload={
                "query": query,
                "configured": status.get("configured"),
                "detail": results.detail,
                "status": status,
            },
        )
        if settings.web_research_enabled and not status.get("configured"):
            body = format_incomplete_config_message(settings)
            body += f"\n\n**Artifact:** `{art['artifact_id']}`"
            return body, "web_search_not_configured", _meta(channel, art["artifact_id"], "web_search")

        body = "\n".join(
            [
                f"**Web search failed** ({results.provider}).",
                "",
                f"**Detail:** {results.detail or 'unknown error'}",
                "",
                "I can still read and summarize a **specific public URL** directly.",
                "",
                f"**Artifact:** `{art['artifact_id']}`",
            ]
        )
        return body, "web_search_failed", _meta(channel, art["artifact_id"], "web_search")

    art = store_research_artifact(
        artifact_type="web_search_result_set",
        intent="web_search",
        channel=channel,
        confidence="medium",
        payload={
            "query": query,
            "results": [r.__dict__ for r in results.results],
            "provider": results.provider,
            "configured": True,
        },
    )
    lines = [
        f"**Web search** ({results.provider}): {query}",
        "",
        f"**Evidence source:** {results.provider} API",
        f"**Confidence:** medium",
        "",
    ]
    if not results.results:
        lines.append("_No results returned._")
    for r in results.results[: settings.web_research_max_results]:
        lines.append(f"- **{r.title}** — {r.url}\n  {r.snippet[:200]}")
    lines.append(f"\n**Artifact:** `{art['artifact_id']}`")
    return "\n".join(lines), "web_search", _meta(channel, art["artifact_id"], "web_search")


def _meta(channel: str, artifact_id: str, intent: str, **extra: str) -> dict[str, str]:
    meta = {
        "lane": "web_intelligence",
        "web_intelligence": "true",
        "channel": channel,
        "research_artifact_id": artifact_id,
        "web_intent_type": intent,
    }
    meta.update({k: str(v) for k, v in extra.items() if v})
    return meta
