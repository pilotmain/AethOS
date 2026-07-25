# SPDX-License-Identifier: Apache-2.0
"""Per-tenant voice preferences — user-configurable wake phrase + send mode.

The backend flags (voice_surface/input/output/wake) decide what's *available*; these
preferences let each user tailor *how* hands-free mode behaves without touching env:

- ``wake_phrase``  — the phrase that starts listening (e.g. their own choice). User-set.
- ``wake_enabled`` — whether hands-free wake mode is on for this user.
- ``auto_send``    — send the captured speech automatically, or drop it in the box to review.

Stored per tenant in the shared data store. Suggested defaults are provided but the user
owns the phrase.
"""

from __future__ import annotations

from typing import Any

from aethos_core.tenancy import get_current_tenant
from aethos_core.tenancy.tenant_data_store import get_record, set_record

NAMESPACE = "voice_prefs"
RECORD_KEY = "prefs"

# Suggested wake phrases the UI can offer; the user may type their own.
SUGGESTED_WAKE_PHRASES = ["hey aethos", "ok aethos", "aethos listen", "i'm here"]
DEFAULT_WAKE_PHRASE = "hey aethos"
MAX_PHRASE_LEN = 40


def get_voice_preferences(*, tenant_id: str | None = None) -> dict[str, Any]:
    owner = tenant_id or get_current_tenant() or "default"
    rec = get_record(NAMESPACE, RECORD_KEY, tenant_id=owner, default=None) or {}
    return {
        "wake_phrase": str(rec.get("wake_phrase") or "").strip().lower() or DEFAULT_WAKE_PHRASE,
        "wake_enabled": bool(rec.get("wake_enabled", False)),
        "auto_send": bool(rec.get("auto_send", True)),
        "suggested_wake_phrases": SUGGESTED_WAKE_PHRASES,
        "is_custom": bool(rec),
    }


def set_voice_preferences(
    *,
    wake_phrase: str | None = None,
    wake_enabled: bool | None = None,
    auto_send: bool | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    owner = tenant_id or get_current_tenant() or "default"
    cur = get_record(NAMESPACE, RECORD_KEY, tenant_id=owner, default=None) or {}
    if wake_phrase is not None:
        phrase = wake_phrase.strip().lower()[:MAX_PHRASE_LEN]
        cur["wake_phrase"] = phrase or DEFAULT_WAKE_PHRASE
    if wake_enabled is not None:
        cur["wake_enabled"] = bool(wake_enabled)
    if auto_send is not None:
        cur["auto_send"] = bool(auto_send)
    set_record(NAMESPACE, RECORD_KEY, cur, tenant_id=owner)
    return get_voice_preferences(tenant_id=owner)
