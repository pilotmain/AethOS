# SPDX-License-Identifier: Apache-2.0
"""Per-user voice preferences: user-chosen wake phrase + send mode, persisted per tenant
and merged into the voice surface config (overriding env defaults)."""

from __future__ import annotations

from uuid import uuid4

import aethos_core.voice.preferences as vp
from aethos_core.tenancy import tenant_scope


def _t() -> str:
    return f"voice-{uuid4().hex}@example.com"


def test_defaults_when_unset():
    with tenant_scope(_t()):
        p = vp.get_voice_preferences()
    assert p["wake_phrase"] == vp.DEFAULT_WAKE_PHRASE
    assert p["auto_send"] is True
    assert p["wake_enabled"] is False
    assert p["suggested_wake_phrases"]  # suggestions offered


def test_set_custom_wake_phrase_and_send_mode():
    t = _t()
    with tenant_scope(t):
        vp.set_voice_preferences(wake_phrase="Daddy Home", wake_enabled=True, auto_send=False)
        p = vp.get_voice_preferences()
    assert p["wake_phrase"] == "daddy home"  # normalized
    assert p["wake_enabled"] is True
    assert p["auto_send"] is False
    assert p["is_custom"] is True


def test_preferences_are_tenant_scoped():
    a, b = _t(), _t()
    with tenant_scope(a):
        vp.set_voice_preferences(wake_phrase="open sesame")
    with tenant_scope(b):
        assert vp.get_voice_preferences()["wake_phrase"] == vp.DEFAULT_WAKE_PHRASE


def test_partial_update_preserves_other_fields():
    t = _t()
    with tenant_scope(t):
        vp.set_voice_preferences(wake_phrase="hi there", wake_enabled=True, auto_send=False)
        vp.set_voice_preferences(auto_send=True)  # only change auto_send
        p = vp.get_voice_preferences()
    assert p["wake_phrase"] == "hi there" and p["wake_enabled"] is True and p["auto_send"] is True
