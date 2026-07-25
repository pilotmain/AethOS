# SPDX-License-Identifier: Apache-2.0
"""Hypothesis graph evolution."""

from __future__ import annotations

from aethos_core.world_model.investigation_state import Hypothesis, InvestigationState

_CATEGORY_TO_HYPOTHESIS: dict[str, tuple[str, str]] = {
    "database_startup_or_storage_activity": ("storage_startup_issue", "storage/startup issue"),
    "database_storage_issue": ("storage_corruption_issue", "storage corruption/disk issue"),
    "database_startup_failure": ("database_startup_failure", "database startup failure"),
    "storage_permission_issue": ("storage_permission_issue", "storage permission issue"),
    "missing_env_variable": ("missing_env_issue", "missing environment variable"),
    "resource_pressure": ("resource_pressure_issue", "resource pressure / OOM"),
    "crash_loop": ("crash_loop_issue", "crash loop"),
    "network_dependency_issue": ("network_dependency_issue", "dependency connectivity issue"),
    "authentication_or_secret_issue": ("auth_secret_issue", "authentication/secret issue"),
    "build_failure": ("build_failure_issue", "build failure"),
    "insufficient_evidence": ("unknown_failure", "unconfirmed failure cause"),
    "unknown_runtime_failure": ("unknown_failure", "unknown runtime failure"),
}


def evolve_hypotheses(
    state: InvestigationState,
    *,
    root_category: str,
    confidence_score: float,
    new_evidence: list[str],
) -> InvestigationState:
    hypo_type, label = _CATEGORY_TO_HYPOTHESIS.get(root_category, ("unknown_failure", "unconfirmed failure cause"))
    incoming = Hypothesis(type=hypo_type, confidence=confidence_score, status="active", label=label)

    merged: dict[str, Hypothesis] = {item.type: item for item in state.hypotheses if item.status != "decayed"}
    existing = merged.get(incoming.type)
    if existing:
        incoming.confidence = max(existing.confidence, incoming.confidence)
        if _supports_hypothesis(new_evidence, incoming.type):
            incoming.confidence = min(1.0, incoming.confidence + 0.08)
    merged[incoming.type] = incoming

    for key, item in list(merged.items()):
        if key == incoming.type:
            continue
        if incoming.confidence - item.confidence >= 0.2:
            item.status = "decayed"
            item.confidence = max(0.05, item.confidence * 0.6)
        elif item.confidence < 0.25:
            item.status = "decayed"

    ranked = sorted(merged.values(), key=lambda h: h.confidence, reverse=True)
    state.hypotheses = ranked[:5]
    return state


def leading_hypothesis(state: InvestigationState) -> Hypothesis | None:
    active = [item for item in state.hypotheses if item.status == "active"]
    if not active:
        return None
    return sorted(active, key=lambda h: h.confidence, reverse=True)[0]


def _supports_hypothesis(evidence: list[str], hypo_type: str) -> bool:
    joined = " ".join(evidence).lower()
    if hypo_type == "storage_corruption_issue":
        return any(token in joined for token in ("disk", "corrupt", "fatal", "permission"))
    if hypo_type == "crash_loop_issue":
        return any(token in joined for token in ("exit_code", "crash", "exited"))
    if hypo_type == "missing_env_issue":
        return "missing_env" in joined or "env" in joined
    return False
