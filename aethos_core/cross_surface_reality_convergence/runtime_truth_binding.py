# SPDX-License-Identifier: Apache-2.0
"""Runtime truth binding — bind provider/runtime truth into cross-surface convergence."""

from __future__ import annotations

from typing import Any


def bind_runtime_truth(*, primary_subject: str | None = None, provider: str = "railway") -> dict[str, Any]:
    """Bind runtime truth layer when operational subject aligns with provider convergence."""
    try:
        from aethos_core.runtime_truth_convergence.runtime_truth_runtime import orchestrate_runtime_truth

        runtime_truth = orchestrate_runtime_truth(provider=provider)
    except Exception:
        return {
            "runtime_truth_bound": False,
            "truth_converged": False,
            "truth_subject": None,
            "summary": "Runtime truth unavailable — cross-surface binding skipped.",
        }

    alignment = runtime_truth.get("alignment") or {}
    truth_subject = alignment.get("primary_subject") or "deployment recovery"
    converged = bool(runtime_truth.get("converged"))

    subject_aligned = True
    if primary_subject and truth_subject:
        from aethos_core.cross_surface_reality_convergence.surface_alignment import _subject_overlap

        subject_aligned = _subject_overlap(str(primary_subject), str(truth_subject)) >= 0.25

    return {
        "runtime_truth_bound": converged or subject_aligned,
        "truth_converged": converged,
        "truth_subject": truth_subject,
        "subject_aligned": subject_aligned,
        "runtime_truth": {
            "converged": converged,
            "summary": runtime_truth.get("summary"),
        },
        "summary": (
            "Runtime truth bound to cross-surface convergence."
            if subject_aligned
            else "Runtime truth present but subject alignment weak — confidence should be reduced."
        ),
    }
