# SPDX-License-Identifier: Apache-2.0
"""HTML / visual comparison — inline research when needed, then HTML page."""

from __future__ import annotations

import re

_HTML_RX = re.compile(
    r"\b(html|\.html\b|visual comparison|visual comp|web page|webpage)\b|"
    r"\bcreate\b.*\b(simple\s+)?html\b",
    re.I,
)


def is_comparison_html_request(text: str) -> bool:
    raw = (text or "").strip()
    if len(raw) < 8:
        return False
    if _HTML_RX.search(raw):
        return True
    if "visual" in raw.lower() and "comparison" in raw.lower():
        return True
    return False


def _comparison_query_from_text(text: str) -> str | None:
    """Extract a research query when the message embeds a full A-vs-B comparison."""
    from aethos_core.chat.web_intelligence import is_comparison_research_request
    from aethos_core.research.planner import extract_comparison_subjects, extract_research_query

    raw = (text or "").strip()
    subjects = extract_comparison_subjects(raw)
    if subjects:
        a, b = subjects
        tail = ""
        if re.search(r"\bsecond brain\b", raw, re.I):
            tail = " and tell me which is best for a personal second brain"
        elif re.search(r"\bwhich is best\b", raw, re.I):
            tail = " and tell me which is best"
        return f"compare {a} to {b}{tail}"
    if is_comparison_research_request(raw):
        return extract_research_query(raw) or raw
    return None


def comparison_html_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    if not is_comparison_html_request(text):
        return None

    from aethos_core.research.comparison_html import (
        build_comparison_html,
        comparison_html_public_url,
        load_comparison_context,
        persist_comparison_html,
    )
    from aethos_core.research.research_session_memory import get_last_research_run

    memory = get_last_research_run(session_id)
    replay_id = str((memory or {}).get("replay_id") or "")

    inline_research = False
    if not replay_id:
        research_query = _comparison_query_from_text(text)
        if research_query:
            from aethos_core.research.research_runtime import run_research_query

            run = run_research_query(research_query, session_id=session_id, channel="chat")
            if run.replay_id:
                replay_id = run.replay_id
                inline_research = True
            if not replay_id:
                body = run.reply or (
                    "Web research is not configured. Set `WEB_RESEARCH_ENABLED=true` and a Tavily key, then retry."
                )
                return body, run.intent or "comparison_html_research_failed", _meta(session_id, "")

    if not replay_id:
        body = (
            "I need a comparison topic to build the visual page.\n\n"
            "Try one message like:\n"
            "`give me a visual comparison for GBrain by Garry Tan to Kaparthay's LLM wiki idea "
            "and tell me which is best for a personal second brain`"
        )
        return body, "comparison_html_missing", _meta(session_id, "")

    ctx = load_comparison_context(replay_id)
    if ctx is None:
        body = (
            f"Found replay `{replay_id}` but could not load comparison data. "
            "Re-run the comparison question, then ask for HTML again."
        )
        return body, "comparison_html_load_failed", _meta(session_id, replay_id)

    page = build_comparison_html(ctx)
    saved = persist_comparison_html(replay_id=ctx.replay_id, html=page)
    download_path = str(saved.get("public_url") or comparison_html_public_url(ctx.replay_id))

    intro = (
        f"Ran comparison research and built a **visual page** for **{ctx.subject_a}** vs **{ctx.subject_b}**.\n\n"
        if inline_research
        else f"Here's a simple **visual comparison page** for **{ctx.subject_a}** vs **{ctx.subject_b}**.\n\n"
    )
    body = (
        f"{intro}"
        f"**Recommendation:** {ctx.verdict}\n\n"
        f"**Open in browser:** `{download_path}`\n\n"
        f"Saved on server as `{saved.get('filename') or 'comparison.html'}` "
        f"(folder: `{saved.get('path') or 'data/research_artifacts/comparisons'}`).\n\n"
        f"Copy the block below into `comparison.html` if you prefer a local file:\n\n"
        f"```html\n{page}\n```\n\n"
        f"Replay: `{ctx.replay_id}` · **Mission Control → Research**."
    )
    meta = _meta(session_id, replay_id)
    meta["comparison_html"] = "true"
    meta["comparison_html_url"] = download_path
    meta["comparison_html_file"] = str(saved.get("filename") or "")
    meta["inline_research"] = str(inline_research).lower()
    meta["presentation_mode"] = "direct"
    meta["suppress_governance_footer"] = "true"
    return body, "comparison_html", meta


def _meta(session_id: str, replay_id: str) -> dict[str, str]:
    return {
        "lane": "comparison_html",
        "session_id": session_id,
        "research_replay_id": replay_id,
        "read_only": "true",
    }
