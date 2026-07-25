# SPDX-License-Identifier: Apache-2.0
"""Confidence scoring for Vercel project candidates — conservative but useful."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from aethos_core.browser.platforms.vercel.vercel_navigation_map import (
    is_nav_label,
    is_platform_feature_slug,
    is_usage_metric_slug,
)

CONFIRMED_THRESHOLD = 5
LIKELY_THRESHOLD = 3
LOW_CONFIDENCE_THRESHOLD = 1

_SCORE_PROJECT_CARD = 4
_SCORE_PRODUCTION = 2
_SCORE_REPO = 2
_SCORE_DEPLOY_HINT = 1
_SCORE_MEMORY_BOOST = 3
_SCORE_PENALTY_PRODUCT = -5
_SCORE_PENALTY_NO_META = -2
_SCORE_PENALTY_TEXT_ONLY = -1


@dataclass
class ProjectCandidate:
    name: str
    score: int = 0
    href: str | None = None
    card_text: str = ""
    from_dom: bool = False
    signals: list[str] = field(default_factory=list)
    rejection_reason: str | None = None

    def add(self, points: int, signal: str) -> None:
        self.score += points
        self.signals.append(signal)


@dataclass
class CandidateBuckets:
    confirmed: list[ProjectCandidate] = field(default_factory=list)
    likely: list[ProjectCandidate] = field(default_factory=list)
    low_confidence: list[ProjectCandidate] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)


def score_candidate(
    name: str,
    *,
    href: str | None = None,
    card_text: str = "",
    from_dom: bool = False,
    from_text_fallback: bool = False,
    memory_confirmed: bool = False,
) -> ProjectCandidate | None:
    key = (name or "").strip().lower()
    if not key or is_nav_label(key) or is_platform_feature_slug(key) or is_usage_metric_slug(key):
        return None

    c = ProjectCandidate(name=key, href=href, card_text=card_text, from_dom=from_dom)

    if from_dom:
        c.add(_SCORE_PROJECT_CARD, "project_link_dom")
    if from_text_fallback:
        c.add(_SCORE_PENALTY_TEXT_ONLY, "text_fallback_only")
    if memory_confirmed:
        c.add(_SCORE_MEMORY_BOOST, "memory_confirmed_boost")

    text = card_text or ""
    if href and re.search(r"vercel\.com/[^/]+/" + re.escape(key), href, re.I):
        c.add(1, "project_href_shape")
    if href and re.search(rf"vercel\.com/{re.escape(key)}(?:/|$)", href, re.I):
        c.add(1, "project_href_direct")

    if ".vercel.app" in (href or "") or re.search(r"\b[\w.-]+\.vercel\.app\b", text, re.I):
        c.add(_SCORE_PRODUCTION, "production_url")
    if re.search(r"github\.com/[\w.-]+/[\w.-]+", text, re.I):
        c.add(_SCORE_REPO, "repo_hint")
    if re.search(
        r"\b(failed|ready|building|deploy|production|preview|no production)\b", text, re.I
    ):
        c.add(_SCORE_DEPLOY_HINT, "deploy_hint")

    if not from_dom and not memory_confirmed and len(c.signals) <= 1:
        c.add(_SCORE_PENALTY_NO_META, "no_metadata")

    if is_platform_feature_slug(key) or is_usage_metric_slug(key):
        c.add(_SCORE_PENALTY_PRODUCT, "product_slug")

    return c


def bucket_candidates(
    candidates: dict[str, ProjectCandidate],
) -> CandidateBuckets:
    confirmed: list[ProjectCandidate] = []
    likely: list[ProjectCandidate] = []
    low_confidence: list[ProjectCandidate] = []
    ignored: list[str] = []

    for c in sorted(candidates.values(), key=lambda x: (-x.score, x.name)):
        if c.score >= CONFIRMED_THRESHOLD:
            confirmed.append(c)
        elif c.score >= LIKELY_THRESHOLD:
            likely.append(c)
        elif c.score >= LOW_CONFIDENCE_THRESHOLD:
            low_confidence.append(c)
        else:
            c.rejection_reason = f"score {c.score} below threshold"
            ignored.append(c.name)

    return CandidateBuckets(
        confirmed=confirmed,
        likely=likely,
        low_confidence=low_confidence,
        ignored=ignored,
    )


def split_confirmed_and_ignored(
    candidates: dict[str, ProjectCandidate],
) -> tuple[list[ProjectCandidate], list[str]]:
    """Legacy helper — returns confirmed+likely as accepted, rest ignored."""
    buckets = bucket_candidates(candidates)
    accepted = buckets.confirmed + buckets.likely
    ignored = [c.name for c in buckets.low_confidence] + buckets.ignored
    return accepted, ignored
