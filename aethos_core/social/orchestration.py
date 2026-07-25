# SPDX-License-Identifier: Apache-2.0
"""Social draft orchestration — approval-gated, no publish (Phase 9.5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.social.drafts import SocialPostDraft, draft_social_post

_DRAFT_STORE: list[dict[str, Any]] = []


@dataclass
class SocialDraftScheduleResult:
    ok: bool
    draft_id: str
    draft: dict[str, Any] = field(default_factory=dict)
    status: str = "pending_approval"
    published: bool = False
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "draft_id": self.draft_id,
            "draft": self.draft,
            "status": self.status,
            "published": self.published,
            "detail": self.detail,
            "execution_enabled": False,
            "phase": "9.5",
        }


def schedule_social_draft(*, platform: str, topic: str, author: str = "operator") -> SocialDraftScheduleResult:
    body = draft_social_post(platform=platform, topic=topic)
    draft_id = f"social-{uuid4().hex[:12]}"
    record = {
        "draft_id": draft_id,
        "platform": platform,
        "topic": topic,
        "author": author,
        "created_at": time(),
        "status": "pending_approval",
        "body": body.body,
        "published": False,
    }
    _DRAFT_STORE.append(record)
    return SocialDraftScheduleResult(
        ok=True,
        draft_id=draft_id,
        draft=body.to_dict(),
        status="pending_approval",
        published=False,
        detail="Social draft queued for approval — publishing remains disabled.",
    )


def list_social_drafts(*, limit: int = 20) -> list[dict[str, Any]]:
    return list(reversed(_DRAFT_STORE[-limit:]))


def clear_social_drafts_for_tests() -> None:
    _DRAFT_STORE.clear()
