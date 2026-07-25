# SPDX-License-Identifier: Apache-2.0
"""Canonical execution receipt statuses — simulated vs live mutation."""

from __future__ import annotations

from typing import Any

# Dry-run / disabled simulated path
STATUS_SIMULATED_SUCCESS = "simulated_success"
STATUS_SIMULATED_FAILURE = "simulated_failure"
STATUS_SIMULATED = "simulated"

# Live mutation path (FIX 108+)
STATUS_MUTATION_SUCCESS = "mutation_success"
STATUS_MUTATION_FAILURE = "mutation_failure"
STATUS_MUTATION_SKIPPED = "mutation_skipped"

MUTATION_RECEIPT_STATUSES = frozenset(
    {
        STATUS_MUTATION_SUCCESS,
        STATUS_MUTATION_FAILURE,
        STATUS_MUTATION_SKIPPED,
    }
)

SIMULATED_RECEIPT_STATUSES = frozenset(
    {
        STATUS_SIMULATED_SUCCESS,
        STATUS_SIMULATED_FAILURE,
        STATUS_SIMULATED,
    }
)

# FIX 110 — dry-run rollback receipts (never live mutation until FIX 111).
STATUS_ROLLBACK_SIMULATED_SUCCESS = "rollback_simulated_success"
STATUS_ROLLBACK_SIMULATED_FAILURE = "rollback_simulated_failure"
STATUS_ROLLBACK_SIMULATED_SKIPPED = "rollback_simulated_skipped"

ROLLBACK_SIMULATED_RECEIPT_STATUSES = frozenset(
    {
        STATUS_ROLLBACK_SIMULATED_SUCCESS,
        STATUS_ROLLBACK_SIMULATED_FAILURE,
        STATUS_ROLLBACK_SIMULATED_SKIPPED,
    }
)

# FIX 111 — live rollback receipts (disconnect_repo_source only).
STATUS_ROLLBACK_MUTATION_SUCCESS = "rollback_mutation_success"
STATUS_ROLLBACK_MUTATION_FAILURE = "rollback_mutation_failure"
STATUS_ROLLBACK_MUTATION_SKIPPED = "rollback_mutation_skipped"
STATUS_ROLLBACK_PARTIAL_FAILURE = "rollback_partial_failure"

ROLLBACK_MUTATION_RECEIPT_STATUSES = frozenset(
    {
        STATUS_ROLLBACK_MUTATION_SUCCESS,
        STATUS_ROLLBACK_MUTATION_FAILURE,
        STATUS_ROLLBACK_MUTATION_SKIPPED,
        STATUS_ROLLBACK_PARTIAL_FAILURE,
    }
)


def normalize_receipt_status(receipt: dict[str, Any]) -> dict[str, Any]:
    """Map legacy statuses to canonical simulated/mutation values."""
    status = str(receipt.get("status") or "")
    if (
        status in MUTATION_RECEIPT_STATUSES
        or status in SIMULATED_RECEIPT_STATUSES
        or status in ROLLBACK_SIMULATED_RECEIPT_STATUSES
        or status in ROLLBACK_MUTATION_RECEIPT_STATUSES
        or status in VERIFICATION_READONLY_RECEIPT_STATUSES
    ):
        return receipt
    mutation_performed = bool(receipt.get("mutation_performed"))
    replayed = bool(receipt.get("replayed"))
    if mutation_performed:
        receipt["status"] = STATUS_MUTATION_FAILURE if status == "failed" else STATUS_MUTATION_SUCCESS
    elif replayed or status in {"skipped", "completed"}:
        receipt["status"] = STATUS_MUTATION_SKIPPED
    elif status in {"simulated_failure", "failed"}:
        receipt["status"] = STATUS_SIMULATED_FAILURE
    elif status in {"simulated_success", "simulated"}:
        receipt["status"] = STATUS_SIMULATED_SUCCESS if status == "simulated_success" else STATUS_SIMULATED
    return receipt


def phase_mutation_recorded(receipt: dict[str, Any] | None) -> bool:
    """True when create_service must not invoke serviceCreate again (success or skipped)."""
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    status = str(receipt.get("status") or "")
    if status in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED}:
        return True
    return bool(receipt.get("mutation_performed")) and status == STATUS_MUTATION_SUCCESS


def receipt_is_simulated(receipt: dict[str, Any]) -> bool:
    status = str(receipt.get("status") or "")
    return status in SIMULATED_RECEIPT_STATUSES or (
        not receipt.get("mutation_performed") and status.startswith("simulated")
    )


