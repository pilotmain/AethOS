# SPDX-License-Identifier: Apache-2.0
"""Phase 9.6 capability foundation chat handlers."""

from __future__ import annotations

import re

from aethos_core.channels.registry import format_channel_summary
from aethos_core.local_repo.inventory import format_repo_status_report, git_status_readonly, resolve_repo_root
from aethos_core.screenshot.artifact import capture_screenshot_evidence
from aethos_core.social.drafts import draft_social_post


_CHANNELS_RX = re.compile(r"\bshow\s+supported\s+channels\b", re.I)
_LOCAL_REPO_RX = re.compile(
    r"\bshow\s+local\s+repo\s+status\b|\blocal\s+repo\s+status\b.*\bfor\b",
    re.I,
)
_SCREENSHOT_RX = re.compile(
    r"\bcapture\s+screenshot\s+evidence\b|\bscreenshot\s+evidence\b.*\bmission\s+control\b",
    re.I,
)
_SOCIAL_DRAFT_RX = re.compile(
    r"\bdraft\b.*\b(linkedin|twitter|x|facebook|instagram)\b.*\bpost\b|"
    r"\bdraft\b.*\bpost\b.*\b(linkedin|twitter|x)\b",
    re.I,
)


def _extract_repo_hint(text: str) -> str | None:
    m = re.search(r"\bfor\s+([A-Za-z0-9._-]+)\b", text)
    return m.group(1) if m else None


def _extract_platform(text: str) -> str:
    lower = text.lower()
    for p in ("linkedin", "twitter", "facebook", "instagram", "x"):
        if p in lower:
            return "x" if p == "x" else p
    return "social"


def capability_foundation_reply(text: str) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.chat.engineering_intelligence import is_engineering_intelligence_request

    if is_engineering_intelligence_request(raw):
        return None

    if _CHANNELS_RX.search(raw):
        return format_channel_summary(), "supported_channels", {}

    if _LOCAL_REPO_RX.search(raw):
        hint = _extract_repo_hint(raw)
        root = resolve_repo_root(hint)
        if root is None:
            return (
                "Local repo status is **readonly-only**. No git repository found for that hint. "
                "Run from a git checkout or pass a valid path.",
                "local_repo_not_configured",
                {"read_only": "true"},
            )
        payload = git_status_readonly(root)
        report = format_repo_status_report(root, payload)
        return report, "local_repo_status", {"read_only": "true", "path": str(root)}

    if _SCREENSHOT_RX.search(raw):
        artifact = capture_screenshot_evidence(target="Mission Control", configured=False)
        return (
            f"Screenshot evidence: **not configured** in this deployment (`{artifact.reason}`). "
            "No hidden browser action was performed.",
            "screenshot_evidence",
            artifact.to_dict(),
        )

    if _SOCIAL_DRAFT_RX.search(raw):
        platform = _extract_platform(raw)
        topic = "AethOS update"
        if "9.3m" in raw.lower():
            topic = "AethOS 9.3M passing orchestration convergence"
        draft = draft_social_post(platform=platform, topic=topic)
        return (
            f"**Social draft ({platform})** — approval required · **not published**\n\n"
            f"{draft.body}",
            "social_draft",
            draft.to_dict(),
        )

    return None
