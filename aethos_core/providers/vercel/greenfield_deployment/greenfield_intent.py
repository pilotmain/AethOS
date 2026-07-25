# SPDX-License-Identifier: Apache-2.0
"""Deterministic Vercel greenfield deployment intent detection."""

from __future__ import annotations

import re

_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_DEPLOY_RX = re.compile(r"\b(deploye?|deploy(?:ment)?|redeploy)\b", re.I)
_REMOTE_REPO_VERCEL_RX = re.compile(
    r"\b(?:remote?\s+repo|from\s+(?:remote?\s+)?repo)\b.*\bvercel\b"
    r"|\bvercel\b.*\b(?:remote?\s+repo|from\s+(?:remote?\s+)?repo)\b"
    r"|\bfrom\s+remote?\s+repo\s+to\s+vercel\b",
    re.I,
)
_ENV_SETUP_RX = re.compile(
    r"\b(?:setup|set\s+up|configure)\s+(?:all\s+)?(?:required\s+)?(?:env(?:ironment)?(?:\s+var(?:s)?)?|secrets)\b",
    re.I,
)
_CREATE_PROJECT_RX = re.compile(
    r"\b(?:create|make|provision)\s+(?:a\s+)?(?:new\s+)?(?:vercel\s+)?(?:project)\b"
    r"|\bnew\s+(?:vercel\s+)?project\b",
    re.I,
)
_GREENFIELD_SIGNAL_RX = re.compile(
    r"\b(new\s+project|greenfield|deploy\s+to\s+vercel|deploy\s+on\s+vercel|set\s+required\s+env)\b",
    re.I,
)
_EXISTING_PROJECT_RX = re.compile(r"\b(?:existing|current)\s+(?:vercel\s+)?project\b", re.I)
_READINESS_ONLY_RX = re.compile(r"\bvercel\s+(?:deployment\s+)?readiness\b", re.I)


def is_vercel_greenfield_deployment_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not _VERCEL_RX.search(raw):
        return False
    if _READINESS_ONLY_RX.search(raw) and not _DEPLOY_RX.search(raw):
        return False
    if _EXISTING_PROJECT_RX.search(raw) and not _CREATE_PROJECT_RX.search(raw):
        return False
    if _CREATE_PROJECT_RX.search(raw):
        return True
    if _DEPLOY_RX.search(raw) and _GREENFIELD_SIGNAL_RX.search(raw):
        return True
    if _DEPLOY_RX.search(raw) and re.search(r"\bnew\b", raw, re.I):
        return True
    if _DEPLOY_RX.search(raw) and re.search(r"\bfresh\b", raw, re.I):
        return True
    if _DEPLOY_RX.search(raw) and _deployment_target_alias_in_text(raw):
        return True
    if _REMOTE_REPO_VERCEL_RX.search(raw):
        return True
    if _DEPLOY_RX.search(raw) and _ENV_SETUP_RX.search(raw):
        return True
    if _DEPLOY_RX.search(raw):
        from aethos_core.provider_readonly_intent.readonly_intent_classifier import extract_vercel_project_hint

        if extract_vercel_project_hint(raw):
            return True
    return False


def _deployment_target_alias_in_text(text: str) -> bool:
    try:
        from aethos_core.deployment_targets.registry import match_aliases_in_text

        return match_aliases_in_text(text) is not None
    except Exception:
        return False
