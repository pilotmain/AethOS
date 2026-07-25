# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    AUTHORITY_FLAGS,
    IDENTITY_HIERARCHY,
    IDENTITY_TRUTH_LOCK_DOMAINS,
    IDENTITY_TRUTH_LOCK_FIX,
    build_creator_attribution_registry,
    build_platform_identity_registry,
    build_provider_attribution_registry,
)
from aethos_core.identity_truth_lock.identity_truth_lock_evaluator import (
    build_identity_truth_validation_report,
    detect_identity_drift,
)
from aethos_core.identity_truth_lock.identity_truth_lock_responses import (
    compose_creator_introduction_response,
    compose_self_introduction_response,
)
from aethos_core.identity_truth_lock.identity_truth_lock_store import list_identity_review_records
from aethos_core.identity_truth_lock.runtime_identity_lock import build_runtime_identity_lock
from aethos_core.identity_truth_lock.runtime_provider_context import resolve_runtime_provider_context


@dataclass(frozen=True)
class IdentityTruthLockResult:
    identity_truth_lock: dict[str, Any]

    @property
    def sections(self) -> dict[str, Any]:
        return self.identity_truth_lock.get("sections") or {}


def build_identity_truth_lock(*, session_id: str = "default", sample_text: str = "") -> IdentityTruthLockResult:
    ctx = resolve_runtime_provider_context()
    runtime_provider = str(ctx["display_provider"])
    runtime_model = str(ctx["display_model"])

    platform_identity_registry = build_platform_identity_registry()
    creator_attribution_registry = build_creator_attribution_registry()
    provider_attribution_registry = build_provider_attribution_registry(
        runtime_provider=runtime_provider,
        runtime_model=runtime_model,
    )
    identity_truth_validation_report = build_identity_truth_validation_report(
        runtime_provider=runtime_provider,
        runtime_model=runtime_model,
    )
    identity_drift_report = detect_identity_drift(text=sample_text)
    self_introduction_package = {
        "markdown": compose_self_introduction_response(session_id=session_id, include_provider=False),
        "includes": (
            "identity",
            "mission",
            "capabilities",
            "trust_boundaries",
            "human_oversight",
            "creator_attribution",
        ),
    }
    creator_introduction_package = {
        "markdown": compose_creator_introduction_response(),
        "includes": ("creator", "vision", "purpose", "governance_philosophy"),
        "provider_ownership_claims_forbidden": True,
    }
    runtime_identity_lock = build_runtime_identity_lock(
        runtime_provider=runtime_provider,
        runtime_model=runtime_model,
    )
    identity_dashboard = {
        "platform": platform_identity_registry["name"],
        "creator": creator_attribution_registry["creator"],
        "owner": creator_attribution_registry["owner"],
        "provider": runtime_provider,
        "runtime_model": runtime_model,
        "trust_status": identity_truth_validation_report["overall_ok"],
        "identity_validation": identity_truth_validation_report["checks"],
        "identity_hierarchy": [dict(row) for row in IDENTITY_HIERARCHY],
        "authority_flags": dict(AUTHORITY_FLAGS),
    }
    identity_review_registry = {
        "records": list_identity_review_records(),
        "commands": (
            "identity note: ...",
            "identity review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "platform_identity_registry": platform_identity_registry,
        "creator_attribution_registry": creator_attribution_registry,
        "provider_attribution_registry": provider_attribution_registry,
        "identity_truth_validation_report": identity_truth_validation_report,
        "identity_drift_report": identity_drift_report,
        "self_introduction_package": self_introduction_package,
        "creator_introduction_package": creator_introduction_package,
        "runtime_identity_lock": runtime_identity_lock,
        "identity_dashboard": identity_dashboard,
        "identity_review_registry": identity_review_registry,
    }

    return IdentityTruthLockResult(
        identity_truth_lock={
            "fix": IDENTITY_TRUTH_LOCK_FIX,
            "session_id": (session_id or "default").strip()[:64] or "default",
            "domains": list(IDENTITY_TRUTH_LOCK_DOMAINS),
            "sections": sections,
        }
    )
