# SPDX-License-Identifier: Apache-2.0
"""Minimal stubs replacing deleted conversational_synthesis helpers (§D1)."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.intent_contracts import IntentContract


def validate_constraints(contract: IntentContract, evidence: Any = None) -> dict[str, Any]:
    _ = (contract, evidence)
    return {"ok": True}


def converge_ranking(contract: IntentContract, items: list[Any] | None = None) -> list[Any]:
    _ = contract
    return list(items or [])


def evidence_to_recommendations(evidence: Any, *, contract: IntentContract | None = None) -> list[dict[str, Any]]:
    _ = (evidence, contract)
    return []


def guard_output(text: str = "", **_: Any) -> str:
    return (text or "").strip()


def abstract_evidence(evidence: Any) -> Any:
    return evidence


def strip_internal_sections(text: str = "") -> str:
    return (text or "").strip()


def synthesize_human_response(**_: Any) -> dict[str, Any]:
    return {"ok": True, "polish": "retired"}
