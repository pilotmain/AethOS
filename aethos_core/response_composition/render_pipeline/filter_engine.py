# SPDX-License-Identifier: Apache-2.0
"""Deterministic payload filtering before renderer selection."""

from __future__ import annotations

from typing import Any, Literal

FilterMode = Literal["all", "failed", "unknown"]


def is_failed_row(row: dict[str, Any]) -> bool:
    health = str(row.get("health") or "").lower()
    status = str(row.get("status") or "").lower()
    return health == "failed" or status == "failed" or health in {"crashed", "error"} or status in {
        "failed",
        "crashed",
        "error",
    }


def is_unknown_row(row: dict[str, Any], *, failed_rows: list[dict[str, Any]]) -> bool:
    if row in failed_rows:
        return False
    health = str(row.get("health") or "").lower()
    status = str(row.get("status") or "").lower()
    return health == "unknown" or status in {"unknown", "deploying"}


def canonical_failed_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Canonical failed rows always derive from services first."""
    services = list(payload.get("services") or [])
    derived = [row for row in services if is_failed_row(row)]
    if derived:
        return derived
    return list(payload.get("failures") or [])


def canonical_unknown_rows(payload: dict[str, Any], *, failed_rows: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    failed = failed_rows if failed_rows is not None else canonical_failed_rows(payload)
    services = list(payload.get("services") or [])
    derived = [row for row in services if is_unknown_row(row, failed_rows=failed)]
    if derived:
        return derived
    return list(payload.get("unknown") or [])


def extract_failed_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return canonical_failed_rows(payload)


def extract_unknown_rows(payload: dict[str, Any], *, failed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return canonical_unknown_rows(payload, failed_rows=failed_rows)


def recompute_counts(
    *,
    services: list[dict[str, Any]],
    failed_rows: list[dict[str, Any]],
    unknown_rows: list[dict[str, Any]],
) -> dict[str, int]:
    healthy = sum(1 for row in services if row.get("health") == "healthy")
    return {
        "total": len(services),
        "healthy": healthy,
        "failed": len(failed_rows),
        "unknown": len(unknown_rows),
    }


def apply_filter(payload: dict[str, Any], filter_mode: FilterMode) -> dict[str, Any]:
    """Return a new payload view; never mutates the input."""
    failed_rows = extract_failed_rows(payload)
    unknown_rows = extract_unknown_rows(payload, failed_rows=failed_rows)
    all_services = list(payload.get("services") or [])

    if filter_mode == "failed":
        services = list(failed_rows)
        view_failures = list(failed_rows)
        view_unknown: list[dict[str, Any]] = []
    elif filter_mode == "unknown":
        services = list(unknown_rows)
        view_failures = []
        view_unknown = list(unknown_rows)
    else:
        services = all_services
        view_failures = list(failed_rows)
        view_unknown = list(unknown_rows)

    counts = recompute_counts(services=services, failed_rows=view_failures, unknown_rows=view_unknown)
    original_counts = dict(payload.get("counts") or {})

    return {
        "services": services,
        "counts": counts,
        "failures": view_failures,
        "unknown": view_unknown,
        "filter_mode": filter_mode,
        "original_counts": original_counts,
    }