def receipt_is_live_mutation(receipt: dict[str, Any]) -> bool:
    receipt = normalize_receipt_status(dict(receipt))
    return bool(receipt.get("mutation_performed")) or str(receipt.get("status") or "") in MUTATION_RECEIPT_STATUSES


def rollback_phase_recorded(receipt: dict[str, Any] | None) -> bool:
    """True when rollback receipt means do not re-run rollback for this phase."""
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    status = str(receipt.get("status") or "")
    if status in {
        STATUS_ROLLBACK_SIMULATED_SUCCESS,
        STATUS_ROLLBACK_SIMULATED_SKIPPED,
        STATUS_ROLLBACK_MUTATION_SUCCESS,
        STATUS_ROLLBACK_MUTATION_SKIPPED,
        STATUS_ROLLBACK_PARTIAL_FAILURE,
    }:
        return True
    return status == STATUS_SIMULATED_SUCCESS and str(receipt.get("phase") or "").startswith("rollback_")


def receipt_is_live_rollback_mutation(receipt: dict[str, Any]) -> bool:
    receipt = normalize_receipt_status(dict(receipt))
    return bool(receipt.get("mutation_performed")) or str(receipt.get("status") or "") in ROLLBACK_MUTATION_RECEIPT_STATUSES


def forward_live_create_service_mutation_recorded(receipt: dict[str, Any] | None) -> bool:
    """True when create_service was applied via governed live mutation."""
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    if str(receipt.get("phase") or "") != "create_service":
        return False
    status = str(receipt.get("status") or "")
    if status in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED} and receipt_is_live_mutation(receipt):
        return True
    return bool(receipt.get("mutation_performed")) and status == STATUS_MUTATION_SUCCESS


def forward_live_connect_source_mutation_recorded(receipt: dict[str, Any] | None) -> bool:
    """True when connect_source was applied via governed live mutation (FIX 111 prerequisite)."""
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    if str(receipt.get("phase") or "") != "connect_source":
        return False
    status = str(receipt.get("status") or "")
    if status in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED} and receipt_is_live_mutation(receipt):
        return True
    return bool(receipt.get("mutation_performed")) and status == STATUS_MUTATION_SUCCESS


def forward_live_trigger_deploy_recorded(receipt: dict[str, Any] | None) -> bool:
    """True when trigger_deploy was applied via governed live mutation (FIX 114 prerequisite)."""
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    if str(receipt.get("phase") or "") != "trigger_deploy":
        return False
    status = str(receipt.get("status") or "")
    if status in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED} and receipt_is_live_mutation(receipt):
        return True
    return bool(receipt.get("mutation_performed")) and status == STATUS_MUTATION_SUCCESS


# FIX 114 — readonly runtime verification receipts (never live mutation).
STATUS_VERIFICATION_READONLY_SUCCESS = "verification_readonly_success"
STATUS_VERIFICATION_READONLY_FAILURE = "verification_readonly_failure"
STATUS_VERIFICATION_READONLY_SKIPPED = "verification_readonly_skipped"

VERIFICATION_READONLY_RECEIPT_STATUSES = frozenset(
    {
        STATUS_VERIFICATION_READONLY_SUCCESS,
        STATUS_VERIFICATION_READONLY_FAILURE,
        STATUS_VERIFICATION_READONLY_SKIPPED,
    }
)


def verification_readonly_recorded(receipt: dict[str, Any] | None) -> bool:
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    status = str(receipt.get("status") or "")
    return status in {
        STATUS_VERIFICATION_READONLY_SUCCESS,
        STATUS_VERIFICATION_READONLY_FAILURE,
        STATUS_VERIFICATION_READONLY_SKIPPED,
    }


def forward_live_configure_env_group_recorded(receipt: dict[str, Any] | None) -> bool:
    """True when configure_env group receipt is from governed live mutation."""
    if not receipt:
        return False
    receipt = normalize_receipt_status(dict(receipt))
    if str(receipt.get("phase") or "") != "configure_env":
        return False
    status = str(receipt.get("status") or "")
    if status in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED} and receipt_is_live_mutation(receipt):
        return True
    return bool(receipt.get("mutation_performed")) and status == STATUS_MUTATION_SUCCESS


def receipt_is_rollback_simulated(receipt: dict[str, Any]) -> bool:
    status = str(receipt.get("status") or "")
    return status in ROLLBACK_SIMULATED_RECEIPT_STATUSES or (
        str(receipt.get("phase") or "").startswith("rollback_")
        and not receipt.get("mutation_performed")
    )
