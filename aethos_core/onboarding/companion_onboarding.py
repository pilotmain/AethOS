# SPDX-License-Identifier: Apache-2.0
"""Unified companion onboarding flow (Phase 9.5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings


@dataclass
class OnboardingStep:
    id: str
    title: str
    status: str
    doc: str
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "doc": self.doc,
            "completed": self.completed,
        }


@dataclass
class CompanionOnboardingState:
    ok: bool
    progress: float
    steps: list[OnboardingStep] = field(default_factory=list)
    next_step: OnboardingStep | None = None
    privacy_acknowledged: bool = False
    capabilities_summary: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "progress": self.progress,
            "steps": [s.to_dict() for s in self.steps],
            "next_step": self.next_step.to_dict() if self.next_step else None,
            "privacy_acknowledged": self.privacy_acknowledged,
            "capabilities_summary": self.capabilities_summary,
            "phase": "9.5",
        }


def build_companion_onboarding_state() -> CompanionOnboardingState:
    s = get_settings()
    steps = [
        OnboardingStep("doctor", "Environment doctor", "recommended", "docs/GETTING_STARTED.md"),
        OnboardingStep("credentials", "Provider credentials", "optional", "docs/GETTING_STARTED.md"),
        OnboardingStep("channels", "Channel setup", "optional", "docs/OPERATOR_GATEWAY_CLI.md"),
        OnboardingStep("governance", "Governance acknowledgment", "required", "docs/AETHOS_GOVERNANCE_FRICTION_AND_APPROVAL_PRINCIPLE.md"),
    ]
    completed_flags = [
        bool(getattr(s, "aethos_operator_break_glass_acknowledged", False) or getattr(s, "aethos_local_env_trusted", False)),
        bool(getattr(s, "railway_api_token", None) or getattr(s, "github_token", None)),
        bool(getattr(s, "telegram_enabled", False) or getattr(s, "slack_enabled", False)),
        bool(getattr(s, "aethos_operator_break_glass_acknowledged", False)),
    ]
    for step, done in zip(steps, completed_flags, strict=False):
        step.completed = done
        step.status = "done" if done else step.status

    done_count = sum(1 for st in steps if st.completed)
    progress = done_count / len(steps) if steps else 0.0
    next_step = next((st for st in steps if not st.completed), None)

    return CompanionOnboardingState(
        ok=True,
        progress=round(progress, 3),
        steps=steps,
        next_step=next_step,
        privacy_acknowledged=bool(getattr(s, "aethos_operator_break_glass_acknowledged", False)),
        capabilities_summary=[
            "Governed cloud readonly (Railway · GitHub · Vercel)",
            "Software delivery loop with human merge",
            "Mission Control approval inbox",
        ],
    )
