# SPDX-License-Identifier: Apache-2.0
"""Screenshot evidence artifacts — auditable, non-destructive."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScreenshotArtifact:
    target: str
    captured: bool
    reason: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "captured": self.captured,
            "reason": self.reason,
            "metadata": self.metadata,
            "evidence_type": "screenshot",
            "mutating": False,
        }


def capture_screenshot_evidence(*, target: str, configured: bool = False) -> ScreenshotArtifact:
    if not configured:
        return ScreenshotArtifact(
            target=target,
            captured=False,
            reason="screenshot_capture_not_configured",
            metadata={"phase": "9.8B", "hint": "Enable BROWSER_AUTOMATION_ENABLED"},
        )

    from aethos_core.browser.runtime.browser_runtime import normalize_target_url, run_browser_evidence_capture

    url = normalize_target_url(target)
    if not url:
        return ScreenshotArtifact(
            target=target,
            captured=False,
            reason="invalid_target_url",
            metadata={"phase": "9.8B"},
        )

    result = run_browser_evidence_capture(url=url, capture_type="screenshot", user_request=f"screenshot {target}")
    if not result.get("ok"):
        policy = result.get("policy") or {}
        return ScreenshotArtifact(
            target=target,
            captured=False,
            reason=str(policy.get("failure_class") or result.get("error") or "capture_failed"),
            metadata={"phase": "9.8B", "policy": policy, "timeline": result.get("timeline")},
        )

    artifacts = result.get("artifacts") or []
    screenshot = next((a for a in artifacts if a.get("artifact_type") == "browser_screenshot"), None)
    return ScreenshotArtifact(
        target=target,
        captured=True,
        reason="browser_evidence_captured",
        metadata={
            "phase": "9.8B",
            "artifact_id": (screenshot or {}).get("artifact_id"),
            "artifacts": [a.get("artifact_id") for a in artifacts],
            "page": result.get("metadata") or {},
        },
    )
