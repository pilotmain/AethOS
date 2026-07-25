# SPDX-License-Identifier: Apache-2.0
"""Social drafting — approval-gated, no publishing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SocialPostDraft:
    platform: str
    body: str
    approval_required: bool = True
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "body": self.body,
            "approval_required": self.approval_required,
            "execution_enabled": self.execution_enabled,
            "published": False,
        }


def draft_social_post(*, platform: str, topic: str) -> SocialPostDraft:
    body = (
        f"Draft post about {topic} — **not published**. "
        "Approval required before any social mutation is enabled."
    )
    return SocialPostDraft(platform=platform, body=body)
