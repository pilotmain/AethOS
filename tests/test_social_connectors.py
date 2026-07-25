# SPDX-License-Identifier: Apache-2.0
"""Social connector framework: platform registry, approval-gated + connection-gated publishing,
and honest 'not wired' for platforms without a publisher. Nothing auto-posts."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.social import connectors as sc
from aethos_core.social.platforms import normalize_platform, platform_spec, supported_platform_names


def test_platform_registry_and_aliases():
    assert "x" in supported_platform_names() and "linkedin" in supported_platform_names()
    assert normalize_platform("twitter") == "x"
    assert normalize_platform("IG") == "instagram"
    assert platform_spec("x").char_limit == 280


def test_publish_requires_approval():
    out = sc.publish_to_platform("x", "hello world", approved=False)
    assert out["ok"] is False and out["error"] == "approval_required"


def test_publish_requires_connection():
    with patch.object(sc, "_resolve_token", return_value=None):
        out = sc.publish_to_platform("x", "hello", approved=True)
    assert out["ok"] is False and out["error"] == "not_connected"


def test_publish_enforces_char_limit():
    out = sc.publish_to_platform("x", "z" * 281, approved=True)
    assert out["ok"] is False and out["error"] == "too_long"


def test_publish_dispatches_when_approved_and_connected():
    with patch.object(sc, "_resolve_token", return_value="tok"):
        with patch.dict(sc._PUBLISHERS, {"x": lambda token, text: {"ok": True, "platform": "x", "post_id": "1", "published": True}}):
            out = sc.publish_to_platform("x", "hello world", approved=True)
    assert out["ok"] is True and out["published"] is True


def test_unwired_platform_is_honest_not_fake():
    # LinkedIn has a token but no publisher wired → honest error, never a fake "published".
    with patch.object(sc, "_resolve_token", return_value="tok"):
        out = sc.publish_to_platform("linkedin", "hello", approved=True)
    assert out["ok"] is False and out["error"] == "publisher_not_wired"
